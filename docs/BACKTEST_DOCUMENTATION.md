# Backtesting Script Documentation (`backtest.py`)

## Purpose

The `backtest.py` script is designed to simulate and evaluate the performance of the RSI(2) mean-reversion trading strategy on historical data. It allows you to test the viability of the strategy over a defined period (by default, from 2020 to the present).

# RSI(2) Strategy Backtest Documentation

This document provides a comprehensive guide to using the `backtest.py` script. The script performs a backtest of a mean-reversion trading strategy based on the RSI(2), allowing users to test its effectiveness with historical market data.

## Trading Strategy

The strategy is based on a combination of three key technical indicators to generate buy and sell signals:

1.  **Trend Filter**: A buy trade is only considered if the asset's current closing price is higher than its 200-day Simple Moving Average (SMA). This ensures that we only trade in the direction of a long-term uptrend.
2.  **Entry Signal (Setup)**: The entry condition is triggered when the 2-period Relative Strength Index (RSI) drops below 5. Such a low RSI indicates an extreme oversold condition, suggesting a possible upward price reversal.
3.  **Exit Signal**: The position is closed (sold) when the asset's closing price exceeds its 5-day Simple Moving Average (SMA). This allows us to capture profits from short-term recoveries.

## Configuration

Before running the script, you can customize several parameters in the `CONFIGURATION` section of `backtest.py` to tailor the simulation to your preferences:

-   `LEVERAGE_FACTOR`: The level of leverage to use. For example, a value of `5` means a 5:1 ratio, where for every euro of your capital, you control 5 euros in the market. **Leverage carries significant risk; ensure you understand the risks before trading with leverage**
-   `INITIAL_CAPITAL`: The initial amount of capital for the backtest (e.g., `250.0`).
-   `MAX_CONCURRENT_POSITIONS`: The maximum number of positions that can be held open simultaneously.
-   `START_DATE` and `END_DATE`: The period for which the backtest will be run (e.g., `"2021-01-01"` to `"2025-12-31"`).
-   `TICKER_FILES`: A list of paths to CSV files containing the tickers of the assets to be included in the backtest. The script can handle multiple files (e.g., `['data/ibex35.csv', 'data/sp500.csv']`).
-   `PRIORITIZATION_METHOD`: The method used to select which assets to buy when there are more buy signals than available open positions.

## Prioritization Methods

When funds or position slots are limited, and multiple assets generate a buy signal on the same day, the script uses a prioritization method to decide which to invest in. You can choose from the following methods:

-   `'RSI'`: Prioritizes assets with the **lowest** RSI(2) value.
-   `'RSI_DESC'`: Prioritizes assets with the **highest** RSI(2) value (but still below the buy threshold).
-   `'A-Z'`: Sorts tickers alphabetically from A to Z.
-   `'Z-A'`: Sorts tickers alphabetically from Z to A.
-   `'HV_DESC'`: Prioritizes assets with the **highest** 100-day Historical Volatility (HV).
-   `'ADX_DESC'`: Prioritizes assets with the **highest** ADX(14) value, indicating a stronger trend.
-   `'ADX_ASC'`: Prioritizes assets with the **lowest** ADX(14) value, indicating a weaker trend or a range.
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
MAX_CONCURRENT_POSITIONS = 5
START_DATE = "2021-01-01"
END_DATE = "2025-12-31"
TICKER_FILES = ['data/ibex35.csv', 'data/sp500.csv', 'data/nasdaq100.csv']
PRIORITIZATION_METHOD = 'ALL'
```

And these are the results obtained:

```
--- Overall Performance Summary ---
         Final Value   Max Value Total Return Annualized Return  Total Trades Avg Duration (d) Winrate
Method
Z-A       $66,000.31  $86,460.99    26300.12%           205.25%          1368             5.63  68.27%
RSI       $19,524.48  $34,236.55     7709.79%           139.21%          1328             5.83  67.62%
RSI_DESC  $19,411.96  $24,269.01     7664.79%           138.94%          1351             5.69  67.43%
A-Z        $6,496.21   $8,683.57     2498.48%            91.93%          1351             5.71  66.91%
ADX_ASC    $2,028.62   $7,359.77      711.45%            52.05%          1323             5.85  66.52%
ADX_DESC   $1,687.18   $4,741.46      574.87%            46.54%          1315             5.87  65.93%
HV_DESC     $-769.34  $13,792.30     -407.73%             0.00%          1099             5.86  66.42%
```
### REMINDER: Past performance is not indicative of future results. 
### Invest responsibly and conduct your own research.