# RSI(2) Mean Reversion Stock Screener

This project is an automated stock screening tool that scans multiple markets to find trading opportunities based on a popular mean-reversion strategy. It identifies stocks that are in a long-term uptrend but have experienced a sharp short-term pullback, making them potential "buy the dip" candidates.

## Original Project

This project is a significantly modified and extended version of the original [rsi2-bot](https://github.com/youngha-mikoto/rsi2-bot) by youngha-mikoto. Credit for the core strategy and initial implementation goes to the original author.

## The Strategy

This screener is based on a strategy popularized by Larry Connors.

- **Buy Condition**: 
    1. The stock's current price must be above its 200-day Simple Moving Average (SMA).
    2. The stock's 2-period Relative Strength Index (RSI) must be below 5.
- **Exit Condition**:
    1. The stock's current price must be above its 5-day Simple Moving Average (SMA).

## How it Works

The project is divided into several scripts, each with a specific purpose:

- **`analyzer.py`**: This is the main script that orchestrates the entire process. It reads the markets to be analyzed, checks for exit signals on existing positions, and scans for new buy signals.
- **`markets.py`**: This script is responsible for loading the ticker symbols from the CSV files located in the `data/` directory. It also handles the de-duplication of tickers found in multiple market lists.
- **`backtest.py`**: This script allows you to backtest the strategy on a single ticker. It will generate a detailed report with the results of the backtest.
- **`generate_tickers.py`**: This is a helper script to automatically create a list of S&P 500 (or other markets) companies and save it as a CSV file in the `data/` directory.

## Setup & Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Install Dependencies**: Make sure you have Python 3 installed. Then, install the required libraries using the provided `requirements.txt` file.
    ```bash
    pip install -r requirements.txt
    ```

3.  **Prepare Market Data**: The screener reads tickers from CSV files in the `data/` directory.
    -   The project comes with CSV files for the IBEX 35 and NASDAQ 100.
    -   To generate the S&P 500 list, run the included helper script:
        ```bash
        python generate_tickers.py
        ```
    -   You can add any other market by creating a CSV file in the `data/` directory. The file must contain a header, and the column with the stock symbols should be named `Ticker` or `Symbol`.

## How to Use

Simply run the main script from your terminal:

```bash
python analyzer.py
```

The script will:
1.  Check for exit signals on positions listed in `positions.txt`.
2.  Scan all tickers from the `.csv` files in the `data/` directory for new signals.
3.  Print any BUY, EXIT, or Potential signals it finds, with colors for easy identification.
4.  Update `positions.txt` with any new BUY signals. You can modify this file with your open positions.

## Documentation

For more detailed information about each script, please refer to the documentation in the `docs/` directory:

- [`analyzer.py` - User Manual](docs/ANALYZER_DOCUMENTATION.md)
- [`backtest.py` - User Manual](docs/BACKTEST_DOCUMENTATION.md)
- [`generate_tickers.py` - User Manual](docs/GENERATE_TICKERS_DOCUMENTATION.md)
- [`markets.py` - User Manual](docs/MARKETS_DOCUMENTATION.md)
