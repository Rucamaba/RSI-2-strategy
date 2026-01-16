"""
This script analyzes tickers to identify buying opportunities
based on the RSI(2) mean-reversion strategy.
1. Trend Filter: Price > 200-day SMA
2. Setup: RSI(2) < 5
3. Sell: Price > 5-day SMA
"""

import yfinance as yf
import pandas_ta as ta
import pandas as pd
import os
import numpy as np
from markets import get_tickers_from_csv

# --- CONFIGURATION ---
PRIORITIZATION_METHOD = "RSI"  # Options: 'RSI', 'RSI_DESC', 'A-Z', 'Z-A', 'HV_DESC', 'ADX_DESC'

POSITIONS_FILE = "positions.txt"

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'

def load_positions():
    """Loads tickers from the positions file."""
    if not os.path.exists(POSITIONS_FILE):
        return []
    with open(POSITIONS_FILE, "r") as f:
        positions = [line.strip() for line in f.readlines() if line.strip()]
    return positions

def save_positions(positions):
    """Saves a list of tickers to the positions file."""
    with open(POSITIONS_FILE, "w") as f:
        for ticker in positions:
            f.write(f"{ticker}\n")

def analyze_ticker(ticker_symbol):
    """
    Analyzes a single ticker and returns its buy/sell signals and price.
    Returns None if data is insufficient.
    """
    df = yf.download(ticker_symbol, period="2y", interval="1d", progress=False)
    
    if len(df) < 200:
        print(f"Warning: Not enough data for {ticker_symbol}, skipping.")
        return None
    # yfinance can return MultiIndex columns; flatten and standardize to lowercase
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = df.columns.str.lower()

    # Calculate indicators
    df["SMA_200"] = ta.sma(df["close"], length=200)
    df["SMA_5"] = ta.sma(df["close"], length=5)
    df["RSI_2"] = ta.rsi(df["close"], length=2)
    df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
    df['hv_100'] = df['log_returns'].rolling(window=100).std() * np.sqrt(252)
    if all(c in df.columns for c in ['high', 'low', 'close']):
        adx_df = ta.adx(df["high"], df["low"], df["close"], length=14)
        if adx_df is not None and not adx_df.empty:
            df['adx_14'] = adx_df.iloc[:, 0]
        else:
            df['adx_14'] = np.nan
    else:
        df['adx_14'] = np.nan

    # Get the latest data
    current_price = df["close"].iloc[-1]
    rsi2 = df["RSI_2"].iloc[-1]
    sma200 = df["SMA_200"].iloc[-1]
    sma5 = df["SMA_5"].iloc[-1]
    hv = df["hv_100"].iloc[-1]
    adx = df["adx_14"].iloc[-1]

    # Ensure we have valid indicator values
    if pd.isna(sma200) or pd.isna(sma5) or pd.isna(rsi2):
        return None

    # Define strategy conditions
    is_uptrend = current_price > sma200
    is_oversold = rsi2 < 5
    is_exit_zone = current_price > sma5

    return {
        "ticker": ticker_symbol,
        "price": current_price,
        "is_buy_signal": is_uptrend and is_oversold and (current_price < sma5),
        "is_exit_signal": is_exit_zone,
        "is_oversold": is_oversold,
                "rsi": rsi2,
                "hv": hv,
                "adx": adx
            }

if __name__ == "__main__":
    # 1. Load tickers of currently held positions
    held_positions = load_positions()
    new_positions = held_positions.copy()

    # 2. Check for EXIT signals in currently held positions
    print("--- Checking for EXIT signals in held positions ---")
    if not held_positions:
        print("No positions currently held.")
    else:
        for ticker in held_positions:
            print(f"Analyzing held position: {ticker}...")
            analysis = analyze_ticker(ticker)
            if analysis and analysis["is_exit_signal"]:
                print(f"{Colors.RED}!!! EXIT SIGNAL for {analysis['ticker']} at price {analysis['price']:.2f} !!!{Colors.RESET}")
                new_positions.remove(ticker)

    # 3. Check for new BUY signals in the market
        print("\n--- Scanning for new BUY signals ---")
        market_files = [os.path.join("data", f) for f in os.listdir("data") if f.endswith(".csv")]
        all_tickers = []
        for f in market_files:
                all_tickers.extend(get_tickers_from_csv(f))
            
        unique_tickers = sorted(list(set(all_tickers)))
        print(f"--> Analyzing {len(unique_tickers)} unique tickers after removing {len(all_tickers) - len(unique_tickers)} duplicates.")
        all_tickers = unique_tickers
        
        buy_signals = []
        potential_signals = []
    
        for ticker in all_tickers:
            if ticker in held_positions:
                continue
            
            print(f"Analyzing new ticker: {ticker}...")
            analysis = analyze_ticker(ticker)
    
            if not analysis:
                continue
            
            if analysis["is_buy_signal"]:
                buy_signals.append(analysis)
                print(f"{Colors.GREEN}BUY SIGNAL: {ticker} @ ${analysis['price']:.2f}{Colors.RESET}")
                if ticker not in new_positions:
                    new_positions.append(ticker)
            elif analysis["is_oversold"]:
                potential_signals.append(analysis)
        
        print("\n--- Summary ---")
        if not buy_signals and not potential_signals:
            print("No new signals found.")
        else:
            if buy_signals:
                print(f"\n--- Strong Buy Signals (Sorted by {PRIORITIZATION_METHOD}) ---")
                # Sort signals based on the chosen method
                if PRIORITIZATION_METHOD == 'RSI':
                    buy_signals.sort(key=lambda x: x['rsi'])
                elif PRIORITIZATION_METHOD == 'RSI_DESC':
                    buy_signals.sort(key=lambda x: x['rsi'], reverse=True)
                elif PRIORITIZATION_METHOD == 'A-Z':
                    buy_signals.sort(key=lambda x: x['ticker'])
                elif PRIORITIZATION_METHOD == 'Z-A':
                    buy_signals.sort(key=lambda x: x['ticker'], reverse=True)
                elif PRIORITIZATION_METHOD == 'HV_DESC':
                    buy_signals.sort(key=lambda x: x['hv'] if not pd.isna(x['hv']) else 0, reverse=True)
                elif PRIORITIZATION_METHOD == 'ADX_DESC':
                    buy_signals.sort(key=lambda x: x['adx'] if not pd.isna(x['adx']) else 0, reverse=True)
                
                for signal in buy_signals:
                    print(f"{Colors.GREEN}BUY: {signal['ticker']} @ ${signal['price']:.2f} (RSI: {signal['rsi']:.2f}, HV: {signal.get('hv', 0):.2f}, ADX: {signal.get('adx', 0):.2f}){Colors.RESET}")
    
            if potential_signals:
                print("\n--- Potential Signals (Watchlist) ---")
                potential_signals.sort(key=lambda x: x['rsi'])
                for signal in potential_signals:
                    print(f"{Colors.YELLOW}WATCH: {signal['ticker']} @ ${signal['price']:.2f} (RSI: {signal['rsi']:.2f}){Colors.RESET}")

    # 4. Save updated positions
        save_positions(new_positions)
        print("\nPositions file updated.")
