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

    # Flatten Multi-Index columns to Single-Index
    df.columns = df.columns.get_level_values(0)

    # 2. Calculate Indicators (SMA 200, SMA 5, RSI 2)
    df["SMA_200"] = ta.sma(df["Close"], length=200)
    df["SMA_5"] = ta.sma(df["Close"], length=5)
    df["RSI_2"] = ta.rsi(df["Close"], length=2)

    # 3. Extract latest values for decision
    latest_data = df.iloc[-1]
    current_price = latest_data["Close"]
    rsi2 = latest_data["RSI_2"]
    sma200 = latest_data["SMA_200"]
    sma5 = latest_data["SMA_5"]

    # 4. Define Strategy Logic
    is_uptrend = current_price > sma200
    is_oversold = rsi2 < 10
    is_exit_zone = current_price > sma5

    # 5. Display Results
    print("-" * 40)
    print(f"Date: {latest_data.name.strftime('%Y-%m-%d')}")
    print(f"Ticker: {ticker_symbol}")
    print(f"Current Price: {current_price:.2f}")
    print(f"200 SMA (Trend): {sma200:.2f}")
    print(f"RSI(2) Value: {rsi2:.2f}")
    print(f"5 SMA (Exit Target): {sma5:.2f}")
    print("-" * 40)

    if is_uptrend and is_oversold:
        print("RESULT: [BUY SIGNAL] Conditions met.")
    if is_exit_zone:
        print("RESULT: [EXIT] Above 5 SMA. Good time to take profit.")


if __name__ == "__main__":
    # You can change the ticker here (e.g., TSLA, BTC-USD, NVDA)
    target_ticker = "VOO"
    check_rsi2_signal(target_ticker)
