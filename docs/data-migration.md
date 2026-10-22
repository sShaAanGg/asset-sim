# 資料遷移指南

本機資料（情境、之後的實際資產紀錄、價格資料）的格式會隨著專案改變。這份指南說明怎麼改格式，又不弄丟、弄壞資料，以及資料變大後該怎麼做。

## 現況

| 資料 | 格式 | 位置 | 版本記在哪 |
|---|---|---|---|
| 情境（`Params`） | 每個情境一個 JSON 檔 | `data/scenarios/`（或 `$ASSETSIM_DATA_DIR/scenarios/`） | 每個檔案的 `"version"` 欄位 |

程式在 `src/assetsim/scenarios.py`：`SCHEMA_VERSION` 是目前版本，`_migrate()` 負責把舊版資料升級。

## 安全原則（不論資料大小）

1. **先備份，再遷移。** 整個資料夾複製一份，例如 `cp -a data/ data.bak-$(date +%Y%m%d)/`。沒有備份就不要跑遷移。
2. **不要原地修改。** 新資料寫到暫存檔或新資料夾，全部成功後再替換（`save_params` 已經是先寫 `.tmp` 再 `replace`）。中途當掉時，舊資料還是完整的。
3. **一次只升一版。** `_migrate` 裡寫成一連串的 `v1 → v2`、`v2 → v3`，不要寫 `v1 → v3` 的捷徑。這樣每一步都小、容易測試，任何舊版本都能一路升上來。
4. **遷移要能重跑（idempotent）。** 已經是新版的資料，再跑一次也不會壞掉。中斷後直接重跑就好。
5. **舊版本的檔案留作測試資料。** 改版時，把一個舊版檔案放進 `tests/fixtures/`，並寫測試確認它能升到最新版，且內容正確。這是保證「以前存的檔案還能讀」的唯一方法。
6. **遷移後要驗證。** 至少比對：筆數一樣、每筆都能成功載入、關鍵欄位的總和或 checksum 一樣。先用 dry-run（只檢查、不寫入）跑一次。
7. **只往前升，不往回降。** 要回到舊版，就用備份還原，不要寫降版的程式。

## 改版步驟（JSON 情境）

以「在 `Params` 加入 `inflation` 欄位」為例：

1. 在 `Params` 加欄位，並給預設值。
2. `SCHEMA_VERSION` 改成 `2`。
3. 在 `_migrate` 加一步：

   ```python
   def _migrate(data: dict) -> dict:
       version = data.get("version")
       if version == 1:
           data = {"version": 2, "params": {**data["params"], "inflation": 0.02}}
           version = 2
       if version != SCHEMA_VERSION:
           raise ValueError(f"不支援的情境檔版本：{version}（目前是 {SCHEMA_VERSION}）")
       return data
   ```

4. 放一個 v1 檔案到 `tests/fixtures/`，寫測試確認它載入後 `inflation == 0.02`。
5. 決定要**延遲遷移**還是**一次全部遷移**（見下一節）。

### 延遲遷移 vs 一次全部遷移

- **延遲遷移（lazy）**：檔案維持舊版，讀取時才在記憶體裡升級；下次儲存時就自然變成新版。這是現在的做法，不需要額外步驟，適合檔案少的情況。缺點是磁碟上會同時有多種版本，所以 `_migrate` 裡的舊步驟不能刪。
- **一次全部遷移（eager）**：寫一個腳本，把每個檔案讀出、升級、用 `save_params` 寫回。適合想刪掉很舊的遷移程式，或是要換儲存格式的時候。

## 資料變大時

### 大概多大會出問題

- 情境 JSON 每個大約 1 KB。就算有幾千個，全部讀一次也不到一秒，**JSON 一個檔一個情境可以撐很久**。
- 真正會變大的是**時間序列**：每月的實際資產紀錄、每日的價格資料、存下來的模擬結果（蒙地卡羅一次就可能有 10 萬條路徑）。這些不要放進 JSON。

| 資料 | 建議格式 | 理由 |
|---|---|---|
| 設定、情境 | JSON | 小、人看得懂、好 diff |
| 會一直增加的紀錄（實際資產、交易） | SQLite | 可以只新增一筆、可以查詢、有交易（transaction） |
| 大量數值（價格、模擬結果） | Parquet | 欄式壓縮、pandas 讀寫很快、可以只讀需要的欄位 |

### 遷移到 SQLite

SQLite 檔案本身沒有「每筆一個版本」，改用整個資料庫的版本號：`PRAGMA user_version`。

```python
import sqlite3

MIGRATIONS = {  # 版本 n → n+1 的 SQL
    0: "CREATE TABLE snapshots (date TEXT, asset TEXT, value REAL, PRIMARY KEY (date, asset))",
    1: "ALTER TABLE snapshots ADD COLUMN currency TEXT NOT NULL DEFAULT 'TWD'",
}

def migrate(conn: sqlite3.Connection) -> None:
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    while version in MIGRATIONS:
        with conn:  # 一個 transaction：成功才 commit，失敗就全部 rollback
            conn.execute(MIGRATIONS[version])
            conn.execute(f"PRAGMA user_version = {version + 1}")
        version += 1
```

重點：

- **每一步都包在 transaction 裡**，失敗時資料庫會停在上一個完整的版本。
- **備份用 `sqlite3 data/app.db ".backup data/app.db.bak"`** 或 Python 的 `conn.backup()`，不要在程式還開著資料庫時直接 `cp`。
- **加欄位用 `ALTER TABLE ... ADD COLUMN`**，很快，不用重寫整個表。改型別、刪欄位、改主鍵這類大改，要「建新表 → `INSERT INTO new SELECT ... FROM old` → 刪舊表 → 改名」，四步放在同一個 transaction 裡。
- **大量寫入要批次處理**：用 `executemany`，並在同一個 transaction 裡寫完，不要每一筆都 commit（差距可以到上百倍）。
- 大表重建完，跑一次 `VACUUM` 把空間還給磁碟。

### 從 JSON 搬到 SQLite（之後如果需要）

1. 備份 `data/`。
2. 寫腳本：讀所有 JSON（經過 `_migrate`，確保都是最新版），寫進新的 `.db` 檔，**整批放在一個 transaction**。
3. 驗證：筆數一樣，每個情境從 DB 讀回來和從 JSON 讀的 `Params` 相等（可以直接寫成測試）。
4. 程式改成讀 DB；舊的 JSON 資料夾改名成 `scenarios.migrated/` 保留一段時間，確定沒問題再刪。

### Parquet 資料

Parquet 檔案寫好就不再修改，所以「遷移」就是重寫一份：

- 讀舊檔 → 轉換 → 寫到新路徑 → 驗證 → 替換。不要覆蓋原檔。
- 資料很大時**分區（partition）**存放，例如每年或每個代號一個檔（`data/prices/ticker=0050.TW/year=2026.parquet`）。遷移時一次處理一個分區，記憶體不會爆，中斷了也只要重跑沒完成的分區。
- 版本記在檔案的 metadata，或資料夾名稱（`prices_v2/`）。
- 下載的價格資料其實可以重新下載，遷移失敗最壞就是重抓；**使用者自己輸入的資料（情境、實際資產紀錄）不能重建，所以要特別小心**。

## 檢查清單

- [ ] 備份了整個資料資料夾
- [ ] 遷移一次只升一版，每一步都有測試，並用舊版的 fixture 檔測過
- [ ] 先 dry-run，再真的寫入
- [ ] 寫入到新位置或包在 transaction 裡，成功才替換
- [ ] 驗證筆數、能不能載入、關鍵數值
- [ ] 舊資料保留一段時間再刪
