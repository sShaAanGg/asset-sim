import json

import pytest

from pathlib import Path

from assetsim.cashflow import Asset, Params, simulate
from assetsim.scenarios import (delete_scenario, list_scenarios, load_params, save_params,
                                scenarios_dir)


def test_round_trip_keeps_every_field(tmp_path):
    p = Params(initial_assets=123, assets={"A": Asset(0.25, price_return=0.04),
                                           "B": Asset(0.75, dividend_yield=0.03, payouts_per_year=4,
                                                      reinvest_dividends=False)},
               years=7, rebalance=False)
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
    assert json.loads(path.read_text(encoding="utf-8"))["version"] == 2


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
        save_params(Params(assets={"A": Asset(0.5)}), "x", tmp_path)
    assert list_scenarios(tmp_path) == []


def test_env_var_overrides_data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("ASSETSIM_DATA_DIR", str(tmp_path))
    assert scenarios_dir() == tmp_path / "scenarios"


FIXTURES = Path(__file__).parent / "fixtures" / "scenarios"


def test_v1_file_migrates_to_identical_results():
    """v1 檔案（用 v1 程式存的）升級後，模擬結果要和 v1 程式算的完全一樣。"""
    p = load_params("v1_example", FIXTURES)
    assert p.monthly_expenses == pytest.approx(55_000 * 0.65)
    assert p.assets["ETF"] == Asset(0.7, price_return=0.07)
    df = simulate(p)
    # 以下數字是 v1 程式（commit 3e41ae3）的輸出
    expected = {1: (521991.16012292285, 519250.0), 12: (772106.2893109211, 731000.0),
                13: (796070.4732527551, 750731.25), 120: (4567978.198400693, 3087981.188374346),
                300: (21004066.01780411, 8390443.468496734)}
    for m, (total, invested) in expected.items():
        assert df.loc[m, "total"] == pytest.approx(total, rel=1e-12)
        assert df.loc[m, "invested"] == pytest.approx(invested, rel=1e-12)
    assert df.loc[13, "ETF"] == pytest.approx(557342.1983676505, rel=1e-12)


def test_loading_v1_does_not_rewrite_the_file():
    before = (FIXTURES / "v1_example.json").read_bytes()
    load_params("v1_example", FIXTURES)
    assert (FIXTURES / "v1_example.json").read_bytes() == before


def test_migrated_scenario_saves_as_v2(tmp_path):
    path = save_params(load_params("v1_example", FIXTURES), "migrated", tmp_path)
    assert json.loads(path.read_text(encoding="utf-8"))["version"] == 2
    assert load_params("migrated", tmp_path) == load_params("v1_example", FIXTURES)
