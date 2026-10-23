# User Guide（使用說明）

How to run the simulator, what each input means, how to read the results, and how to save your settings as plans（方案）.

## Starting the app

```bash
uv sync                        # first time only
uv run streamlit run app.py
```

Then open <http://localhost:8501> in your browser (on WSL, the Windows browser works). Stop the app with `Ctrl+C` in the terminal.

## Inputs（輸入）

All inputs are in the sidebar. The results update as soon as you change anything.

### 收入與投入 (income and contributions)

| Field | Meaning |
|---|---|
| 起始資產 (TWD) | Starting assets（起始資產）. Split across assets by the allocation below on day one. |
| 月薪 (TWD) | Monthly salary（月薪）. |
| 每年加薪 % | Annual raise（每年加薪）. Applied every 12 months; the first raise takes effect in month 13. |
| 薪水投入比例 % | Savings rate（投入比例）: the share of each month's salary that gets invested. |
| 模擬年數 | Number of years to simulate. |

### 配置比例 (allocation)

| Field | Meaning |
|---|---|
| ETF % / 股票 % | Target weights（配置比例） for ETFs and individual stocks. |
| 現金 % | Cash（現金） is whatever is left: `100 − ETF − 股票`. If ETF + 股票 is over 100%, the app shows an error and stops until you fix it. |
| 每年再平衡 | Annual rebalancing（再平衡）: at the end of every 12 months, reset holdings to the target weights. When it's off, holdings drift with returns, but new contributions are still split by the target weights. |

### 預期年化報酬率 % (expected annualized returns)

The expected annualized return（年化報酬率） for each asset (ETF, 股票, 現金). It's converted to an equivalent monthly rate, `(1 + r)^(1/12) − 1`, so that compounding for 12 months gives exactly `r`.

## How the simulation works（模擬方式）

Each month, in order:

1. Every asset grows by its monthly rate.
2. `salary × savings rate` is invested at the end of the month (an ordinary annuity（期末年金）), split by the target weights.
3. Every 12 months: the salary goes up by the annual raise, and if rebalancing is on, holdings are reset to the target weights.

Returns are fixed and deterministic（固定報酬率） in this stage: there is no randomness, inflation, tax or fees yet. All amounts are nominal TWD（名目金額）. See [plan.md](../plan.md) for what later stages add.

## Reading the results（結果）

| Item | Meaning |
|---|---|
| N 年後總資產 | Total assets at the end of the last month. |
| 累計投入本金 | Total principal invested（投入本金）: starting assets plus every monthly contribution. |
| 投資收益 | Investment gain（投資收益） = total assets − principal. The percentage below it is the gain divided by principal, a total return over the whole period, **not** an annualized one. |
| 總資產 vs 投入本金 | Line chart of total assets and principal at the end of each year. The gap between the lines is the gain. |
| 各資產價值 | Stacked area chart of each asset's value at the end of each year. |
| 逐年明細 | Expandable year-by-year table: salary, monthly contribution, each asset, total, principal and gain. |

## Plans（方案）

A plan is a named, saved set of all the inputs above, for example 「保守」 (conservative) and 「積極」 (aggressive), so you can switch between them.

The 「方案」 section is at the bottom of the sidebar.

| Action | How |
|---|---|
| Save（儲存） | Type a name in 「方案名稱」 and click 「儲存目前設定」. Saving with an existing name **overwrites** that plan (the message says 「覆蓋舊檔」). |
| Load（載入） | Pick a plan in 「已存的方案」 and click 「載入」. This list only appears once at least one plan is saved. |
| Set default（設為預設） | Pick a plan and click 「設為預設」. It's marked with ★, and every new browser session (a new tab or a restart) starts from it. Click 「取消預設」 to go back to the built-in defaults. |

Notes:

- Changing an input does **not** change the saved plan. Click 「儲存目前設定」 again to update it.
- Refreshing the page or opening a new tab starts a new session（工作階段）: inputs go back to the default plan, or to the built-in values if no default is set. Unsaved changes are lost, so save first.
- Plan names can't contain `/ \ : * ? " < > |` or start with a dot.
- If the default plan can't be loaded (deleted, or a file was edited by hand and is invalid), the app starts from the built-in values and shows an error.

### Where plans are stored（存放位置）

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

## Troubleshooting（疑難排解）

| Problem | Fix |
|---|---|
| The page doesn't open | Check that the terminal shows `Local URL: http://localhost:8501`. If port 8501 is busy, Streamlit picks another port, so use the URL it prints. |
| 「ETF + 股票 = …%，不能超過 100%」 | Lower ETF % or 股票 % until they add up to 100% or less. |
| 「無法載入…」 / 「找不到方案…」 when loading | The plan file is missing or invalid. Check `data/plans/`, or restore it from your backup. |
| 「無法讀取設定檔」 at startup | `data/settings.json` is invalid. Delete it (you only lose which plan is the default) and set the default again. |
| A loaded plan raises a Streamlit error about a value out of range | The file holds a value outside a slider's range (only possible if it was edited by hand). Fix the value in the JSON file. |
