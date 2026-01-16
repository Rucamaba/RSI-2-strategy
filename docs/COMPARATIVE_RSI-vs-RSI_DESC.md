# Comparative Analysis of RSI vs. RSI_DESC Trading Strategies

## Abstract

This paper presents a comparative performance analysis of two distinct trading strategies: a standard Relative Strength Index (RSI) strategy and a descending RSI strategy (RSI_DESC). The evaluation is based on a series of backtests conducted over various yearly periods, including downtrend periods such as 2020 (COVID-19 pandemic) and other market conditions from 2018 to 2025. The objective is to determine the relative effectiveness and robustness of each strategy under identical trading parameters.

## 1. Backtest Parameters

All simulations were executed with the following standardized parameters to ensure a consistent and unbiased comparison:

*   **Leverage Factor:** 5  **Leverage carries significant risk; ensure you understand the risks before trading with leverage**
*   **Initial Capital:** $250.0
*   **Maximum Concurrent Positions:** 5

---

## 2. Performance Results by Year

### Year 2025
#### S&P 500: 16,65%

--- Overall Performance Summary ---
| Method   | Final Value | Max Value | Total Return | Annualized Return | Total Trades | Avg Duration (d) | Winrate |
|----------|-------------|-----------|--------------|-------------------|--------------|------------------|---------|
| RSI      | $352.86     | $354.92   | 41.14%       | 41.31%            | 265          | 4.08             | 67.17%  |
| RSI_DESC | $317.12     | $392.70   | 26.85%       | 26.95%            | 277          | 3.99             | 66.06%  |

### Year 2024
#### S&P 500: 23,30%

--- Overall Performance Summary ---
| Method   | Final Value | Max Value   | Total Return | Annualized Return | Total Trades | Avg Duration (d) | Winrate |
|----------|-------------|-------------|--------------|-------------------|--------------|------------------|---------|
| RSI      | $1,035.27   | $2,003.22   | 314.11%      | 314.51%           | 298          | 3.95             | 71.14%  |
| RSI_DESC | $1,030.33   | $1,384.79   | 312.13%      | 312.53%           | 297          | 3.88             | 70.71%  |

### Year 2023
#### S&P 500: 25,86%

--- Overall Performance Summary ---
| Method   | Final Value | Max Value | Total Return | Annualized Return | Total Trades | Avg Duration (d) | Winrate |
|----------|-------------|-----------|--------------|-------------------|--------------|------------------|---------|
| RSI_DESC | $764.10     | $786.80   | 205.64%      | 206.82%           | 261          | 4.11             | 68.97%  |
| RSI      | $601.28     | $623.33   | 140.51%      | 141.24%           | 251          | 4.27             | 66.93%  |

### Year 2022
#### S&P 500: -18,17%

--- Overall Performance Summary ---
| Method   | Final Value | Max Value | Total Return | Annualized Return | Total Trades | Avg Duration (d) | Winrate |
|----------|-------------|-----------|--------------|-------------------|--------------|------------------|---------|
| RSI      | $106.28     | $250.00   | -57.49%      | -57.61%           | 184          | 4.60             | 60.33%  |
| RSI_DESC | $79.23      | $250.00   | -68.31%      | -68.43%           | 180          | 4.47             | 63.33%  |

### Year 2021
#### S&P 500: 28,75%

--- Overall Performance Summary ---
| Method   | Final Value | Max Value   | Total Return | Annualized Return | Total Trades | Avg Duration (d) | Winrate |
|----------|-------------|-------------|--------------|-------------------|--------------|------------------|---------|
| RSI      | $2,680.50   | $3,305.39   | 972.20%      | 980.97%           | 295          | 3.89             | 69.83%  |
| RSI_DESC | $1,097.08   | $1,336.50   | 338.83%      | 341.07%           | 293          | 3.97             | 65.53%  |

### Year 2020 (COVID-19 Crisis) !!! This backtest ends in March due to bankruptcy !!!
#### S&P 500: 18,37% (ALL YEAR)

