"""
This script do a backtest of the trading strategy based on the RSI(2) mean-reversion strategy.
1. Trend Filter: Price > 200-day SMA && S&P 500 > (200-day SMA * SP500_ENTRY_THRESHOLD) && VIX < VIX_PROTECTION
2. Setup: RSI(2) < 5
3. Sell: Price > 5-day SMA OR TIME_STOP
"""

import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta
from datetime import datetime
import math
import time
import os
import re
import requests
from io import StringIO
from bs4 import BeautifulSoup

# ==============================================================================
# --- CONFIGURATION ---
# ==============================================================================
LEVERAGE_FACTOR = 5
INITIAL_CAPITAL = 350.0
MAX_CONCURRENT_POSITIONS = 8
START_DATE = "2020-01-01" # YYYY-MM-DD
END_DATE = "2025-12-31"
TICKER_FILES = ['data/ibex35.csv', 'data/sp500.csv', 'data/nasdaq100.csv']
# ==============================================================================
PRIORITIZATION_METHOD = 'RSI' # Options: 'RSI', 'RSI_DESC', 'A-Z', 'Z-A', 'HV_DESC', 'ADX_DESC', or 'ALL' or a list of methods
ALL_METHODS = ['RSI', 'RSI_DESC', 'A-Z', 'Z-A', 'HV_DESC', 'ADX_DESC']
STRATEGY_TYPE = "NORMAL" # Options: "NORMAL", "INVERSE", "BOTH"
# ==============================================================================
VIX_PROTECTION = 45 # VIX threshold to shut off system (0 = disabled). System reactivates when VIX < threshold * 0.8
PANIC_BUTTON = False # If True, sell all open positions when VIX protection is triggered
TIME_STOP = 10 # Maximum number of days to hold a position (0 = disabled)
SP500_ENTRY_THRESHOLD = 1.02 # S&P 500 must be above SMA(200) * this value to open positions (e.g., 1.01 = 1% above SMA)
# ==============================================================================
# ==============================================================================

def prepare_data(tickers):
    print(f"Step 1: Downloading historical data... (Leverage: 1:{LEVERAGE_FACTOR})")
    all_historical_data = {}
    data_start_date = pd.to_datetime(START_DATE) - pd.DateOffset(months=10)

    # Download S&P 500 data for market trend filter
    sp500_data = yf.download('^GSPC', start=data_start_date, end=END_DATE, progress=False)
    if sp500_data.empty:
        print("Warning: Could not download S&P 500 data. Market trend filter will be disabled.")
        sp500_data = None
    else:
        if isinstance(sp500_data.columns, pd.MultiIndex):
            sp500_data.columns = sp500_data.columns.droplevel(1)
        sp500_data.columns = [str(col).lower() for col in sp500_data.columns]
        sp500_data['sma_200'] = ta.sma(sp500_data['close'], length=200)

    # Download VIX data
    vix_data = yf.download('^VIX', start=data_start_date, end=END_DATE, progress=False)
    if vix_data.empty:
        print("Warning: Could not download VIX data. VIX protection will be disabled.")
        vix_data = None
    else:
        vix_data = vix_data[['Close']].rename(columns={'Close': 'vix_close'})

    # Download Fed Funds Rate data for swap calculation
    # Download Fed Funds Rate data by scraping
    try:
        url = "https://datosmacro.expansion.com/tipo-interes/usa"
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'table-striped'})

        dates = []
        rates = []
        for row in table.find_all('tr')[1:]: # Skip header row
            cols = row.find_all('td')
            # The date is in the first column, rate in the second
            date_str = cols[0].text.strip()
            rate_str = cols[1].text.strip().replace('%', '').replace(',', '.')
            
            # Convert date from DD/MM/YYYY to YYYY-MM-DD
            day, month, year = date_str.split('/')
            formatted_date = f"{year}-{month}-{day}"
            
            dates.append(formatted_date)
            rates.append(float(rate_str))

        fed_funds_data = pd.DataFrame({'fed_rate': rates}, index=pd.to_datetime(dates))
        # The scraped data is not daily, so we need to reindex and ffill
        # We also need to sort the index as the table is descending
        fed_funds_data = fed_funds_data.sort_index()
        all_dates = pd.date_range(start=fed_funds_data.index.min(), end=END_DATE, freq='D')
        fed_funds_data = fed_funds_data.reindex(all_dates, method='ffill')


    except requests.exceptions.RequestException as e:
        print(f"Warning: Could not download Fed Funds Rate data. Error: {e}. Swap calculation will be disabled.")
        fed_funds_data = None
    except Exception as e:
        print(f"Warning: Could not process Fed Funds Rate data. Error: {e}. Swap calculation will be disabled.")
        fed_funds_data = None

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
    if vix_data is not None:
        vix_data = vix_data.reindex(master_index, method='ffill')
    if sp500_data is not None:
        sp500_data = sp500_data.reindex(master_index, method='ffill')
    if fed_funds_data is not None:
        fed_funds_data = fed_funds_data.reindex(master_index, method='ffill')
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
            # Normal Strategy Signals
            df["is_buy_signal_normal"] = (df["close"] > df["sma_200"]) & (df["rsi_2"] < 5) & (df["close"] < df["sma_5"])
            df["is_exit_signal_normal"] = df["close"] > df["sma_5"]
            
            # Inverse Strategy Signals
            df["is_buy_signal_inverse"] = (df["close"] < df["sma_200"]) & (df["rsi_2"] > 95) & (df["close"] > df["sma_5"])
            df["is_exit_signal_inverse"] = df["close"] < df["sma_5"]
        except Exception as e:
            print(f"Warning: Could not calculate indicators for {ticker}. It will be removed. Error: {e}")
            tickers_to_remove.append(ticker)
    
    for ticker in tickers_to_remove:
        del all_historical_data[ticker]
    
    if vix_data is not None:
        return all_historical_data, master_index, vix_data, sp500_data, fed_funds_data
    return all_historical_data, master_index, None, None, None

