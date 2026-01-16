"""
This script provides utility functions to read ticker symbols from CSV files
for various market indices.
"""

import pandas as pd
import os

def get_tickers_from_csv(file_path, ticker_column="Ticker"):
    """
    Reads a list of tickers from a specified column in a CSV file.

    Args:
        file_path (str): The path to the CSV file.
        ticker_column (str): The name of the column containing the tickers.

    Returns:
        list: A list of tickers, or an empty list if the file cannot be read.
    """
    if not os.path.exists(file_path):
        print(f"Warning: Market file not found at '{file_path}'. Skipping.")
        return []
    
    try:
        df = pd.read_csv(file_path, header=None)
        tickers = df[0].dropna().tolist()
        return tickers
    except Exception as e:
        print(f"Error reading CSV file '{file_path}': {e}")
        return []
