"""
This script do a backtest of the trading strategy based on the RSI(2) mean-reversion strategy.
1. Trend Filter: Price > 200-day SMA 
2. Setup: RSI(2) < 5
3. Sell: Price > 5-day SMA
"""

import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta
from datetime import datetime
import math
import time

# ==============================================================================
# --- CONFIGURATION ---
# ==============================================================================
LEVERAGE_FACTOR = 5
INITIAL_CAPITAL = 250.0
MAX_CONCURRENT_POSITIONS = 5
START_DATE = "2018-01-01"
END_DATE = "2018-12-31"
TICKER_FILES = ['data/ibex35.csv', 'data/sp500.csv', 'data/nasdaq100.csv']
PRIORITIZATION_METHOD = ['RSI', 'RSI_DESC'] # Options: 'RSI', 'RSI_DESC', 'A-Z', 'Z-A', 'HV_DESC', 'ADX_DESC', or 'ALL' or a list of methods
ALL_METHODS = ['RSI', 'RSI_DESC', 'A-Z', 'Z-A', 'HV_DESC', 'ADX_DESC']
# ==============================================================================
# ==============================================================================

def prepare_data(tickers):
    print(f"Step 1: Downloading historical data... (Leverage: 1:{LEVERAGE_FACTOR})")
    all_historical_data = {}
    data_start_date = pd.to_datetime(START_DATE) - pd.DateOffset(months=10)
    # Batch download to be friendlier to the API
    for i in range(0, len(tickers), 100):
        batch = tickers[i:i+100]
        try:
            data_batch = yf.download(batch, start=data_start_date, end=END_DATE, progress=False, group_by='ticker')
            if data_batch is not None and not data_batch.empty:
                for ticker in batch:
                    try:
                        df = data_batch[ticker]
                        if not df.empty and len(df) > 200:
                            all_historical_data[ticker] = df.dropna(subset=['Open', 'High', 'Low', 'Close'])
                    except KeyError:
                        pass # Ticker might not be in the downloaded batch
        except Exception as e: print(f"Could not download data for batch starting with {batch[0]}: {e}")
        time.sleep(1)
    print(f"Successfully downloaded data for {len(all_historical_data)} tickers.")

    print("Step 2: Unifying and forward-filling data...")
    master_index = pd.DatetimeIndex([])
    for df in all_historical_data.values(): master_index = master_index.union(df.index)
    for ticker in all_historical_data: all_historical_data[ticker] = all_historical_data[ticker].reindex(master_index, method='ffill')

    print("Step 3: Pre-calculating signals...")
    tickers_to_remove = []
    for ticker, df in all_historical_data.items():
        try:
            # Ensure correct data types before calculations
            for col in ['open', 'high', 'low', 'close']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            df.columns = [str(col).lower() for col in df.columns]
            df["sma_200"] = ta.sma(df["close"], length=200)
            df["sma_5"] = ta.sma(df["close"], length=5)
            df["rsi_2"] = ta.rsi(df["close"], length=2)
            df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
            df['hv_100'] = df['log_returns'].rolling(window=100).std() * np.sqrt(252)
            # Ensure high, low, close are available for ADX
            if all(c in df.columns for c in ['high', 'low', 'close']):
                adx_df = ta.adx(df["high"], df["low"], df["close"], length=14)
                if adx_df is not None and not adx_df.empty:
                    df['adx_14'] = adx_df.iloc[:, 0]
                else:
                    df['adx_14'] = np.nan
            else:
                df['adx_14'] = np.nan
            df["is_buy_signal"] = (df["close"] > df["sma_200"]) & (df["rsi_2"] < 5) & (df["close"] < df["sma_5"])
            df["is_exit_signal"] = df["close"] > df["sma_5"]
        except Exception as e:
            print(f"Warning: Could not calculate indicators for {ticker}. It will be removed. Error: {e}")
            tickers_to_remove.append(ticker)
    
    for ticker in tickers_to_remove:
        del all_historical_data[ticker]
    return all_historical_data, master_index