def run_simulation(all_historical_data, master_index, prioritization_method, strategy_type, vix_data, sp500_data, fed_funds_data, verbose=True):
    cash = INITIAL_CAPITAL
    portfolio_value_history, positions, completed_trades = [], {}, []
    system_shut_off = False
    previous_system_state = False  # Track previous state to detect changes
    
    for date in master_index:
        if date < pd.to_datetime(START_DATE): continue

        # --- SWAP CALCULATION for leveraged positions ---
        if LEVERAGE_FACTOR > 1 and fed_funds_data is not None:
            if date in fed_funds_data.index:
                current_fed_rate = fed_funds_data.loc[date, 'fed_rate']
                if pd.notna(current_fed_rate):
                    # Broker's spread is 2.5%
                    swap_rate_annual = (current_fed_rate / 100) + 0.025
                    for ticker, pos_data in positions.items():
                        daily_swap = (pos_data["notional_value"] * swap_rate_annual) / 360
                        pos_data["accumulated_swap"] += daily_swap

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
                pnl = (pos_info["notional_value"] - (signal_data["close"] * pos_info["quantity"])) if strategy_type == "INVERSE" else ((signal_data["close"] * pos_info["quantity"]) - pos_info["notional_value"])
                pnl -= pos_info["accumulated_swap"]
                cash += pos_info["investment_cost"] + pnl
                duration = np.busday_count(pos_info["buy_date"].date(), date.date())  # Business days
                completed_trades.append({"ticker": ticker, "duration": duration, "pnl": pnl, "investment_cost": pos_info["investment_cost"]})
                print(f"{date.date()}: LIQUIDATION of {'{:.2f}'.format(pos_info['quantity'])} {ticker} at {signal_data['close']:.2f} | P&L: ${pnl:,.2f} (Swap: ${pos_info['accumulated_swap']:,.2f})")
                del positions[ticker]
            
            # Record final value after liquidation and halt
            portfolio_value_history.append({"date": date, "value": cash}) # Final value is remaining cash
            break

        # Close positions (including TIME_STOP check) - this ALWAYS runs regardless of system_shut_off
        for ticker in list(positions.keys()):
            signal_data = all_historical_data[ticker].loc[date]
            exit_signal = f"is_exit_signal_{strategy_type.lower()}"
            pos_info = positions[ticker]
            
            # Check for TIME_STOP condition (business days only, excluding weekends)
            time_stop_triggered = False
            if TIME_STOP > 0:
                days_held = np.busday_count(pos_info["buy_date"].date(), date.date())
                if days_held >= TIME_STOP:
                    time_stop_triggered = True
            
            if signal_data[exit_signal] or time_stop_triggered:
                pnl = (pos_info["notional_value"] - (signal_data["close"] * pos_info["quantity"])) if strategy_type == "INVERSE" else ((signal_data["close"] * pos_info["quantity"]) - pos_info["notional_value"])
                pnl -= pos_info["accumulated_swap"]
                cash += pos_info["investment_cost"] + pnl
                duration = np.busday_count(pos_info["buy_date"].date(), date.date())  # Use business days
                completed_trades.append({"ticker": ticker, "duration": duration, "pnl": pnl, "investment_cost": pos_info["investment_cost"]})
                exit_reason = "TIME_STOP" if time_stop_triggered else "Price > SMA(5)"
                if verbose:
                    percent_pnl = (pnl / pos_info['investment_cost']) * 100 if pos_info['investment_cost'] > 0 else 0
                    print(f"{date.date()}: SELL {'{:.2f}'.format(pos_info['quantity'])} of {ticker} at {signal_data['close']:.2f} | P&L: ${pnl:,.2f} (Swap: ${pos_info['accumulated_swap']:,.2f}) | %PL: {percent_pnl:.2f}% ({exit_reason}) [Days: {duration}]")
                del positions[ticker]

        # VIX Protection and System State Logic - this affects NEW ENTRIES only
        # Always evaluate system state based on VIX (if enabled) and S&P 500 trend
        vix_value = None
        vix_reactivation_threshold = None
        
        if VIX_PROTECTION > 0 and vix_data is not None and date in vix_data.index:
            vix_value = vix_data.loc[date, 'vix_close']
            if isinstance(vix_value, pd.Series):
                vix_value = vix_value.iloc[0]
            vix_reactivation_threshold = VIX_PROTECTION * 0.8
        
        # Get S&P 500 data for trend analysis (always needed for system state)
        sp500_price = sp500_data.loc[date, 'close'] if sp500_data is not None else None
        sp500_sma200 = sp500_data.loc[date, 'sma_200'] if sp500_data is not None else None
        if isinstance(sp500_price, pd.Series):
            sp500_price = sp500_price.iloc[0]
        if isinstance(sp500_sma200, pd.Series):
            sp500_sma200 = sp500_sma200.iloc[0]
        
        # Shutdown condition: Price < SMA200
        is_sp500_bearish = pd.notna(sp500_price) and pd.notna(sp500_sma200) and sp500_price < sp500_sma200
        
        # Reactivation condition: Price > SMA200 * SP500_ENTRY_THRESHOLD
        is_sp500_strong = pd.notna(sp500_price) and pd.notna(sp500_sma200) and sp500_price > (sp500_sma200 * SP500_ENTRY_THRESHOLD)
        
        # State change logic
        if not system_shut_off:
            # Check if system should shut off
            if vix_value is not None and vix_value > VIX_PROTECTION:
                system_shut_off = True
                print(f"\033[93m{date.date()}: System shut off because VIX > {VIX_PROTECTION} (VIX: {vix_value:.2f})\033[0m")
                if PANIC_BUTTON and positions:
                    print(f"\033[91m{date.date()}: PANIC BUTTON ACTIVATED. Liquidating all open positions.\033[0m")
                    for ticker in list(positions.keys()):
                        pos_info = positions[ticker]
                        signal_data = all_historical_data[ticker].loc[date]
                        pnl = (pos_info["notional_value"] - (signal_data["close"] * pos_info["quantity"])) if strategy_type == "INVERSE" else ((signal_data["close"] * pos_info["quantity"]) - pos_info["notional_value"])
                        pnl -= pos_info["accumulated_swap"]
                        cash += pos_info["investment_cost"] + pnl
                        duration = np.busday_count(pos_info["buy_date"].date(), date.date())  # Business days
                        completed_trades.append({"ticker": ticker, "duration": duration, "pnl": pnl, "investment_cost": pos_info["investment_cost"]})
                        print(f"\033[91m{date.date()}: VIX LIQUIDATION of {'{:.2f}'.format(pos_info['quantity'])} {ticker} at {signal_data['close']:.2f} | P&L: ${pnl:,.2f} (Swap: ${pos_info['accumulated_swap']:,.2f})\033[0m")
                        del positions[ticker]
            elif is_sp500_bearish:
                system_shut_off = True
                sp500_price_str = f"{sp500_price:.2f}" if pd.notna(sp500_price) else "N/A"
                sp500_sma200_str = f"{sp500_sma200:.2f}" if pd.notna(sp500_sma200) else "N/A"
                print(f"\033[93m{date.date()}: System shut off because S&P500 downtrend (Price: {sp500_price_str} < SMA200: {sp500_sma200_str})\033[0m")
        else: 
            # System is shut off - check if it should turn back on
            vix_condition_ok = vix_value is None or vix_value < vix_reactivation_threshold
            sp500_condition_ok = is_sp500_strong
            
            if vix_condition_ok and sp500_condition_ok:
                system_shut_off = False
                sp500_price_str = f"{sp500_price:.2f}" if pd.notna(sp500_price) else "N/A"
                sp500_sma200_str = f"{sp500_sma200:.2f}" if pd.notna(sp500_sma200) else "N/A"
                sp500_threshold_str = f"{sp500_sma200 * SP500_ENTRY_THRESHOLD:.2f}" if pd.notna(sp500_sma200) else "N/A"
                if vix_value is not None:
                    print(f"\033[92m{date.date()}: System shut on | VIX: {vix_value:.2f} < {vix_reactivation_threshold:.2f} | S&P500: {sp500_price_str} > SMA200: {sp500_sma200_str} (threshold: {sp500_threshold_str})\033[0m")
                else:
                    print(f"\033[92m{date.date()}: System shut on | S&P500: {sp500_price_str} > SMA200: {sp500_sma200_str} (threshold: {sp500_threshold_str})\033[0m")
        
        previous_system_state = system_shut_off
        
        # Skip opening new positions if system is shut off
        if system_shut_off:
            portfolio_value_history.append({"date": date, "value": total_portfolio_value})
            continue

        open_slots = MAX_CONCURRENT_POSITIONS - len(positions)
        if open_slots > 0:
            # S&P 500 Market Trend Filter - use the is_sp500_strong variable calculated earlier
            if not is_sp500_strong:
                portfolio_value_history.append({"date": date, "value": total_portfolio_value})
                continue
            
            potential_buys = []
            for ticker in all_historical_data.keys():
                if ticker not in positions:
                    signal_data = all_historical_data[ticker].loc[date]
                    buy_signal = f"is_buy_signal_{strategy_type.lower()}"
                    if signal_data[buy_signal] and not pd.isna(signal_data["close"]):
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
                    positions[ticker] = {
                        "quantity": quantity,
                        "buy_date": date,
                        "investment_cost": actual_investment_cost,
                        "notional_value": actual_notional_value,
                        "accumulated_swap": 0
                    }
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
    
    # Calculate average percent return
    total_percent_return = 0
    if total_trades > 0:
        for t in completed_trades:
            if t['investment_cost'] > 0:
                total_percent_return += (t['pnl'] / t['investment_cost']) * 100
        avg_percent_return = total_percent_return / total_trades
    else:
        avg_percent_return = 0
        
    return {
        "Final Value": f"${final_value:,.2f}",
        "Max Value": f"${max_value:,.2f}",
        "Total Return": f"{total_return_percent:.2f}%",
        "Annualized Return": f"{annualized_return_percent:.2f}%",
        "Total Trades": total_trades,
        "Avg Duration (d)": f"{avg_duration:.2f}",
        "Winrate": f"{win_rate:.2f}%",
        "Avg Profit per Trade": f"{avg_percent_return:.2f}%"
    }

