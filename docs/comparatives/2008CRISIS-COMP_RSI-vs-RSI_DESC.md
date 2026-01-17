# Backtest Analysis: Navigating the 2008 Financial Crisis

This document analyzes the performance of a mean-reversion trading strategy during the severe market downturn of the 2008 financial crisis, specifically from October 1, 2007, to March 31, 2009. The analysis highlights the defensive mechanisms implemented in the system to mitigate risk and minimize drawdowns during periods of high volatility and negative market trends.

## Backtest Configuration

The simulation was executed with the following parameters:

```python
LEVERAGE_FACTOR = 5
INITIAL_CAPITAL = 350.0
MAX_CONCURRENT_POSITIONS = 8
START_DATE = "2007-10-01"
END_DATE = "2009-03-31"
TICKER_FILES = ['data/ibex35.csv', 'data/sp500.csv', 'data/nasdaq100.csv']
PRIORITIZATION_METHOD = ['RSI', 'RSI_DESC']
STRATEGY_TYPE = "NORMAL"
VIX_PROTECTION = 45
PANIC_BUTTON = False
TIME_STOP = 10
SP500_ENTRY_THRESHOLD = 1.02
```

## Performance Results

The results below show a slight loss, which can be considered a strong outcome given the S&P 500 lost over 40% of its value during the same period. The system's ability to preserve capital was paramount.

```
--- Overall Performance Summary for NORMAL Strategy ---
         Final Value Max Value Total Return Annualized Return  Total Trades Avg Duration (d) Winrate
Method
RSI          $325.59   $438.82       -6.97%            -4.71%            44             4.11  63.64%
RSI_DESC     $312.44   $406.68      -10.73%            -7.30%            44             4.16  63.64%
```

## Core Defensive Mechanisms

The strategy's resilience is not accidental but the result of several integrated safety protocols designed to halt trading activity when market conditions are unfavorable. These mechanisms are crucial for capital preservation.

### 1. S&P 500 Trend Filter (Primary Defense)

This is the most critical protection layer. The system is only permitted to open **new long positions** if two conditions related to the S&P 500 index are met:
- The index's current price must be above its 200-day Simple Moving Average (SMA).
- To confirm strength, the price must also be at least 2% above the 200-day SMA (`SP500_ENTRY_THRESHOLD = 1.02`).

Conversely, the system's ability to open new trades is **immediately shut off** if the S&P 500 price falls below its 200-day SMA. This single rule is the primary reason for the low trade count during the 2008 crisis. The market was in a persistent downtrend, rarely providing the required bullish signal to resume trading.

A log snippet from the backtest clearly illustrates this mechanism in action:

- **`2007-11-07`**: `System shut off because S&P500 downtrend (Price: 1475.62 < SMA200: 1483.12)`
- **`2007-12-10`**: `System shut on | VIX: 20.74 < 36.00 | S&P500: 1515.96 > SMA200: 1485.04 (threshold: 1514.74)`
- **`2007-12-11`**: `System shut off because S&P500 downtrend (Price: 1477.65 < SMA200: 1485.44)`

As seen here, the system remained inactive for a month. It reactivated for only a single day before the bearish trend resumed, forcing it back into a defensive, inactive state. This "on/off" switching, dictated by the broad market trend, is fundamental to avoiding large drawdowns.

### 2. Low Trade Frequency by Design

The core strategy is based on a 2-period Relative Strength Index (RSI), entering trades only when the RSI value is below 5. This signifies an extremely oversold, short-term condition. Such opportunities are inherently rare. By combining this strict entry criterion with the market trend filter, the number of potential trades is drastically reduced. This selectivity is a feature, not a flaw, as it ensures the system only engages when a high-probability setup occurs within a confirmed market uptrend.

### 3. Additional Safety Layers

- **VIX Protection**: While the S&P 500 filter was the primary actor in this scenario, the system also monitors the VIX (Volatility Index). Trading is halted if the VIX exceeds a predefined threshold (set to `45` in this backtest), preventing entries during periods of extreme market fear. The system only reactivates when the VIX drops to 80% of this threshold.

- **Time Stop**: No position is held for more than 10 business days (`TIME_STOP = 10`). This acts as a final safeguard, forcing an exit from a trade that is not performing as expected and preventing prolonged exposure in a single asset.

- **Individual Stock Trend Filter**: In addition to the main S&P 500 filter, each individual stock must also be trading above its own 200-day SMA to be considered for a long entry.

## Conclusion

The backtest demonstrates that the strategy's strength lies in its robust defensive protocols. By prioritizing capital preservation and strictly limiting market exposure during bearish trends, the system successfully navigated one of the worst market crashes in history with minimal capital erosion. The low frequency of operations is a direct and intended consequence of these safety measures, proving that avoiding significant losses is often more important than generating frequent gains, especially in a bear market.
