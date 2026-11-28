# Monte Carlo simulation (蒙地卡羅模擬)

Run the cash-flow simulation many times with random returns, to show the range of outcomes instead of a single path.

## Goal (目標)

- `simulate()` assumes the same return every month, so it gives one answer, as if the future were certain. Real returns go up and down from year to year (volatility, 波動度).
- This feature shows how uncertain the outcome is: the spread of the final total assets (for example the P10 / P50 / P90 percentiles, 百分位數), and the probability (機率) of reaching a target amount.
- It lets me revisit phase 0 exercise 5: what rebalancing (再平衡) does once returns are volatile.
- Later phases build on it: correlated assets (phase 2) and parameters estimated from historical data (phase 3).

## Interface (介面)

## Properties (性質)

## Open questions (待釐清的問題)