def run_simulation(all_historical_data, master_index, prioritization_method, verbose=True):
    cash = INITIAL_CAPITAL
    portfolio_value_history, positions, completed_trades = [], {}, []
    
    for date in master_index:
        if date < pd.to_datetime(START_DATE): continue

        # Calculate portfolio value at the start of the day to check for bankruptcy
        equity_in_positions = 0
        for ticker, pos_data in positions.items():
            current_price = all_historical_data[ticker].loc[date]['close']
            unrealized_pnl = (current_price * pos_data["quantity"]) - pos_data["notional_value"]
            equity_in_positions += pos_data["investment_cost"] + unrealized_pnl
        total_portfolio_value = cash + equity_in_positions

        # Halt simulation if bankrupt
        if total_portfolio_value <= 0:
            print(f"\\n{date.date()}: --- MARGIN CALL! --- Portfolio value is zero or negative. Liquidating all open positions.")
            for ticker in list(positions.keys()):
                pos_info = positions[ticker]
                signal_data = all_historical_data[ticker].loc[date]
                pnl = (signal_data["close"] * pos_info["quantity"]) - pos_info["notional_value"]
                cash += pos_info["investment_cost"] + pnl
                duration = np.busday_count(pos_info["buy_date"].date(), date.date())
                completed_trades.append({"ticker": ticker, "duration": duration, "pnl": pnl, "investment_cost": pos_info["investment_cost"]})
                print(f"{date.date()}: LIQUIDATION of {'{:.2f}'.format(pos_info['quantity'])} {ticker} at {signal_data['close']:.2f} | P&L: ${pnl:,.2f}")
                del positions[ticker]
            
            # Record final value after liquidation and halt
            portfolio_value_history.append({"date": date, "value": cash}) # Final value is remaining cash
            break

        for ticker in list(positions.keys()):
            signal_data = all_historical_data[ticker].loc[date]
            if signal_data["is_exit_signal"]:
                pos_info = positions[ticker]
                pnl = (signal_data["close"] * pos_info["quantity"]) - pos_info["notional_value"]
                cash += pos_info["investment_cost"] + pnl
                duration = np.busday_count(pos_info["buy_date"].date(), date.date())
                completed_trades.append({"ticker": ticker, "duration": duration, "pnl": pnl, "investment_cost": pos_info["investment_cost"]})
                print(f"{date.date()}: SELL {'{:.2f}'.format(pos_info['quantity'])} of {ticker} at {signal_data['close']:.2f} | P&L: ${pnl:,.2f}")
                del positions[ticker]

        open_slots = MAX_CONCURRENT_POSITIONS - len(positions)
        if open_slots > 0:
            potential_buys = []
            for ticker in all_historical_data.keys():
                if ticker not in positions:
                    signal_data = all_historical_data[ticker].loc[date]
                    if signal_data["is_buy_signal"] and not pd.isna(signal_data["close"]):
                        potential_buys.append({
                            "ticker": ticker,
                            "rsi": signal_data["rsi_2"],
                            "price": signal_data["close"],
                            "hv": signal_data["hv_100"],
                            "adx": signal_data["adx_14"]
                        })
            
            # Sort potential buys based on the configured method
            if prioritization_method == 'RSI':
                sorted_buys = sorted(potential_buys, key=lambda x: x['rsi'])
            elif prioritization_method == 'RSI_DESC':
                sorted_buys = sorted(potential_buys, key=lambda x: x['rsi'], reverse=True)
            elif prioritization_method == 'A-Z':
                sorted_buys = sorted(potential_buys, key=lambda x: x['ticker'])
            elif prioritization_method == 'Z-A':
                sorted_buys = sorted(potential_buys, key=lambda x: x['ticker'], reverse=True)
            elif prioritization_method == 'HV_DESC':
                sorted_buys = sorted(potential_buys, key=lambda x: x['hv'] if not pd.isna(x['hv']) else 0, reverse=True)
            elif prioritization_method == 'ADX_DESC':
                sorted_buys = sorted(potential_buys, key=lambda x: x['adx'] if not pd.isna(x['adx']) else 0, reverse=True)
            else: # Default to RSI ASC if method is unknown
                sorted_buys = sorted(potential_buys, key=lambda x: x['rsi'])

            for buy in sorted_buys:
                if len(positions) >= MAX_CONCURRENT_POSITIONS: break
                
                # Recalculate open slots and cash per slot for each new trade
                open_slots = MAX_CONCURRENT_POSITIONS - len(positions)
                if open_slots <= 0: continue
                cash_per_slot = cash / open_slots

                ticker = buy["ticker"]
                price = buy["price"]

                target_notional = cash_per_slot * LEVERAGE_FACTOR
                quantity = math.floor(target_notional / price) if LEVERAGE_FACTOR > 1 else target_notional / price
                if quantity == 0: continue

                actual_notional_value = quantity * price
                actual_investment_cost = actual_notional_value / LEVERAGE_FACTOR
                if actual_investment_cost < 5.0: continue # Minimum trade size

                if cash >= actual_investment_cost:
                    cash -= actual_investment_cost
                    positions[ticker] = {"quantity": quantity, "buy_date": date, "investment_cost": actual_investment_cost, "notional_value": actual_notional_value}
                    if verbose:
                        print(f"{date.date()}: BUY {'{:.2f}'.format(quantity)} of {ticker} at {price:.2f} | Cost: ${actual_investment_cost:,.2f} (Notional: ${actual_notional_value:,.2f}, RSI: {buy['rsi']:.2f}, HV: {buy.get('hv', 0):.2f}, ADX: {buy.get('adx', 0):.2f})")
        
        portfolio_value_history.append({"date": date, "value": total_portfolio_value})

    portfolio_df = pd.DataFrame(portfolio_value_history).set_index("date")
    calendar_range = pd.date_range(start=START_DATE, end=END_DATE)
    portfolio_df = portfolio_df.reindex(calendar_range, method='ffill')
    return {"portfolio_df": portfolio_df, "completed_trades": completed_trades, "open_positions": positions}

