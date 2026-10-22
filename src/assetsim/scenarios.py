"""把 Params 存成具名情境（JSON 檔），之後可以再載入。

檔案格式：
    {"version": 1, "params": {...Params 的欄位...}}

version 是格式版本：之後 Params 欄位改變時，遞增 SCHEMA_VERSION，
並在 _migrate 裡把舊版資料轉成新版，舊檔案就還能讀。

存放位置：預設是專案的 data/scenarios/（不進 git），
可以用環境變數 ASSETSIM_DATA_DIR 改到別的資料夾。
"""

import json
import os
from dataclasses import asdict
from pathlib import Path

from assetsim.cashflow import Params

SCHEMA_VERSION = 1
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def scenarios_dir() -> Path:
    base = os.environ.get("ASSETSIM_DATA_DIR")
    return (Path(base) if base else _PROJECT_ROOT / "data") / "scenarios"


def _path(name: str, directory: Path | None) -> Path:
    name = name.strip()
    if not name or name.startswith(".") or any(c in name for c in '/\\:*?"<>|'):
        raise ValueError(f"情境名稱不合法：{name!r}")
    return (directory or scenarios_dir()) / f"{name}.json"


def list_scenarios(directory: Path | None = None) -> list[str]:
    d = directory or scenarios_dir()
    return sorted(f.stem for f in d.glob("*.json")) if d.exists() else []


def save_params(p: Params, name: str, directory: Path | None = None) -> Path:
    p.validate()
    path = _path(name, directory)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"version": SCHEMA_VERSION, "params": asdict(p)}
    # 先寫暫存檔再改名，寫到一半當掉也不會留下壞掉的檔案
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)
    return path


def load_params(name: str, directory: Path | None = None) -> Params:
    data = json.loads(_path(name, directory).read_text(encoding="utf-8"))
    p = Params(**_migrate(data)["params"])
    p.validate()
    return p


def delete_scenario(name: str, directory: Path | None = None) -> None:
    _path(name, directory).unlink()


def _migrate(data: dict) -> dict:
    """把舊版格式逐版升級到 SCHEMA_VERSION。目前只有第 1 版。"""
    version = data.get("version")
    if version != SCHEMA_VERSION:
        raise ValueError(f"不支援的情境檔版本：{version}（目前是 {SCHEMA_VERSION}）")
    return data
