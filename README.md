# RSI(2) Mean Reversion Stock Screener

This project is an automated stock screening tool that scans multiple markets to find trading opportunities based on a popular mean-reversion strategy. It identifies stocks that are in a long-term uptrend but have experienced a sharp short-term pullback, making them potential "buy the dip" candidates.

## Original Project

This project is a significantly modified and extended version of the original [rsi2-bot](https://github.com/youngha-mikoto/rsi2-bot) by youngha-mikoto. Credit for the core strategy and initial implementation goes to the original author.

## Features

- **Multi-Market Analysis**: Scans a configurable list of markets by reading ticker symbols from CSV files located in the `data/` directory.
- **Flexible Strategy**: Implements the RSI(2) trading strategy, checking for stocks that are above their 200-day moving average but have a 2-period RSI below a set threshold (currently 5).
- **Dual Signal System**: 
    -   **BUY Signal (Green)**: Triggered when all strategy conditions are met.
    -   **Potential Signal (Yellow)**: Triggered when only the RSI condition is met, indicating a stock to watch.
- **Position Tracking**: Automatically saves all confirmed BUY signals to `positions.txt` to track a portfolio of held assets.
- **Exit Signal Monitoring**: On each run, it first checks all held positions for an exit signal (price closing above the 5-day moving average) and prints a notification (in Red).
- **Efficient & Clean**: De-duplicates tickers found in multiple market lists to avoid redundant analysis.
- **Ticker Generation**: Includes a helper script (`generate_tickers.py`) to automatically create a list of S&P 500 companies.

## The Strategy

This screener is based on a strategy popularized by Larry Connors.

- **Buy Condition**: 
    1. The stock's current price must be above its 200-day Simple Moving Average (SMA).
    2. The stock's 2-period Relative Strength Index (RSI) must be below 5.
- **Exit Condition**:
    1. The stock's current price must be above its 5-day Simple Moving Average (SMA).

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
python main.py
```

The script will:
1.  Check for exit signals on positions listed in `positions.txt`.
2.  Scan all tickers from the `.csv` files in the `data/` directory for new signals.
3.  Print any BUY, EXIT, or Potential signals it finds, with colors for easy identification.
4.  Update `positions.txt` with any new BUY signals. You can modify this file with your open positions.
