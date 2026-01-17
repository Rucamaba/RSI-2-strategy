"""
This script analyzes tickers to identify buying opportunities based on the RSI(2) mean-reversion strategy.
1. Trend Filter: Price > 200-day SMA && S&P 500 > (200-day SMA * SP500_ENTRY_THRESHOLD) && VIX < VIX_PROTECTION
2. Setup: RSI(2) < 5 (Normal) or RSI(2) > 95 (Inverse)
3. Sell: Price > 5-day SMA (Normal) or Price < 5-day SMA (Inverse)
"""

import yfinance as yf
import pandas_ta as ta
import pandas as pd
import os
import numpy as np
from datetime import datetime
from markets import get_tickers_from_csv

# --- CONFIGURATION ---
PRIORITIZATION_METHOD = "RSI"  # Options: 'RSI', 'RSI_DESC', 'A-Z', 'Z-A', 'HV_DESC', 'ADX_DESC'
STRATEGY_TYPE = "NORMAL" # Options: "NORMAL", "INVERSE", "BOTH"
VIX_PROTECTION = 45 # VIX threshold to shut off system (0 = disabled). System reactivates when VIX < threshold * 0.8
PANIC_BUTTON = False # If True, sell all open positions when VIX protection is triggered
SP500_ENTRY_THRESHOLD = 1.02 # S&P 500 must be above SMA(200) * this value to open positions (e.g., 1.01 = 1% above SMA)
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

def get_market_sentiment_data():
    """Downloads S&P 500 and VIX data to determine market sentiment."""
    print("--> Downloading S&P 500 and VIX data for market sentiment analysis...")
    # Download S&P 500 data
    sp500_data = yf.download('^GSPC', period="2y", interval="1d", progress=False)
    if sp500_data.empty:
        print(f"{Colors.RED}Fatal: Could not download S&P 500 data. Cannot assess market trend.{Colors.RESET}")
        return None, None
    if isinstance(sp500_data.columns, pd.MultiIndex):
        sp500_data.columns = sp500_data.columns.get_level_values(0)
    sp500_data.columns = sp500_data.columns.str.lower()
    sp500_data['sma_200'] = ta.sma(sp500_data['close'], length=200)

    # Download VIX data
    vix_data = yf.download('^VIX', period="1y", interval="1d", progress=False)
    if vix_data.empty:
        print(f"{Colors.YELLOW}Warning: Could not download VIX data. VIX protection will be disabled.{Colors.RESET}")
        vix_data = None
    else:
        if isinstance(vix_data.columns, pd.MultiIndex):
            vix_data.columns = vix_data.columns.get_level_values(0)
        vix_data.columns = vix_data.columns.str.lower()

    return sp500_data.iloc[-1], vix_data.iloc[-1] if vix_data is not None else None

def analyze_ticker(ticker_symbol, strategy_type):
    """
    Analyzes a single ticker and returns its signals and other data.
    Returns None if data is insufficient.
    """
    df = yf.download(ticker_symbol, period="2y", interval="1d", progress=False)
    
    if len(df) < 200:
        return None
    
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = df.columns.str.lower()

    # Calculate indicators
    df["sma_200"] = ta.sma(df["close"], length=200)
    df["sma_5"] = ta.sma(df["close"], length=5)
    df["rsi_2"] = ta.rsi(df["close"], length=2)
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

    latest = df.iloc[-1]
    if pd.isna(latest["sma_200"]) or pd.isna(latest["sma_5"]) or pd.isna(latest["rsi_2"]):
        return None

    analysis = {
        "ticker": ticker_symbol,
        "price": latest["close"],
        "rsi": latest["rsi_2"],
        "hv": latest["hv_100"],
        "adx": latest["adx_14"],
        "sma5": latest["sma_5"],
        "is_buy_signal": False,
        "is_exit_signal": False,
        "is_oversold": False,
        "strategy": None
    }

    # Normal Strategy Conditions
    if strategy_type in ["NORMAL", "BOTH"]:
        is_uptrend = latest["close"] > latest["sma_200"]
        is_oversold = latest["rsi_2"] < 5
        is_exit_zone = latest["close"] > latest["sma_5"]
        if is_uptrend and is_oversold:
            analysis["is_buy_signal"] = True
            analysis["strategy"] = "NORMAL"
        if is_exit_zone:
            analysis["is_exit_signal"] = True
            analysis["strategy"] = "NORMAL"

    # Inverse Strategy Conditions
    if strategy_type in ["INVERSE", "BOTH"]:
        is_downtrend = latest["close"] < latest["sma_200"]
        is_overbought = latest["rsi_2"] > 95
        is_exit_zone_inverse = latest["close"] < latest["sma_5"]
        if not analysis["is_buy_signal"] and is_downtrend and is_overbought:
             analysis["is_buy_signal"] = True
             analysis["strategy"] = "INVERSE"
        if is_exit_zone_inverse:
            if not analysis["is_exit_signal"]: # Prevent overwrite if NORMAL exit already triggered
                analysis["is_exit_signal"] = True
                analysis["strategy"] = "INVERSE"

    return analysis


