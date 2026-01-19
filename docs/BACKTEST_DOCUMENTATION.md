# Backtesting Script Documentation (`backtest.py`)

## Purpose

The `backtest.py` script is designed to simulate and evaluate the performance of the RSI(2) mean-reversion trading strategy on historical data. It allows you to test the viability of the strategy over a defined period (by default, from 2020 to the present).

# RSI(2) Strategy Backtest Documentation

This document provides a comprehensive guide to using the `backtest.py` script. The script performs a backtest of a mean-reversion trading strategy based on the RSI(2), allowing users to test its effectiveness with historical market data.

## Trading Strategy

The strategy is based on a combination of three key technical indicators to generate buy and sell signals:

1.  **Trend Filter**: A buy trade is only considered if the asset's current closing price is higher than its 200-day Simple Moving Average (SMA), the S&P 500 is above its 200-day SMA by a certain threshold, and the VIX is below a certain level. This ensures that we only trade in the direction of a long-term uptrend and in favorable market conditions.
2.  **Entry Signal (Setup)**: The entry condition is triggered when the 2-period Relative Strength Index (RSI) drops below 5, the price is below the 5-day SMA, and the ADX(14) is below 50. Such a low RSI indicates an extreme oversold condition, suggesting a possible upward price reversal.
3.  **Exit Signal**: The position is closed (sold) when the asset's closing price exceeds its 5-day Simple Moving Average (SMA) or after a certain number of days (TIME_STOP). This allows us to capture profits from short-term recoveries.

## Configuration

Before running the script, you can customize several parameters in the `CONFIGURATION` section of `backtest.py` to tailor the simulation to your preferences:

-   `LEVERAGE_FACTOR`: The level of leverage to use. For example, a value of `5` means a 5:1 ratio, where for every euro of your capital, you control 5 euros in the market. **Leverage carries significant risk; ensure you understand the risks before trading with leverage**
-   `INITIAL_CAPITAL`: The initial amount of capital for the backtest (e.g., `350.0`).
-   `MAX_CONCURRENT_POSITIONS`: The maximum number of positions that can be held open simultaneously (e.g., `8`).
-   `START_DATE` and `END_DATE`: The period for which the backtest will be run (e.g., `"2021-01-01"` to `"2025-12-31"`).
-   `TICKER_FILES`: A list of paths to CSV files containing the tickers of the assets to be included in the backtest. The script can handle multiple files (e.g., `['data/ibex35.csv', 'data/sp500.csv']`).
-   `PRIORITIZATION_METHOD`: The method used to select which assets to buy when there are more buy signals than available open positions.
-   `STRATEGY_TYPE`: The type of strategy to backtest. Options are `"NORMAL"`, `"INVERSE"`, and `"BOTH"`.
-   `VIX_PROTECTION`: The VIX threshold to shut off the system (e.g., `45`). The system reactivates when the VIX is below the threshold * 0.8.
-   `PANIC_BUTTON`: If `True`, all open positions will be sold when the VIX protection is triggered.
-   `TIME_STOP`: The maximum number of days to hold a position (e.g., `10`).
-   `SP500_ENTRY_THRESHOLD`: The S&P 500 must be above its 200-day SMA * this value to open positions (e.g., `1.02`).

## Prioritization Methods

When funds or position slots are limited, and multiple assets generate a buy signal on the same day, the script uses a prioritization method to decide which to invest in. You can choose from the following methods:

-   `'RSI'`: Prioritizes assets with the **lowest** RSI(2) value.
-   `'RSI_DESC'`: Prioritizes assets with the **highest** RSI(2) value (but still below the buy threshold).
-   `'A-Z'`: Sorts tickers alphabetically from A to Z.
-   `'Z-A'`: Sorts tickers alphabetically from Z to A.
-   `'HV_DESC'`: Prioritizes assets with the **highest** 100-day Historical Volatility (HV).
-   `'ADX_DESC'`: Prioritizes assets with the **highest** ADX(14) value, indicating a stronger trend.
-   `'ALL'`: Runs the backtest for **each** of the above prioritization methods and presents a comparative table of the results.

## Running the Script

To run the backtest, simply execute the script from your terminal:

```bash
python backtest.py
```

The script will perform the following steps:

1.  **Load Tickers**: Reads the tickers from the files specified in `TICKER_FILES`.
2.  **Download Data**: Obtains historical price data for each ticker from Yahoo Finance.
3.  **Pre-calculate Indicators**: Calculates the necessary indicators (SMA, RSI, HV, ADX) for each day of the backtest period.
4.  **Run Simulation**: Iterates through each day of the testing period, applying the strategy logic, managing positions, and calculating portfolio value.
5.  **Present Results**: Displays a detailed performance summary, including the final portfolio value, total and annualized return, trade statistics, and the best/worst trades.

## Output

If `PRIORITIZATION_METHOD` is set to a specific method, the script will print:

-   A detailed log of each buy and sell trade.
-   A summary of the portfolio's performance.
-   Detailed statistics on completed trades.
-   A list of positions that remained open at the end of the backtest period.

If `PRIORITIZATION_METHOD` is set to `'ALL'`, the script will display a summary table comparing the key performance of each method, allowing you to see which prioritization strategy was most effective during the test period.

## Example

Here is an example of a backtest run with the following parameters:

```python
LEVERAGE_FACTOR = 5
INITIAL_CAPITAL = 250.0
MAX_CONCURRENT_POSITIONS = 8
START_DATE = "2021-01-01"
END_DATE = "2025-12-31"
TICKER_FILES = ['data/ibex35.csv', 'data/sp500.csv', 'data/nasdaq100.csv']
PRIORITIZATION_METHOD = 'ALL'
STRATEGY_TYPE = "NORMAL"
VIX_PROTECTION = 45
PANIC_BUTTON = False
TIME_STOP = 10
SP500_ENTRY_THRESHOLD = 1.02
```

And these are the results obtained:

```
--- Overall Performance Summary for NORMAL Strategy ---
         Final Value   Max Value Total Return Annualized Return  Total Trades Avg Duration (d) Winrate Avg Profit per Trade
Method
RSI       $17,044.36  $19,422.79     6717.74%           132.80%          1652             3.94  68.64%                2.44%
Z-A        $9,390.33  $10,467.04     3656.13%           106.62%          1671             3.89  66.97%                2.17%
RSI_DESC   $6,909.53   $7,792.64     2663.81%            94.31%          1664             3.89  67.25%                2.06%
HV_DESC    $5,328.95   $9,294.67     2031.58%            84.47%          1643             3.96  66.89%                2.30%
A-Z        $5,184.22   $5,947.26     1973.69%            83.45%          1639             3.96  66.87%                1.91%
ADX_DESC   $3,058.25   $4,072.42     1123.30%            65.07%          1633             4.00  65.77%                1.80%
```
### REMINDER: Past performance is not indicative of future results. 
### Invest responsibly and conduct your own research.