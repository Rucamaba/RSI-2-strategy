# `markets.py` - User Manual

## Overview

The `markets.py` script is responsible for loading the ticker symbols from the CSV files located in the `data/` directory. It also handles the de-duplication of tickers found in multiple market lists.

## How it Works

The script defines a single function, `get_ticker_list()`, which does the following:

1.  **Find CSV Files**: It scans the `data/` directory for all files with a `.csv` extension.
2.  **Read Tickers**: For each CSV file found, it reads the ticker symbols from the `Ticker` or `Symbol` column.
3.  **De-duplicate**: It combines all the tickers from the different files into a single list and removes any duplicates.
4.  **Blacklist**: It identifies tickers that are marked as "blacklisted" in the CSV files because they have historically performed poorly with this strategy. These tickers are still included in the analysis, but they are flagged so that the `analyzer.py` script can handle them differently. `backtest.py` won't buy tickers in the blacklist.
5.  **Return Lists**: It returns two lists: the final, de-duplicated list of tickers, and a list of blacklisted tickers.

## How to Use

This script is not intended to be run directly. It is imported and used by the `analyzer.py` script to get the list of tickers to be analyzed.

## Customization

To add a new market to the screener, you simply need to create a new CSV file in the `data/` directory.

To blacklist a ticker, you can add the ticker below `Blacklist:` in CSV files. The `markets.py` script will automatically detect the new file and include its tickers in the analysis, flagging the blacklisted ones.
