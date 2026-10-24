# User Guide (使用說明)

How to run the simulator, what each input means, how to read the results, and how to save your settings as plans (方案).

## Starting the app

```bash
uv sync                        # first time only
uv run streamlit run app.py
```

Then open <http://localhost:8501> in your browser (on WSL, the Windows browser works). Stop the app with `Ctrl+C` in the terminal.

## Inputs (輸入)

All inputs are in the sidebar. The results update as soon as you change anything.

### 收入 (income)

| Field | Meaning |
|---|---|
| 起始資產 (TWD) | Starting assets (起始資產). The emergency fund is filled from this first; the rest is held according to the allocation below. |
| 月薪 (TWD) | Monthly salary (月薪). |
| 每年加薪 % | Annual raise (每年加薪). Applied after every 12 months; the first raise takes effect in month 13. |
| 年終獎金 (月) | Year-end bonus (年終獎金), in months of salary, paid in month 12 of each year. |

### 開銷 (expenses)

| Field | Meaning |
|---|---|
| 每月生活開銷 (TWD) | Monthly living expenses (生活開銷). What's left of income after expenses is the surplus (結餘), which is what gets invested. |
| 通膨 % | Inflation (通膨): expenses go up by this much every 12 months. |
| 緊急預備金 (幾個月開銷) | Emergency fund (緊急預備金) target, in months of current expenses. The surplus tops it up before anything is invested. |
| 緊急預備金年利率 % | Interest rate on the emergency fund (e.g. a savings account). |

### 配置比例 (allocation)

| Field | Meaning |
|---|---|
| ETF % / 股票 % | Target weights (配置比例) for ETFs and individual stocks. |
| 現金 % | Cash (現金) is whatever is left: `100 − ETF − 股票`. If ETF + 股票 is over 100%, the app shows an error and stops until you fix it. |
| 每年再平衡 | Annual rebalancing (再平衡): at the end of every 12 months, sell what's overweight and buy what's underweight. Selling pays fees and sell tax. When it's off, holdings drift with returns, but new money is still split by the target weights. |
| 模擬年數 | Number of years to simulate. |

### 各資產 (per asset)

Expand ETF or 股票 to set:

| Field | Meaning |
|---|---|
| 價格報酬 % | Price return (價格報酬): the annual price change **excluding dividends and before the expense ratio**. Published ETF returns usually already include dividends and fees, so entering them here would count those twice. |
| 股息殖利率 % | Dividend yield (股息殖利率), annual. |
| 每年配息次數 | Payouts per year (配息頻率): 1, 2, 3, 4, 6 or 12. |
| 內扣費用 % | Expense ratio (內扣費用), deducted from the value monthly. |
| 股息再投入 | Reinvest dividends (股息再投入) into the same asset. When off, dividends join that month's cash and are split by the target weights. |

Under 現金 you set its annual interest rate. Below the asset settings, "總報酬" shows each asset's equivalent total return (總報酬), i.e. price return plus reinvested dividends minus the expense ratio, ignoring fees and taxes. That's the number to compare with an ETF's published total return.

### 費用與稅 (fees and taxes)

| Field | Meaning |
|---|---|
| 手續費折扣 | Broker fee discount (手續費折扣): multiplies the 0.1425% list fee. 1 = no discount. Paid on both buys and sells. |
| 計入證交稅 | Securities transaction tax (證交稅): 0.1% for ETFs, 0.3% for stocks, paid only when selling (rebalancing, or covering a shortfall). |
| 計入二代健保補充保費 | NHI supplementary premium (二代健保補充保費): 2.11% of any single dividend payment of 20,000 or more. |
| 股利所得有效稅率 % | Effective tax rate on dividend income (股利所得有效稅率). With the 8.5% credit under combined taxation, it's close to 0 for many people. |

## How the simulation works (模擬方式)

Each month, in order:

1. Every asset grows by its monthly price return, minus its monthly expense ratio. The emergency fund earns its interest.
2. In payout months, dividends are paid. NHI premium and dividend tax are deducted, and the rest is reinvested or added to this month's cash.
3. Income (salary, plus the bonus in month 12) minus expenses is the surplus (結餘).
   - **Surplus ≥ 0:** top up the emergency fund first, then buy assets by target weight (paying broker fees). Money is invested at the end of the month (an ordinary annuity (期末年金)).
   - **Surplus < 0:** draw from the emergency fund first, then sell assets in proportion to their value (paying fees and sell tax). If everything has been sold, the unpaid amount is recorded as a shortfall (短缺).
