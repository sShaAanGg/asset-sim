import json

import pytest

from assetsim.cashflow import Params
from assetsim.plans import (data_dir, delete_plan, get_default_plan, list_plans, load_plan,
                            save_plan, set_default_plan)


def test_round_trip_keeps_every_field(tmp_path):
    p = Params(initial_assets=123, allocation={"A": 0.25, "B": 0.75},
               annual_returns={"A": 0.04, "B": 0.08}, years=7, rebalance=False)
    save_plan(p, "測試", tmp_path)
    assert load_plan("測試", tmp_path) == p


def test_plans_are_stored_under_plans_dir(tmp_path):
    assert save_plan(Params(), "x", tmp_path) == tmp_path / "plans" / "x.json"


def test_list_and_delete(tmp_path):
    assert list_plans(tmp_path / "missing") == []
    save_plan(Params(), "b", tmp_path)
    save_plan(Params(), "a", tmp_path)
    assert list_plans(tmp_path) == ["a", "b"]
    delete_plan("a", tmp_path)
    assert list_plans(tmp_path) == ["b"]


def test_file_has_schema_version(tmp_path):
    path = save_plan(Params(), "x", tmp_path)
    assert json.loads(path.read_text(encoding="utf-8"))["version"] == 1


def test_unknown_version_is_rejected(tmp_path):
    (tmp_path / "plans").mkdir()
    (tmp_path / "plans" / "old.json").write_text(json.dumps({"version": 99, "params": {}}))
    with pytest.raises(ValueError, match="版本"):
        load_plan("old", tmp_path)


@pytest.mark.parametrize("bad", ["", "  ", "../escape", "a/b", ".hidden"])
def test_bad_names_are_rejected(tmp_path, bad):
    with pytest.raises(ValueError):
        save_plan(Params(), bad, tmp_path)


def test_invalid_params_are_not_saved(tmp_path):
    with pytest.raises(ValueError):
        save_plan(Params(allocation={"A": 0.5}, annual_returns={"A": 0.1}), "x", tmp_path)
    assert list_plans(tmp_path) == []


def test_env_var_overrides_data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("ASSETSIM_DATA_DIR", str(tmp_path))
    assert data_dir() == tmp_path


def test_default_plan_round_trip(tmp_path):
    assert get_default_plan(tmp_path) is None
    save_plan(Params(), "保守", tmp_path)
    set_default_plan("保守", tmp_path)
    assert get_default_plan(tmp_path) == "保守"
    set_default_plan(None, tmp_path)
    assert get_default_plan(tmp_path) is None


def test_default_must_exist(tmp_path):
    with pytest.raises(ValueError):
        set_default_plan("沒有這個", tmp_path)


def test_deleting_default_clears_it(tmp_path):
    save_plan(Params(), "a", tmp_path)
    save_plan(Params(), "b", tmp_path)
    set_default_plan("a", tmp_path)
    delete_plan("b", tmp_path)
    assert get_default_plan(tmp_path) == "a"
    delete_plan("a", tmp_path)
    assert get_default_plan(tmp_path) is None


def test_settings_file_has_version(tmp_path):
    save_plan(Params(), "a", tmp_path)
    set_default_plan("a", tmp_path)
    data = json.loads((tmp_path / "settings.json").read_text(encoding="utf-8"))
    assert data == {"version": 1, "default_plan": "a"}
