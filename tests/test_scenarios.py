import json

import pytest

from assetsim.cashflow import Params
from assetsim.scenarios import (delete_scenario, list_scenarios, load_params, save_params,
                                scenarios_dir)


def test_round_trip_keeps_every_field(tmp_path):
    p = Params(initial_assets=123, allocation={"A": 0.25, "B": 0.75},
               annual_returns={"A": 0.04, "B": 0.08}, years=7, rebalance=False)
    save_params(p, "測試", tmp_path)
    assert load_params("測試", tmp_path) == p


def test_list_and_delete(tmp_path):
    assert list_scenarios(tmp_path / "missing") == []
    save_params(Params(), "b", tmp_path)
    save_params(Params(), "a", tmp_path)
    assert list_scenarios(tmp_path) == ["a", "b"]
    delete_scenario("a", tmp_path)
    assert list_scenarios(tmp_path) == ["b"]


def test_file_has_schema_version(tmp_path):
    path = save_params(Params(), "x", tmp_path)
    assert json.loads(path.read_text(encoding="utf-8"))["version"] == 1


def test_unknown_version_is_rejected(tmp_path):
    (tmp_path / "old.json").write_text(json.dumps({"version": 99, "params": {}}))
    with pytest.raises(ValueError, match="版本"):
        load_params("old", tmp_path)


@pytest.mark.parametrize("bad", ["", "  ", "../escape", "a/b", ".hidden"])
def test_bad_names_are_rejected(tmp_path, bad):
    with pytest.raises(ValueError):
        save_params(Params(), bad, tmp_path)


def test_invalid_params_are_not_saved(tmp_path):
    with pytest.raises(ValueError):
        save_params(Params(allocation={"A": 0.5}, annual_returns={"A": 0.1}), "x", tmp_path)
    assert list_scenarios(tmp_path) == []


def test_env_var_overrides_data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("ASSETSIM_DATA_DIR", str(tmp_path))
    assert scenarios_dir() == tmp_path / "scenarios"
