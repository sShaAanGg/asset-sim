# Real total assets (實質總資產)

Add a `real_total` column to `simulate()`'s output: total assets in today's purchasing power.

## Goal (目標)

- `total` is in nominal TWD (名目): a million TWD thirty years from now buys less than a million today, because of inflation (通膨).
- `real_total` shows what the total assets are worth in today's money (real purchasing power, 實質購買力), so results from different years, and from different inflation assumptions, can be compared.
- `Params.inflation` already raises expenses each year; this feature reuses the same rate.

## Interface (介面)
1. Add a new field to pd.DataFrame named `real_total` returned by simulate()
2. Update the real_total at the same timing as expenses raising

## Properties (性質)
1. When t <= 0, real_total == total
2. If Params.inflation == 0, real_total == total
3. If inflation != 0, real_total = total / (1+inflation) ** t
  - t = (month - 1) // 12, month starting from 0
  - In sync with the timing of expenses raising
4. Every row's expenses / (1+inflation) ** t should be equal to the original monthly_expenses

## Open questions (待釐清的問題)

### Raised by agents (agent 提出的問題)

Questions from spec review. Each is for the user to answer in the sections above; delete it once answered.

1. ~~Dividing floats rarely gives exact results. How should the tests compare `real_total` with the expected value?~~ Deferred: implementation detail, not a spec concern.
2. ~~Should other money columns (`invested`, `dividends`, `expenses`, ...) also get real versions, now or later?~~ Deferred: separate feature if needed.
3. ~~Expenses adjust yearly. Making them adjustable monthly would change `simulate()`'s existing behavior: is that part of this spec or a separate feature?~~ Deferred: separate feature.
4. ~~Should Monte Carlo (`specs/monte-carlo.md`) report results in real terms too, and does it depend on this feature?~~ Deferred: Monte Carlo spec will decide whether to use `real_total`.