if __name__ == "__main__":
    sp500_latest, vix_latest = get_market_sentiment_data()
    system_shut_off = False

    if sp500_latest is None:
        system_shut_off = True
        print(f"{Colors.RED}SYSTEM HALTED: Cannot proceed without S&P 500 data.{Colors.RESET}")
    else:
        sp500_price = sp500_latest['close']
        sp500_sma200 = sp500_latest['sma_200']
        is_sp500_bearish = sp500_price < sp500_sma200
        is_sp500_strong = sp500_price > (sp500_sma200 * SP500_ENTRY_THRESHOLD)
        vix_value = vix_latest['close'] if vix_latest is not None else 0

        # System State Logic
        if VIX_PROTECTION > 0 and vix_value > VIX_PROTECTION:
            system_shut_off = True
            print(f"{Colors.YELLOW}SYSTEM OFF: VIX ({vix_value:.2f}) is above threshold ({VIX_PROTECTION}).{Colors.RESET}")
        elif is_sp500_bearish:
            system_shut_off = True
            print(f"{Colors.YELLOW}SYSTEM OFF: S&P 500 is in a downtrend (Price: {sp500_price:.2f} < SMA200: {sp500_sma200:.2f}).{Colors.RESET}")
        elif not is_sp500_strong:
             system_shut_off = True
             print(f"{Colors.YELLOW}SYSTEM OFF: S&P 500 is not strong enough (Price: {sp500_price:.2f}, Required: >{sp500_sma200 * SP500_ENTRY_THRESHOLD:.2f}).{Colors.RESET}")
        else:
            print(f"{Colors.GREEN}SYSTEM ON: S&P 500 is strong and VIX is normal.{Colors.RESET}")
            print(f"-> S&P 500 Price: {sp500_price:.2f} | Strength Threshold: {sp500_sma200 * SP500_ENTRY_THRESHOLD:.2f}")
            if VIX_PROTECTION > 0: print(f"-> VIX: {vix_value:.2f} | Protection Threshold: {VIX_PROTECTION}")
    
    held_positions = load_positions()
    new_positions = held_positions.copy()
    exit_signals = []

    print("\n--- Checking for EXIT signals in held positions ---")
    if not held_positions:
        print("No positions currently held.")
    else:
        for ticker in held_positions:
            print(f"Analyzing held position: {ticker}...")
            analysis = analyze_ticker(ticker, STRATEGY_TYPE)

            if analysis and analysis["is_exit_signal"]:
                print(f"{Colors.RED}!!! EXIT SIGNAL for {ticker} at price {analysis['price']:.2f} (Strategy: {analysis.get('strategy', 'N/A')}) !!!{Colors.RESET}")
                exit_signals.append(analysis)
                if ticker in new_positions:
                    new_positions.remove(ticker)
            elif analysis:
                print(f"{Colors.YELLOW}No exit signal for {analysis['ticker']}. "
                      f"Current Price: ${analysis['price']:.2f}, "
                      f"Approx. Take Profit: ${analysis['sma5']:.2f}{Colors.RESET}")

    if system_shut_off:
        if PANIC_BUTTON and held_positions:
            print(f"{Colors.RED}\n--- PANIC BUTTON ACTIVATED: SELL all positions due to system shutdown. ---{Colors.RESET}")
        else:
             print("\n--- Scanning for new BUY signals HALTED due to system being OFF. ---")
    else:
        print("\n--- Scanning for new BUY signals ---")
        market_files = [os.path.join("data", f) for f in os.listdir("data") if f.endswith(".csv")]
        all_tickers = []
        for f in market_files:
            all_tickers.extend(get_tickers_from_csv(f))
        
        unique_tickers = sorted(list(set(all_tickers)))
        print(f"--> Analyzing {len(unique_tickers)} unique tickers.")
        
        buy_signals = []
        for ticker in unique_tickers:
            if ticker in held_positions:
                continue
            
            analysis = analyze_ticker(ticker, STRATEGY_TYPE)

            if analysis and analysis["is_buy_signal"]:
                buy_signals.append(analysis)
                print(f"{Colors.GREEN}BUY SIGNAL (Strategy: {analysis['strategy']}): {ticker} @ ${analysis['price']:.2f} (Approx. Take Profit: ${analysis['sma5']:.2f}){Colors.RESET}")
                if ticker not in new_positions:
                    new_positions.append(ticker)
        
        if buy_signals:
            print(f"\n--- Strong Buy Signals (Sorted by {PRIORITIZATION_METHOD}) ---")
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
                 print(f"{Colors.GREEN}BUY ({signal['strategy']}): {signal['ticker']} @ ${signal['price']:.2f} (RSI: {signal['rsi']:.2f}, HV: {signal.get('hv', 0):.2f}, ADX: {signal.get('adx', 0):.2f}){Colors.RESET}")

    save_positions(new_positions)
    print("\nPositions file updated.")
