import yfinance as yf
import pandas_ta as ta
import pandas as pd
import FinanceDataReader as fdr


def buy_recommend(ticker_symbol, name):
    df = yf.download(ticker_symbol, period="2y", interval="1d", progress=False)

    # Flatten Multi-Index columns to Single-Index
    df.columns = df.columns.get_level_values(0)

    # Calculate Indicators (SMA 200, SMA 5, RSI 2)
    df["SMA_200"] = ta.sma(df["Close"], length=200)
    df["SMA_5"] = ta.sma(df["Close"], length=5)
    df["RSI_2"] = ta.rsi(df["Close"], length=2)

    latest_data = df.iloc[-1]

    current_price = latest_data["Close"]
    rsi2 = latest_data["RSI_2"]
    sma200 = latest_data["SMA_200"]

    if sma200 is None:
        return

    is_uptrend = current_price > sma200
    is_oversold = rsi2 < 10

    if is_uptrend and is_oversold:
        print(ticker_symbol, name, current_price, rsi2)


def get_kospi_200_rsi2():
    df = pd.read_csv("./data/krx_kospi_200.csv", encoding="cp949")
    for _, row in df.iterrows():
        ticker_symbol = row.to_dict()["종목코드"]
        buy_recommend(ticker_symbol + ".KS", row.to_dict()["종목명"])


get_kospi_200_rsi2()
