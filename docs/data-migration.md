# Data Migration Guide（資料遷移指南）

The format of local data (plans（方案）, and later real balance history and price data) will change as the project grows. This guide explains how to change a format without losing or corrupting data, and what to do once the data gets big.

## Current state

| Data | Format | Location | Where the version lives |
|---|---|---|---|
| Plans (`Params`) | One JSON file per plan | `data/plans/` (or `$ASSETSIM_DATA_DIR/plans/`) | The `"version"` field in each file |
| Settings (default plan) | One JSON file | `data/settings.json` | Its own `"version"` field (`SETTINGS_VERSION`) |

The code is in `src/assetsim/plans.py`: `SCHEMA_VERSION` is the current plan format version, and `_migrate()` upgrades older plan files. The settings file is versioned separately, so the two formats can change independently.

## Safety rules（安全原則）

1. **Back up first, then migrate（先備份，再遷移）.** Copy the whole folder, e.g. `cp -a data/ data.bak-$(date +%Y%m%d)/`. Never run a migration without a backup.
2. **Never modify in place（不要原地修改）.** Write new data to a temp file or a new folder, and swap it in only after everything succeeds (`save_plan` already writes a `.tmp` file and then calls `replace`). If something crashes halfway, the old data is still intact.
3. **Upgrade one version at a time（一次只升一版）.** Write `_migrate` as a chain of `v1 → v2`, `v2 → v3` steps, never a `v1 → v3` shortcut. Each step stays small and easy to test, and any old version can be upgraded all the way to the latest.
4. **Make migrations idempotent（可重跑、冪等）.** Running a migration again on data that is already up to date must not break it. If a run is interrupted, just run it again.
5. **Keep old-version files as test data（測試資料，fixture）.** On every format change, put a file in the old format into `tests/fixtures/` and write a test that upgrades it to the latest version and checks the content. This is the only way to guarantee that files saved earlier can still be read.
6. **Verify after migrating（遷移後驗證）.** At minimum, check that the record count is unchanged, every record loads, and the sums or checksums of key fields match. Do a dry-run（試跑） (check only, no writes) first.
7. **Only upgrade, never downgrade（只升版，不降版）.** To go back to an old version, restore the backup instead of writing downgrade code.

## Steps for a format change（改版步驟，JSON 方案）

Example: adding an `inflation` field to `Params`.

1. Add the field to `Params` with a default value.
2. Change `SCHEMA_VERSION` to `2`.
3. Add a step to `_migrate`:

   ```python
   def _migrate(data: dict) -> dict:
       version = data.get("version")
       if version == 1:
           data = {"version": 2, "params": {**data["params"], "inflation": 0.02}}
           version = 2
       if version != SCHEMA_VERSION:
           raise ValueError(f"不支援的方案檔版本：{version}（目前是 {SCHEMA_VERSION}）")
       return data
   ```

4. Put a v1 file in `tests/fixtures/` and write a test checking that it loads with `inflation == 0.02`.
5. Decide between **lazy migration** and **migrating everything at once** (see the next section).

### Lazy vs eager migration（延遲遷移 vs 一次全部遷移）

- **Lazy:** files stay in the old version and are upgraded in memory when read; the next save writes them in the new version. This is the current approach. It needs no extra steps and suits a small number of files. The downside is that several versions coexist on disk, so old steps in `_migrate` can never be removed.
- **Eager:** a script reads every file, upgrades it, and writes it back with `save_plan`. Use this when you want to delete very old migration code, or when switching to a different storage format.

## When the data gets big（資料變大時）

### Roughly when it becomes a problem

- Each plan JSON is about 1 KB. Even with thousands of them, reading them all takes under a second, so **one JSON file per plan will last a long time**.
- What actually grows is **time-series data（時間序列）**: monthly real balance records, daily prices, and saved simulation results (a single Monte Carlo run can have 100,000 paths). Don't put these in JSON.

| Data | Recommended format | Why |
|---|---|---|
| Settings, plans | JSON | Small, human-readable, easy to diff |
| Records that keep growing (real balances, transactions) | SQLite | Append one row at a time, query it, transactions |
| Large numeric data (prices, simulation results) | Parquet | Columnar（欄式） compression, fast pandas reads and writes, read only the columns you need |

### Migrating SQLite

A SQLite file has no per-record version, so use a version number for the whole database: `PRAGMA user_version`.

```python
import sqlite3

MIGRATIONS = {  # SQL that upgrades version n to n+1
    0: "CREATE TABLE snapshots (date TEXT, asset TEXT, value REAL, PRIMARY KEY (date, asset))",
    1: "ALTER TABLE snapshots ADD COLUMN currency TEXT NOT NULL DEFAULT 'TWD'",
}

def migrate(conn: sqlite3.Connection) -> None:
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    while version in MIGRATIONS:
        with conn:  # one transaction: commit on success, roll everything back on failure
            conn.execute(MIGRATIONS[version])
            conn.execute(f"PRAGMA user_version = {version + 1}")
        version += 1
```

Key points:

- **Wrap every step in a transaction（交易）**, so a failure leaves the database at the previous complete version.
- **Back up with `sqlite3 data/app.db ".backup data/app.db.bak"`** or Python's `conn.backup()`. Don't `cp` the file while a program has the database open.
- **Add columns with `ALTER TABLE ... ADD COLUMN`.** It's fast and doesn't rewrite the table. Bigger changes, such as changing a type, dropping a column, or changing the primary key, need "create new table → `INSERT INTO new SELECT ... FROM old` → drop old table → rename", with all four steps in the same transaction.
- **Batch large writes（批次寫入）:** use `executemany` and write everything in one transaction instead of committing after each row (the difference can be 100x or more).
- After rebuilding a large table, run `VACUUM` to give the space back to the disk.

### Moving from JSON to SQLite (if needed later)

1. Back up `data/`.
2. Write a script that reads every JSON file (through `_migrate`, so they're all at the latest version) and writes them into a new `.db` file, **all in one transaction**.
3. Verify: the counts match, and every plan read back from the DB equals the `Params` read from JSON (this can be a test).
4. Switch the code to read from the DB. Rename the old JSON folder to `plans.migrated/` and keep it for a while; delete it once you're sure everything works.

### Parquet data

Parquet files aren't modified after they're written, so "migrating" means writing a new copy:

- Read the old file → transform → write to a new path → verify → swap. Don't overwrite the original.
- For large data, **partition（分區）** it, e.g. one file per year or per ticker (`data/prices/ticker=0050.TW/year=2026.parquet`). Migrate one partition at a time so memory stays bounded, and after an interruption only the unfinished partitions need rerunning.
- Record the version in the file metadata or in the folder name (`prices_v2/`).
- Downloaded price data can be downloaded again, so the worst case for a failed migration is re-fetching it. **Data you entered yourself (plans, real balance records) can't be rebuilt, so be especially careful with it.**

## Checklist（檢查清單）

- [ ] Backed up the whole data folder
- [ ] Each migration step upgrades one version, has a test, and was tested against an old-version fixture file
- [ ] Ran a dry-run before writing for real
- [ ] Writes go to a new location or happen inside a transaction, swapped in only on success
- [ ] Verified counts, that every record loads, and key values
- [ ] Kept the old data for a while before deleting it