--- Overall Performance Summary ---
| Method   | Final Value | Max Value | Total Return | Annualized Return | Total Trades | Avg Duration (d) | Winrate |
|----------|-------------|-----------|--------------|-------------------|--------------|------------------|---------|
| RSI      | $-30.10     | $271.25   | -112.04%     | 0.00%             | 48           | 4.83             | 56.25%  |
| RSI_DESC | $-44.70     | $282.62   | -117.88%     | 0.00%             | 45           | 4.98             | 55.56%  |

### Year 2019
#### S&P 500: 31,22%

--- Overall Performance Summary ---
| Method   | Final Value | Max Value   | Total Return | Annualized Return | Total Trades | Avg Duration (d) | Winrate |
|----------|-------------|-------------|--------------|-------------------|--------------|------------------|---------|
| RSI_DESC | $1,139.24   | $1,144.26   | 355.70%      | 358.07%           | 284          | 3.79             | 76.06%  |
| RSI      | $856.44     | $866.95     | 242.58%      | 244.03%           | 277          | 3.82             | 74.01%  |

### Year 2018
#### S&P 500: -4,56%

--- Overall Performance Summary ---
| Method   | Final Value | Max Value | Total Return | Annualized Return | Total Trades | Avg Duration (d) | Winrate |
|----------|-------------|-----------|--------------|-------------------|--------------|------------------|---------|
| RSI      | $127.79     | $616.45   | -48.88%      | -49.00%           | 254          | 4.41             | 61.81%  |
| RSI_DESC | $90.91      | $364.43   | -63.64%      | -63.76%           | 272          | 4.08             | 65.44%  |


##### Method winner

| 2018 | RSI (BEARISH) |
| 2019 | RSI_DESC |
| 2020 | RSI (BANKRUPTCY) |
| 2021 | RSI |
| 2022 | RSI (BEARISH) | 
| 2023 | RSI_DESC |
| 2024 | RSI |
| 2025 | RSI |

---

## 3. Analysis and Conclusion

Based on the backtest results from 2018 to 2025, a comprehensive analysis points to the **standard RSI strategy as the more reliable and robust of the two methods**, albeit within a high-risk framework.

### Key Observations:

1.  **Superior Performance in Bear Markets:** In years where the S&P 500 finished negatively (2018, 2022), both strategies incurred significant losses, far exceeding the market's decline. However, in both instances, the standard **RSI** strategy demonstrated better risk management by losing considerably less than the **RSI_DESC** strategy. This suggests a superior defensive capability during market downturns.

2.  **Exceptional Bull Market Gains:** While both strategies generated returns that vastly outperformed the S&P 500 in bullish years, the standard RSI strategy was responsible for the single most profitable year (2021), with a return of over 972%. Although **RSI_DESC** showed stronger performance in 2019 and 2023, the sheer scale of the RSI's peak performance highlights its potential for explosive growth.

3.  **Volatility and Risk:** The 2020 COVID-19 crisis serves as a critical stress test. Both strategies resulted in bankruptcy by March, underscoring the extreme risk posed by the 5x leverage factor. Their inability to navigate a "black swan" event, while the broader market recovered to post a positive return for the year, indicates that neither strategy is suitable for risk-averse investors without significant parameter adjustments (e.g., lower leverage, stop-loss mechanisms).

### Conclusion:

While neither strategy can be deemed "safe" due to the aggressive leverage used, the **standard RSI strategy** exhibits a more favorable risk-reward profile. Its ability to consistently outperform **RSI_DESC** during negative years provides a crucial edge in capital preservation. Coupled with its proven capacity for immense returns in favorable conditions, it stands out as the more dependable choice. The **RSI_DESC** strategy, while potent, appears to be more volatile and susceptible to larger drawdowns, making it a less reliable option over the long term.

Therefore, for a trader prioritizing a balance between high growth potential and relative downside protection, the standard RSI strategy is the recommended choice based on this comparative analysis.