def print_single_run_details(results):
    portfolio_df = results["portfolio_df"]
    completed_trades = results["completed_trades"]
    
    if portfolio_df.empty or portfolio_df['value'].isna().all():
        print("Could not generate portfolio history. No trades were made or data was unavailable.")
        return

    print("\n--- Backtest Finished: Performance Summary ---")
    summary = calculate_summary_performance(portfolio_df, completed_trades)
    first_valid_index = portfolio_df['value'].first_valid_index()
    initial_value = portfolio_df.loc[first_valid_index]['value'] if first_valid_index is not None else float('nan')
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

    print("\n--- Periodic Returns ---")
    periodic_returns = calculate_periodic_returns(portfolio_df)
    for year, data in periodic_returns.items():
        print(f"\n{year}:")
        print(f"  Initial Capital: ${data['initial_capital']:,.2f}")
        print(f"  Yearly P&L: ${data['yearly_pnl']:,.2f} ({data['yearly_return']:.2f}%)")
        for month, month_data in data['months'].items():
            print(f"    {month}: ${month_data['pnl']:,.2f} ({month_data['return']:.2f}%)")

def calculate_periodic_returns(portfolio_df):
    """Calculates yearly and monthly returns from the portfolio value history."""
    if portfolio_df.empty:
        return {}

    # Resample to get the last value of each month and year
    monthly_values = portfolio_df['value'].resample('ME').last()
    yearly_values = portfolio_df['value'].resample('YE').last()

    # Get initial capital for each year
    yearly_initial_capital = portfolio_df['value'].resample('YE').first()

    periodic_data = {}
    for year_end_date in yearly_values.index:
        year = year_end_date.year
        initial_capital = yearly_initial_capital.get(year_end_date, 0)
        final_value = yearly_values.get(year_end_date, 0)
        
        yearly_pnl = final_value - initial_capital
        yearly_return_pct = (yearly_pnl / initial_capital) * 100 if initial_capital > 0 else 0

        periodic_data[year] = {
            'initial_capital': initial_capital,
            'yearly_pnl': yearly_pnl,
            'yearly_return': yearly_return_pct,
            'months': {}
        }

        # Monthly Returns
        monthly_df = portfolio_df[portfolio_df.index.year == year]
        monthly_starts = monthly_df['value'].resample('MS').first()
        monthly_ends = monthly_df['value'].resample('ME').last()
        
        for month_start_date in monthly_starts.index:
            month_end_date = month_start_date + pd.offsets.MonthEnd(0)
            start_val = monthly_starts[month_start_date]
            end_val = monthly_ends.get(month_end_date, start_val)
            
            month_pnl = end_val - start_val
            month_return_pct = (month_pnl / start_val) * 100 if start_val > 0 else 0
            
            periodic_data[year]['months'][month_end_date.strftime('%B')] = {
                'pnl': month_pnl,
                'return': month_return_pct
            }
            
    return periodic_data

