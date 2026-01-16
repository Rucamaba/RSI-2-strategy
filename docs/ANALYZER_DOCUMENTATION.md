# `analyzer.py` - User Manual

## Overview

The `analyzer.py` script is the core of the RSI(2) Mean Reversion Stock Screener. It orchestrates the entire process of scanning markets, identifying trading signals, and managing positions.

## How it Works

The script performs the following steps in sequence:

1.  **Load Positions**: It reads the `positions.txt` file to get a list of currently held positions.
2.  **Check Exit Signals**: For each position in the list, it checks if the exit condition has been met (i.e., the price has closed above the 5-day SMA). If an exit signal is found, it prints a message in red.
3.  **Load Markets**: It loads the ticker symbols from all the `.csv` files in the `data/` directory using the `markets.py` script.
4.  **Scan for Buy Signals**: It iterates through all the loaded tickers and checks if they meet the buy conditions of the strategy:
    -   The stock's current price is above its 200-day SMA.
    -   The stock's 2-period RSI is below 5.
5.  **Signal System**:
    -   **BUY Signal (Green)**: If both buy conditions are met, the script prints a "BUY" signal in green and adds the ticker to the `positions.txt` file.
    -   **Potential Signal (Yellow)**: If only the RSI condition is met, it prints a "Potential" signal in yellow. This indicates that the stock is in a short-term pullback but not yet in a long-term uptrend, so it's worth watching.
6.  **Update Positions**: After scanning all the tickers, the `positions.txt` file is updated with any new buy signals.

## How to Use

To run the script, simply execute the following command in your terminal:

```bash
python analyzer.py
```

The script will then print the signals it finds directly to the console.

## Files

-   **`positions.txt`**: This file contains a list of the ticker symbols for the stocks you currently hold. The `analyzer.py` script reads this file to check for exit signals and updates it with new buy signals. You can also manually edit this file to add or remove positions.
-   **`data/` directory**: This directory should contain one or more `.csv` files, each with a list of ticker symbols for a specific market. The script will automatically load all `.csv` files in this directory.