4. Every 12 months: rebalance if it's on, then raise the salary and adjust expenses for inflation.

Returns are fixed and deterministic (固定報酬率) in this stage: there is no randomness yet. All amounts are nominal TWD (名目金額). See [plan.md](../plan.md) for what later stages add.

## Reading the results (結果)

| Item | Meaning |
|---|---|
| N 年後總資產 (市值) | Total market value (市值) at the end: all assets plus the emergency fund. |
| 全部賣出後淨值 | Liquidation value (全部賣出後淨值): what you'd get after selling everything and paying fees and sell tax. |
| 累計投入本金 | Total principal (投入本金): starting assets plus every month's surplus. A negative surplus reduces it. |
| 投資收益 | Investment gain (投資收益) = total market value − principal. The percentage below it is the gain divided by principal, a total return over the whole period, **not** an annualized one. |
| 第一年儲蓄率 | First-year savings rate (儲蓄率): surplus ÷ income over the first 12 months. |
| 累計股息 / 手續費 / 稅 | Cumulative dividends (before tax), broker fees, and taxes (NHI premium, dividend tax, sell tax). |
| Red error "資產在第 N 年用完" | Assets ran out in year N; it also shows the total of expenses that couldn't be paid after that. |
| 總資產 vs 投入本金 | Line chart of total assets and principal at the end of each year. The gap between the lines is the gain. |
| 各資產價值 | Stacked area chart of each asset and the emergency fund at the end of each year. |
| 逐年明細 | Expandable year-by-year table: salary, income, expenses, surplus, each asset, the emergency fund, totals, and cumulative dividends, fees and taxes. |

## Plans (方案)

A plan is a named, saved set of all the inputs above, for example "保守" (conservative) and "積極" (aggressive), so you can switch between them.

The "方案" section is at the bottom of the sidebar.

| Action | How |
|---|---|
| Save (儲存) | Type a name in "方案名稱" and click "儲存目前設定". Saving with an existing name **overwrites** that plan (the message says "覆蓋舊檔"). |
| Load (載入) | Pick a plan in "已存的方案" and click "載入". This list only appears once at least one plan is saved. |
| Set default (設為預設) | Pick a plan and click "設為預設". It's marked with ★, and every new browser session (a new tab or a restart) starts from it. Click "取消預設" to go back to the built-in defaults. |

Notes:

- Changing an input does **not** change the saved plan. Click "儲存目前設定" again to update it.
- Refreshing the page or opening a new tab starts a new session (工作階段): inputs go back to the default plan, or to the built-in values if no default is set. Unsaved changes are lost, so save first.
- Plans saved by an older version of the app are upgraded when loaded. New settings get values that keep the old results unchanged (e.g. no bonus, no fees, no dividends), so check them after loading. The file on disk stays in the old format until you save the plan again.
- Plan names can't contain `/ \ : * ? " < > |` or start with a dot.
- If the default plan can't be loaded (deleted, or a file was edited by hand and is invalid), the app starts from the built-in values and shows an error.

### Where plans are stored (存放位置)

| File | Contents |
|---|---|
| `data/plans/<name>.json` | One plan per file |
| `data/settings.json` | Which plan is the default |

`data/` is not tracked by git, so **plans aren't backed up anywhere.** Copy the folder yourself if you care about them, e.g. `cp -a data/ ~/asset-sim-backup/`. The files are plain JSON and can be read or copied by hand.

To keep data outside the repo (so deleting or re-cloning the repo doesn't delete it), set `ASSETSIM_DATA_DIR`:

```bash
ASSETSIM_DATA_DIR=~/.local/share/asset-sim uv run streamlit run app.py
```

Plans then live in `~/.local/share/asset-sim/plans/`. For how the file format is versioned and upgraded, see [data-migration.md](data-migration.md).

## Troubleshooting (疑難排解)

| Problem | Fix |
|---|---|
| The page doesn't open | Check that the terminal shows `Local URL: http://localhost:8501`. If port 8501 is busy, Streamlit picks another port, so use the URL it prints. |
| "ETF + 股票 = ...%, 不能超過 100%" | Lower ETF % or 股票 % until they add up to 100% or less. |
| "無法載入..." / "找不到方案..." when loading | The plan file is missing or invalid. Check `data/plans/`, or restore it from your backup. |
| "無法讀取設定檔" at startup | `data/settings.json` is invalid. Delete it (you only lose which plan is the default) and set the default again. |
| A loaded plan raises a Streamlit error about a value out of range | The file holds a value outside a slider's range (only possible if it was edited by hand). Fix the value in the JSON file. |
