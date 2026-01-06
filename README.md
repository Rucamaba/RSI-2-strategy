## Strategy Overview: RSI(2) Mean Reversion

This project implements a mean-reversion trading strategy popularized by **Larry Connors**. The strategy aims to identify short-term pullbacks within a long-term uptrend to capture quick "bounce-back" profits.

### 1. Market Filters & Indicators

- **Long-term Trend (Filter)**: The price must be above its **200-day Simple Moving Average (SMA)**. This ensures we only trade in a bullish market environment.

- **Short-term Momentum (Trigger)**: We use a **2-period Relative Strength Index (RSI)** to find extreme oversold conditions.

- **Exit Target**: The **5-day Simple Moving Average (SMA)** acts as the price target for taking profits.

### 2. Trading Rules

| Action          | Condition                               |
| :-------------- | :-------------------------------------- |
| **Buy Signal**  | Price > 200-day SMA **AND** RSI(2) < 10 |
| **Exit Signal** | Price > 5-day SMA                       |

### 3. Why it Works

The RSI(2) strategy exploits the "rubber band effect." When a strong stock drops sharply in the short term (RSI < 10), it often snaps back to its mean. By exiting at the 5-day SMA, the strategy captures the meat of that snap-back move without overstaying the welcome.

## Example Output

When you run the script, it will display the technical indicators and the trading signal as follows:

```text
Fetching data for VOO...
----------------------------------------
Date: 2026-01-05
Ticker: VOO
Current Price: 633.30
200 SMA (Trend): 574.38
RSI(2) Value: 80.20
5 SMA (Exit Target): 630.61
----------------------------------------
RESULT: [EXIT] Above 5 SMA. Good time to take profit.
```
