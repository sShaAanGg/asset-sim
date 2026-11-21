import json
from pathlib import Path

import pytest

from assetsim.cashflow import Asset, Params, simulate
from assetsim.plans import (data_dir, delete_plan, get_default_plan, list_plans, load_plan,
                            save_plan, set_default_plan)


def test_round_trip_keeps_every_field(tmp_path):
    p = Params(initial_assets=123, assets={"A": Asset(0.25, price_return=0.04),
                                           "B": Asset(0.75, dividend_yield=0.03, payouts_per_year=4,
                                                      reinvest_dividends=False)},
               years=7, rebalance=False)
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
    assert json.loads(path.read_text(encoding="utf-8"))["version"] == 2


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
        save_plan(Params(assets={"A": Asset(0.5)}), "x", tmp_path)
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


FIXTURES = Path(__file__).parent / "fixtures"  # 方案檔在 fixtures/plans/


def test_v1_file_migrates_to_identical_results():
    """v1 檔案 (用 v1 程式存的) 升級後, 模擬結果要和 v1 程式算的完全一樣."""
    p = load_plan("v1_example", FIXTURES)
    assert p.monthly_expenses == pytest.approx(55_000 * 0.65)
    assert p.assets["ETF"] == Asset(0.7, price_return=0.07)
    df = simulate(p)
    # 以下數字是 v1 程式 (commit 3e41ae3) 的輸出
    expected = {1: (521991.16012292285, 519250.0), 12: (772106.2893109211, 731000.0),
                13: (796070.4732527551, 750731.25), 120: (4567978.198400693, 3087981.188374346),
                300: (21004066.01780411, 8390443.468496734)}
    for m, (total, invested) in expected.items():
        assert df.loc[m, "total"] == pytest.approx(total, rel=1e-12)
        assert df.loc[m, "invested"] == pytest.approx(invested, rel=1e-12)
    assert df.loc[13, "ETF"] == pytest.approx(557342.1983676505, rel=1e-12)


def test_loading_v1_does_not_rewrite_the_file():
    before = (FIXTURES / "plans" / "v1_example.json").read_bytes()
    load_plan("v1_example", FIXTURES)
    assert (FIXTURES / "plans" / "v1_example.json").read_bytes() == before


def test_migrated_plan_saves_as_v2(tmp_path):
    path = save_plan(load_plan("v1_example", FIXTURES), "migrated", tmp_path)
    assert json.loads(path.read_text(encoding="utf-8"))["version"] == 2
    assert load_plan("migrated", tmp_path) == load_plan("v1_example", FIXTURES)