def calculate_summary_performance(portfolio_df, completed_trades):
    if portfolio_df.empty or portfolio_df['value'].isna().all():
        return None
    first_valid_index = portfolio_df['value'].first_valid_index()
    initial_value = portfolio_df.loc[first_valid_index]['value']
    final_value = portfolio_df['value'].iloc[-1]
    total_return_percent = ((final_value - initial_value) / initial_value) * 100 if initial_value != 0 else 0
    max_value = portfolio_df['value'].max()
    num_days = (portfolio_df.index[-1] - portfolio_df.index[0]).days
    num_years = num_days / 365.25
    annualized_return_percent = 0
    if (1 + total_return_percent / 100) > 0 and num_years > 0:
        annualized_return_percent = ((1 + total_return_percent / 100) ** (1 / num_years) - 1) * 100
    winning_trades = sum(1 for t in completed_trades if t['pnl'] > 0)
    total_trades = len(completed_trades)
    win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
    avg_duration = sum(t['duration'] for t in completed_trades) / total_trades if total_trades > 0 else 0
    return {
        "Final Value": f"${final_value:,.2f}",
        "Max Value": f"${max_value:,.2f}",
        "Total Return": f"{total_return_percent:.2f}%",
        "Annualized Return": f"{annualized_return_percent:.2f}%",
        "Total Trades": total_trades,
        "Avg Duration (d)": f"{avg_duration:.2f}",
        "Winrate": f"{win_rate:.2f}%"
    }

