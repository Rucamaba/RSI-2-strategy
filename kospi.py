"""
This script scans the top 100 KOSPI stocks by market capitalization
and filters those meeting the RSI(2) mean-reversion criteria.
"""

from pykrx import stock
import yfinance as yf
import pandas_ta as ta
import pandas as pd
from datetime import datetime


def get_kospi_top_100_signals():
    pass
