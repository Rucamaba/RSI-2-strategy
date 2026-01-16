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
from markets import get_tickers_from_csv

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

    # Get the latest data
    current_price = df["close"].iloc[-1]
    rsi2 = df["RSI_2"].iloc[-1]
    sma200 = df["SMA_200"].iloc[-1]
    sma5 = df["SMA_5"].iloc[-1]

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
    print("\n--- Checking for NEW BUY signals from market CSV files ---")
    market_files = [
        "data/ibex35.csv",
        "data/nasdaq100.csv",
        "data/sp500.csv"
    ]
    all_tickers = []
    for f in market_files:
        all_tickers.extend(get_tickers_from_csv(f))

    print(f"--> Loaded {len(all_tickers)} total tickers.")
    
    # Remove duplicates for efficiency, as some tickers are in multiple indices
    unique_tickers = sorted(list(set(all_tickers)))
    
    if len(unique_tickers) < len(all_tickers):
        print(f"--> Analyzing {len(unique_tickers)} unique tickers after removing {len(all_tickers) - len(unique_tickers)} duplicates.")
    
    for ticker in unique_tickers:
        if ticker in new_positions:
            continue  # Skip if we already have a position

        print(f"Analyzing market for: {ticker}...")
        analysis = analyze_ticker(ticker)
        if analysis:
            if analysis["is_buy_signal"]:
                print(f"{Colors.GREEN}!!! BUY SIGNAL for {analysis['ticker']} at price {analysis['price']:.2f} !!!{Colors.RESET}")
                new_positions.append(ticker)
            elif analysis["is_oversold"]:
                print(f"{Colors.YELLOW}--- Potential Signal (RSI<5 BUT DON'T BUY) for {analysis['ticker']} at price {analysis['price']:.2f} ---{Colors.RESET}")

    # 4. Save the updated list of positions
    save_positions(new_positions)
    print(f"\n--- Analysis complete. Updated positions saved to {POSITIONS_FILE}. ---")
    print(f"Current positions: {new_positions}")