def write_report(results, config, logs):
    """Writes the backtest report to a markdown file."""
    # Ensure the target directory exists
    output_dir = "docs/backtests"
    os.makedirs(output_dir, exist_ok=True)
    
    filename_base = f"{config['START_DATE']}-{config['END_DATE']}"
    
    # Check for existing files and increment suffix
    i = 1
    filename = os.path.join(output_dir, f"{filename_base}.md")
    while os.path.exists(filename):
        filename = os.path.join(output_dir, f"{filename_base}-{i}.md")
        i += 1

    with open(filename, 'w') as f:
        f.write("# Backtest Report\n")
        f.write("## Configuration\n")
        for key, value in config.items():
            f.write(f"- **{key}:** {value}\n")
        
        f.write("\n## Performance Summary\n")
        summary = calculate_summary_performance(results["portfolio_df"], results["completed_trades"])
        if summary:
            for key, value in summary.items():
                f.write(f"- **{key}:** {value}\n")

        f.write("\n## Periodic Returns\n")
        periodic_returns = calculate_periodic_returns(results["portfolio_df"])
        for year, data in periodic_returns.items():
            f.write(f"### {year}\n")
            f.write(f"- **Initial Capital:** ${data['initial_capital']:,.2f}\n")
            f.write(f"- **Yearly P&L:** ${data['yearly_pnl']:,.2f} ({data['yearly_return']:.2f}%)\n")
            for month, month_data in data['months'].items():
                f.write(f"  - **{month}:** ${month_data['pnl']:,.2f} ({month_data['return']:.2f}%)\n")
        
        f.write("\n## Trade Log\n")
        # Function to remove ANSI escape codes
        def remove_ansi_codes(text):
            ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
            return ansi_escape.sub('', text)

        for log_entry in logs:
            f.write(f"{remove_ansi_codes(log_entry)}\n")

