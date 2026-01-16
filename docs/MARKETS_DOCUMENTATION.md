# `markets.py` - User Manual

## Overview

The `markets.py` script is responsible for loading the ticker symbols from the CSV files located in the `data/` directory. It also handles the de-duplication of tickers found in multiple market lists.

## How it Works

The script defines a single function, `get_ticker_list()`, which does the following:

1.  **Find CSV Files**: It scans the `data/` directory for all files with a `.csv` extension.
2.  **Read Tickers**: For each CSV file found, it reads the ticker symbols from the `Ticker` or `Symbol` column.
3.  **De-duplicate**: It combines all the tickers from the different files into a single list and removes any duplicates.
4.  **Return List**: It returns the final, de-duplicated list of tickers.

## How to Use

This script is not intended to be run directly. It is imported and used by the `analyzer.py` script to get the list of tickers to be analyzed.

## Customization

To add a new market to the screener, you simply need to create a new CSV file in the `data/` directory. The file must have a header, and the column containing the ticker symbols must be named either `Ticker` or `Symbol`. The `markets.py` script will automatically detect the new file and include its tickers in the analysis.
