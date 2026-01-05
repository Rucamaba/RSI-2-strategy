"""
This script monitors a specific ticker to identify buying opportunities
based on the RSI(2) mean-reversion strategy.
1. Trend Filter: Price > 200-day SMA
2. Setup: RSI(2) < 10
"""

import yfinance as yf
import pandas_ta as ta
import pandas as pd


def check_rsi2_signal(ticker_symbol):
    # 1. Fetch historical data
    print(f"Fetching data for {ticker_symbol}...")
    df = yf.download(ticker_symbol, period="2y", interval="1d", progress=False)

    if len(df) < 200:
        print("Error: Not enough data for 200 SMA calculation.")
        return
