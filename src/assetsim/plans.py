"""把 Params 存成具名方案 (plan, JSON 檔), 之後可以再載入; 也可以指定一個預設方案.

方案檔格式:
    {"version": 1, "params": {...Params 的欄位...}}

設定檔格式 (data/settings.json):
    {"version": 1, "default_plan": "保守"}  # 沒有預設方案時是 null

version 是格式版本 (schema version): 之後欄位改變時, 遞增 SCHEMA_VERSION,
並在 _migrate 裡把舊版資料轉成新版, 舊檔案就還能讀. 詳見 docs/data-migration.md.

存放位置: 預設是專案的 data/(不進 git), 方案放在 data/plans/;
可以用環境變數 ASSETSIM_DATA_DIR 改到別的資料夾.
"""

import json
import os
from dataclasses import asdict
from pathlib import Path

from assetsim.cashflow import Params

SCHEMA_VERSION = 2
SETTINGS_VERSION = 1
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def data_dir() -> Path:
    base = os.environ.get("ASSETSIM_DATA_DIR")
    return Path(base) if base else _PROJECT_ROOT / "data"


def _check_name(name: str) -> str:
    name = name.strip()
    if not name or name.startswith(".") or any(c in name for c in '/\\:*?"<>|'):
        raise ValueError(f"方案名稱不合法: {name!r}")
    return name


def _path(name: str, root: Path | None) -> Path:
    return (root or data_dir()) / "plans" / f"{_check_name(name)}.json"


def _write_json(path: Path, data: dict) -> None:
    # 先寫暫存檔再改名 (atomic write), 寫到一半當掉也不會留下壞掉的檔案
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def list_plans(root: Path | None = None) -> list[str]:
    d = (root or data_dir()) / "plans"
    return sorted(f.stem for f in d.glob("*.json")) if d.exists() else []


def save_plan(p: Params, name: str, root: Path | None = None) -> Path:
    p.validate()
    path = _path(name, root)
    _write_json(path, {"version": SCHEMA_VERSION, "params": asdict(p)})
    return path


def load_plan(name: str, root: Path | None = None) -> Params:
    data = json.loads(_path(name, root).read_text(encoding="utf-8"))
    p = Params.from_dict(_migrate(data)["params"])
    p.validate()
    return p


def delete_plan(name: str, root: Path | None = None) -> None:
    _path(name, root).unlink()
    if get_default_plan(root) == name.strip():
        set_default_plan(None, root)


def get_default_plan(root: Path | None = None) -> str | None:
    """回傳預設方案的名稱; 沒有設定, 或設定檔讀不懂時回傳 None."""
    path = (root or data_dir()) / "settings.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != SETTINGS_VERSION:
        raise ValueError(f"不支援的設定檔版本: {data.get('version')}(目前是 {SETTINGS_VERSION})")
    return data.get("default_plan")


def set_default_plan(name: str | None, root: Path | None = None) -> None:
    """指定預設方案; 傳 None 表示取消. 方案必須已經存在."""
    if name is not None:
        if not _path(name, root).exists():
            raise ValueError(f"找不到方案: {name}")
        name = _check_name(name)
    _write_json((root or data_dir()) / "settings.json",
                {"version": SETTINGS_VERSION, "default_plan": name})


def _v1_to_v2(params: dict) -> dict:
    """v1: 每月投入 = 薪水 × savings_rate, 報酬率不分股息與費用.
    v2: 結餘 = 薪水 − 開銷, 每種資產各自設定股息, 費用, 稅.

    把開銷設成 薪水 × (1 − savings_rate), 並讓開銷和薪水以相同幅度成長,
    每月投入金額就和 v1 完全相同; 其他新項目 (年終, 緊急預備金, 費用, 股息) 都設為 0.
    """
    old = {k: v for k, v in params.items() if k not in ("savings_rate", "allocation", "annual_returns")}
    return {
        **old,
        "monthly_expenses": params["monthly_salary"] * (1 - params["savings_rate"]),
        "inflation": params["annual_raise"],
        "bonus_months": 0.0,
        "emergency_months": 0.0,
        "assets": {n: {"weight": w, "price_return": params["annual_returns"][n]}
                   for n, w in params["allocation"].items()},
    }


def _migrate(data: dict) -> dict:
    """把舊版格式逐版升級到 SCHEMA_VERSION, 一次升一版 (見 docs/data-migration.md)."""
    version = data.get("version")
    if version == 1:
        data = {"version": 2, "params": _v1_to_v2(data["params"])}
        version = 2
    if version != SCHEMA_VERSION:
        raise ValueError(f"不支援的方案檔版本: {version}(目前是 {SCHEMA_VERSION})")
    return data
