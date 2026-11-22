# Real total assets (實質總資產)

Add a `real_total` column to `simulate()`'s output: total assets in today's purchasing power.

## Goal (目標)

- `total` is in nominal TWD (名目): a million TWD thirty years from now buys less than a million today, because of inflation (通膨).
- `real_total` shows what the total assets are worth in today's money (real purchasing power, 實質購買力), so results from different years, and from different inflation assumptions, can be compared.
- `Params.inflation` already raises expenses each year; this feature reuses the same rate.

## Interface (介面)
1. Add a new field to pd.DataFrame named `real_total` returned by simulate()
2. Update the real_total at the same timing as expenses raising, which will be detiailed at Properties 3

## Properties (性質)
1. When month = 0, real_total == total
2. If Params.inflation == 0, real_total == total
3. If inflation != 0, real_total = total / (1+inflation) ** t
  - t = month / 12, month starting from 0
  - In sync with the timing of expenses raising

## Open questions (待釐清的問題)

### Raised by agents (agent 提出的問題)

Questions from spec review. Each is for the user to answer in the sections above; delete it once answered.

1. Property 3: in review you chose option A, yearly deflation in sync with expenses (t = 0 at months 11 and 12, t = 1 at month 13), over option B (the price index steps up at month 12). Plug months 6, 11, 12 and 13 into `t = month / 12`: does the result match option A, or is it monthly deflation? Write the choice and its reason in the Interface.
2. Property 3: which Python operator drops the fractional part? With it, does month 12 follow option A or B, and how would you adjust the formula so the step happens at month 13? Then check that month 0 still satisfies Property 1.
3. Interface item 2 points to Property 3, and Property 3 points back to "the timing of expenses raising". Where should the definition (formula) live, so the other section can check it?
4. With option A, a row's `expenses` and `real_total` use the same price index. What do you get if you convert every row's `expenses` the same way? Can that be a property that doesn't restate the formula?
5. Dividing floats rarely gives exact results. How should the tests compare `real_total` with the expected value?
6. Should other money columns (`invested`, `dividends`, `expenses`, ...) also get real versions, now or later?
7. Expenses adjust yearly. Making them adjustable monthly would change `simulate()`'s existing behavior: is that part of this spec or a separate feature?
8. Should Monte Carlo (`specs/monte-carlo.md`) report results in real terms too, and does it depend on this feature?