if __name__ == '__main__':
    # Capture logs
    import sys
    from io import StringIO
    
    original_stdout = sys.stdout
    log_stream = StringIO()

    class Tee(object):
        def __init__(self, *files):
            self.files = files
        def write(self, obj):
            for f in self.files:
                f.write(obj)
        def flush(self):
            for f in self.files:
                f.flush()

    sys.stdout = Tee(sys.stdout, log_stream)


    start_time = time.perf_counter()
    all_tickers = []
    for fp in TICKER_FILES:
        try:
            with open(fp, 'r') as f: all_tickers.extend([line.strip() for line in f.readlines() if line.strip()])
        except FileNotFoundError: print(f"Warning: Could not find ticker file: {fp}")
    unique_tickers = sorted(list(set(all_tickers)))
    print(f"Loaded {len(unique_tickers)} unique tickers.")
    
    all_historical_data, master_index, vix_data, sp500_data, fed_funds_data = prepare_data(unique_tickers)
    
    if isinstance(PRIORITIZATION_METHOD, list) or PRIORITIZATION_METHOD == 'ALL':
        methods_to_run = PRIORITIZATION_METHOD if isinstance(PRIORITIZATION_METHOD, list) else ALL_METHODS
        
        if STRATEGY_TYPE == 'BOTH':
            strategies = ['NORMAL', 'INVERSE']
        else:
            strategies = [STRATEGY_TYPE]

        for strategy in strategies:
            print(f"\n--- Running Simulations for {strategy} Strategy ---")
            all_results = []
            for method in methods_to_run:
                print(f"--- Prioritization Method: {method} ---")
                results = run_simulation(all_historical_data, master_index, method, strategy, vix_data, sp500_data, fed_funds_data, verbose=False)
                performance = calculate_summary_performance(results["portfolio_df"], results["completed_trades"])
                if performance:
                    performance["Method"] = method
                    all_results.append(performance)
            
            print(f"\n\n--- Overall Performance Summary for {strategy} Strategy ---")
            if all_results:
                summary_df = pd.DataFrame(all_results).set_index("Method")
                summary_df['Total Return (sort)'] = summary_df['Total Return'].str.replace('%', '').astype(float)
                summary_df = summary_df.sort_values(by='Total Return (sort)', ascending=False).drop(columns=['Total Return (sort)'])
                print(summary_df)
                print("\nNote: Avg Duration omits Saturdays and Sundays because the markets are closed.")
            else:
                print("No results to display.")
    
    else:
        if STRATEGY_TYPE == "BOTH":
            all_results = []
            print(f"\n--- Running Simulation for Strategy: NORMAL ---")
            results_normal = run_simulation(all_historical_data, master_index, PRIORITIZATION_METHOD, "NORMAL", vix_data, sp500_data, fed_funds_data, verbose=False)
            performance_normal = calculate_summary_performance(results_normal["portfolio_df"], results_normal["completed_trades"])
            if performance_normal:
                performance_normal["Strategy"] = "NORMAL"
                all_results.append(performance_normal)

            print(f"\n--- Running Simulation for Strategy: INVERSE ---")
            results_inverse = run_simulation(all_historical_data, master_index, PRIORITIZATION_METHOD, "INVERSE", vix_data, sp500_data, fed_funds_data, verbose=False)
            performance_inverse = calculate_summary_performance(results_inverse["portfolio_df"], results_inverse["completed_trades"])
            if performance_inverse:
                performance_inverse["Strategy"] = "INVERSE"
                all_results.append(performance_inverse)
            
            print("\n\n--- Overall Performance Summary ---")
            if all_results:
                summary_df = pd.DataFrame(all_results).set_index("Strategy")
                summary_df['Total Return (sort)'] = summary_df['Total Return'].str.replace('%', '').astype(float)
                summary_df = summary_df.sort_values(by='Total Return (sort)', ascending=False).drop(columns=['Total Return (sort)'])
                print(summary_df)
                print("\nNote: Avg Duration omits Saturdays and Sundays because the markets are closed.")
            else:
                print("No results to display.")
        else:
            print(f"\n--- Running Simulation for Prioritization Method: {PRIORITIZATION_METHOD} ---")
            results = run_simulation(all_historical_data, master_index, PRIORITIZATION_METHOD, STRATEGY_TYPE, vix_data, sp500_data, fed_funds_data, verbose=True)
            print_single_run_details(results)

            # After the run, write the report
            sys.stdout = original_stdout # Restore stdout
            logs = log_stream.getvalue().splitlines()
            
            config = {
                "LEVERAGE_FACTOR": LEVERAGE_FACTOR,
                "INITIAL_CAPITAL": INITIAL_CAPITAL,
                "MAX_CONCURRENT_POSITIONS": MAX_CONCURRENT_POSITIONS,
                "START_DATE": START_DATE,
                "END_DATE": END_DATE,
                "TICKER_FILES": TICKER_FILES,
                "PRIORITIZATION_METHOD": PRIORITIZATION_METHOD,
                "STRATEGY_TYPE": STRATEGY_TYPE,
                "VIX_PROTECTION": VIX_PROTECTION,
                "PANIC_BUTTON": PANIC_BUTTON,
                "TIME_STOP": TIME_STOP,
                "SP500_ENTRY_THRESHOLD": SP500_ENTRY_THRESHOLD
            }
            write_report(results, config, logs)

    elapsed_seconds = time.perf_counter() - start_time
    minutes, seconds = divmod(elapsed_seconds, 60)
    print(f"\nTotal execution time: {int(minutes)} minutes {seconds:.1f} seconds")
