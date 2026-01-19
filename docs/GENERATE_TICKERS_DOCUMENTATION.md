# `generate_tickers.py` - User Manual

## Overview

The `generate_tickers.py` script is a helper utility that allows you to automatically generate a list of ticker symbols for a given market and save it as a CSV file in the `data/` directory.

## How it Works

The script uses the `yfinance` library to download the list of tickers for a specific index. It then saves this list to a CSV file. The default index is the S&P 500, but you can easily modify the script to use other indices.

## How to Use

To run the script, simply execute the following command in your terminal:

```bash
python generate_tickers.py
```

This will create a new file named `sp500.csv` in the `data/` directory, containing the ticker symbols for all the companies in the S&P 500 index.

## Customization

You can customize the script to download the tickers for other indices by changing the `tickers` variable in the script. For example, to download the tickers for the NASDAQ 100, you would change the line:

```python
tickers = si.get_nasdaq_100()
```

You can also add a `Blacklist` section to the CSV file to mark tickers that should not be traded. The `analyzer.py` script will still analyze these tickers, but it will advice about historically poor performance.

```