def print_single_run_details(results):
    portfolio_df = results["portfolio_df"]
    completed_trades = results["completed_trades"]
    
    if portfolio_df.empty or portfolio_df['value'].isna().all():
        print("Could not generate portfolio history. No trades were made or data was unavailable.")
        return

    print("\n--- Backtest Finished: Performance Summary ---")
    summary = calculate_summary_performance(portfolio_df, completed_trades)
    initial_value = portfolio_df['value'].iloc[0]
    max_portfolio_value = portfolio_df['value'].max()
    print(f"Initial Portfolio Value: ${initial_value:,.2f}")
    print(f"Max Portfolio Value:     ${max_portfolio_value:,.2f}")
    print(f"Final Portfolio Value:   {summary['Final Value']}")
    print(f"Total Return:            {summary['Total Return']}")
    print(f"Annualized Return:       {summary['Annualized Return']}")

    if completed_trades:
        for trade in completed_trades:
            trade['percent_return'] = (trade['pnl'] / trade['investment_cost']) * 100 if trade['investment_cost'] > 0 else 0
        
        best_trade_pct = max(completed_trades, key=lambda x: x['percent_return'])
        worst_trade_pct = min(completed_trades, key=lambda x: x['percent_return'])
        best_trade_usd = max(completed_trades, key=lambda x: x['pnl'])
        worst_trade_usd = min(completed_trades, key=lambda x: x['pnl'])
        longest_trade = max(completed_trades, key=lambda x: x['duration'])

        print("\n--- Trade Statistics ---")
        print(f"Total Completed Trades:  {len(completed_trades)}")
        print(f"Average Trade Duration:  {sum(t['duration'] for t in completed_trades) / len(completed_trades):.2f} days")
        print(f"Longest Trade:           {longest_trade['duration']} days ({longest_trade['ticker']})")
        
        print("\n--- Best & Worst Trades ---")
        print(f"Best Trade ($):          ${best_trade_usd['pnl']:,.2f} ({best_trade_usd['ticker']})")
        print(f"Worst Trade ($):         ${worst_trade_usd['pnl']:,.2f} ({worst_trade_usd['ticker']})")
        print(f"Best Trade (%):          {best_trade_pct['percent_return']:.2f}% ({best_trade_pct['ticker']})")
        print(f"Worst Trade (%):         {worst_trade_pct['percent_return']:.2f}% ({worst_trade_pct['ticker']})")

    open_positions = results["open_positions"]
    print("\n--- Open Positions at End of Backtest ---")
    if open_positions:
        end_date_dt = pd.to_datetime(END_DATE)
        for ticker, pos in open_positions.items():
            duration = (end_date_dt - pos['buy_date']).days
            print(f"- {ticker}: Held for {duration} days (Quantity: {'{:.2f}'.format(pos['quantity'])})")
    else: print("No positions were open at the end of the backtest.")

if __name__ == '__main__':
    start_time = time.perf_counter()
    all_tickers = []
    for fp in TICKER_FILES:
        try:
            with open(fp, 'r') as f: all_tickers.extend([line.strip() for line in f.readlines() if line.strip()])
        except FileNotFoundError: print(f"Warning: Could not find ticker file: {fp}")
    unique_tickers = sorted(list(set(all_tickers)))
    print(f"Loaded {len(unique_tickers)} unique tickers.")
    
    all_historical_data, master_index = prepare_data(unique_tickers)
    
    if isinstance(PRIORITIZATION_METHOD, list) or PRIORITIZATION_METHOD == 'ALL':
        methods_to_run = PRIORITIZATION_METHOD if isinstance(PRIORITIZATION_METHOD, list) else ALL_METHODS
        all_results = []
        for method in methods_to_run:
            print(f"\n--- Running Simulation for Prioritization Method: {method} ---")
            results = run_simulation(all_historical_data, master_index, method, verbose=False)
            performance = calculate_summary_performance(results["portfolio_df"], results["completed_trades"])
            if performance:
                performance["Method"] = method
                all_results.append(performance)
            
        print("\n\n--- Overall Performance Summary ---")
        if all_results:
            summary_df = pd.DataFrame(all_results).set_index("Method")
            summary_df['Total Return (sort)'] = summary_df['Total Return'].str.replace('%', '').astype(float)
            summary_df = summary_df.sort_values(by='Total Return (sort)', ascending=False).drop(columns=['Total Return (sort)'])
            print(summary_df)
            print("\nNote: Avg Duration omits Saturdays and Sundays because the markets are closed.")
        else:
            print("No results to display.")
    
    else:
        print(f"\n--- Running Simulation for Prioritization Method: {PRIORITIZATION_METHOD} ---")
        results = run_simulation(all_historical_data, master_index, PRIORITIZATION_METHOD, verbose=True)
        print_single_run_details(results)

    elapsed_seconds = time.perf_counter() - start_time
    minutes, seconds = divmod(elapsed_seconds, 60)
    print(f"\nTotal execution time: {int(minutes)} minutes {seconds:.1f} seconds")
