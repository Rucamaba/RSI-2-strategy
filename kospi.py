import FinanceDataReader as fdr
import yfinance as yf
import pandas_ta as ta


def get_kospi_top_100():
    df_kospi = fdr.StockListing("KOSPI")
    kospi_100 = df_kospi.sort_values(by="Marcap", ascending=False).head(100)

    ret = []

    for _, row in kospi_100.iterrows():
        ticker = row["Code"]
        name = row["Name"]
        symbol = f"{ticker}.KS"

        ret.append(symbol)

    return ret


def recommend_kospi_stocks():
    kospi_stocks = get_kospi_top_100()

    ret = []

    for symbol in kospi_stocks:
        df = yf.download(symbol, period="2y", interval="1d", progress=False)

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
        if sma200 is None:
            continue
        is_uptrend = current_price > sma200
        is_oversold = rsi2 < 10
        is_exit_zone = current_price > sma5

        if is_uptrend and is_oversold:
            print(symbol, rsi2)
            ret.append(symbol)

    return ret


recommend_kospi_stocks()
