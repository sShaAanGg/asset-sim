from dataclasses import asdict

import pytest

from assetsim.cashflow import Asset, Params, effective_return, monthly_rate, simulate
from assetsim.formulas import fv_annuity, fv_lump_sum


def simple(assets: dict[str, Asset] | None = None, **kw) -> Params:
    """不加薪, 沒有年終, 開銷固定, 沒有緊急預備金, 費用和股息都是 0: 回到最基本的複利模型."""
    defaults = dict(assets=assets or {"A": Asset(1.0, price_return=0.07)}, annual_raise=0.0,
                    bonus_months=0.0, inflation=0.0, emergency_months=0.0, rebalance=False)
    return Params(**(defaults | kw))


def final(p: Params, column: str = "total") -> float:
    return simulate(p)[column].iloc[-1]


# --- 基本複利: 和封閉解比較 ---

def test_monthly_rate_compounds_to_annual():
    assert (1 + monthly_rate(0.07)) ** 12 == pytest.approx(1.07)


def test_lump_sum_matches_closed_form():
    p = simple(initial_assets=1_000_000, monthly_salary=0, monthly_expenses=0, years=30)
    assert final(p) == pytest.approx(fv_lump_sum(1_000_000, 0.07, 30))


def test_monthly_surplus_matches_annuity_formula():
    p = simple(initial_assets=0, monthly_salary=50_000, monthly_expenses=40_000, years=20)
    assert final(p) == pytest.approx(fv_annuity(10_000, monthly_rate(0.07), 240))


def test_zero_return_is_just_the_sum_of_surpluses():
    p = simple(assets={"A": Asset(1.0)}, initial_assets=100, monthly_salary=1000,
               monthly_expenses=500, annual_raise=0.05, inflation=0.03, bonus_months=2, years=3)
    df = simulate(p)
    assert df["total"].iloc[-1] == pytest.approx(df["invested"].iloc[-1])
    assert df["gain"].abs().max() == pytest.approx(0, abs=1e-6)


def test_rebalance_irrelevant_when_all_returns_equal_and_no_costs():
    assets = {"A": Asset(0.5, price_return=0.05), "B": Asset(0.5, price_return=0.05)}
    on = final(simple(assets=assets, rebalance=True))
    off = final(simple(assets=assets, rebalance=False))
    assert on == pytest.approx(off)


# --- 收入與開銷 ---

def test_raise_and_inflation_apply_after_month_12():
    df = simulate(simple(monthly_salary=1000, annual_raise=0.1, monthly_expenses=500,
                         inflation=0.04, years=2))
    assert (df.loc[12, "salary"], df.loc[12, "expenses"]) == pytest.approx((1000, 500))
    assert (df.loc[13, "salary"], df.loc[13, "expenses"]) == pytest.approx((1100, 520))


def test_bonus_paid_in_month_12_only():
    df = simulate(simple(monthly_salary=1000, monthly_expenses=0, bonus_months=2, years=1))
    assert df.loc[11, "income"] == pytest.approx(1000)
    assert df.loc[12, "income"] == pytest.approx(3000)


def test_emergency_fund_is_filled_before_investing():
    df = simulate(simple(initial_assets=0, monthly_salary=30_000, monthly_expenses=20_000,
                         emergency_months=3, emergency_rate=0.0, years=1))
    # 目標 60,000: 前 6 個月的結餘全部進緊急預備金
    assert df.loc[6, "emergency"] == pytest.approx(60_000)
    assert df.loc[6, "A"] == pytest.approx(0)
    assert df.loc[7, "emergency"] == pytest.approx(60_000)
    assert df.loc[7, "A"] == pytest.approx(10_000)


def test_deficit_uses_emergency_fund_then_sells_assets():
    a = Asset(1.0, fee_rate=0.001, sell_tax=0.003)
    df = simulate(simple(assets={"A": a}, initial_assets=110_000, monthly_salary=0,
                         monthly_expenses=10_000, emergency_months=1, emergency_rate=0.0, years=1))
    # 起始: 緊急預備金 10,000, 資產 100,000
    assert df.loc[1, "emergency"] == pytest.approx(0)
    assert df.loc[1, "A"] == pytest.approx(100_000)
    # 第 2 個月要賣出 10,000 / (1 - 0.004) 的市值, 才能湊到 10,000
    assert df.loc[2, "A"] == pytest.approx(100_000 - 10_000 / 0.996)
    # 一年開銷 120,000, 能動用的只有 10,000 + 100,000 × 0.996
    assert df["shortfall"].iloc[-1] == pytest.approx(120_000 - 10_000 - 99_600)
    assert df["total"].iloc[-1] == pytest.approx(0, abs=1e-6)


def test_shortfall_when_everything_is_sold():
    df = simulate(simple(initial_assets=5_000, monthly_salary=0, monthly_expenses=10_000,
                         assets={"A": Asset(1.0)}, years=1))
    assert df.loc[1, "total"] == pytest.approx(0)
    assert df.loc[1, "shortfall"] == pytest.approx(5_000)
    assert df["shortfall"].iloc[-1] == pytest.approx(115_000)


# --- 費用, 股息, 稅 ---

def test_expense_ratio_drag():
    p = simple(assets={"A": Asset(1.0, price_return=0.07, expense_ratio=0.005)},
               initial_assets=1_000_000, monthly_salary=0, monthly_expenses=0, years=10)
    assert final(p) == pytest.approx(1_000_000 * (1.07 * 0.995) ** 10)


def test_buy_fee_is_deducted_from_contribution():
    p = simple(assets={"A": Asset(1.0, fee_rate=0.001425)}, initial_assets=0,
               monthly_salary=10_000, monthly_expenses=0, years=1)
    df = simulate(p)
    assert df.loc[1, "A"] == pytest.approx(10_000 / 1.001425)
    assert df.loc[1, "fees"] == pytest.approx(10_000 - 10_000 / 1.001425)


def test_liquidation_value_deducts_fee_and_sell_tax():
    p = simple(assets={"A": Asset(1.0, fee_rate=0.001, sell_tax=0.003)},
               initial_assets=1_000_000, monthly_salary=0, monthly_expenses=0, years=1)
    df = simulate(p)
    assert df["liquidation"].iloc[-1] == pytest.approx(df["total"].iloc[-1] * 0.996)


@pytest.mark.parametrize("k", [1, 2, 4, 12])
def test_reinvested_dividends_match_effective_return(k):
    a = Asset(1.0, price_return=0.04, dividend_yield=0.03, payouts_per_year=k, expense_ratio=0.002)
    p = simple(assets={"A": a}, initial_assets=1_000_000, monthly_salary=0, monthly_expenses=0,
               nhi_rate=0.0, years=5)
    assert final(p) == pytest.approx(1_000_000 * (1 + effective_return(a)) ** 5)


def test_nhi_supplement_only_above_threshold():
    a = Asset(1.0, dividend_yield=0.04, payouts_per_year=1)
    small = simulate(simple(assets={"A": a}, initial_assets=499_000, monthly_salary=0,
                            monthly_expenses=0, years=1))
    big = simulate(simple(assets={"A": a}, initial_assets=500_000, monthly_salary=0,
                          monthly_expenses=0, years=1))
    assert small["taxes"].iloc[-1] == 0  # 股息 19,960 < 20,000
    assert big["taxes"].iloc[-1] == pytest.approx(20_000 * 0.0211)


def test_dividend_tax_and_cash_payout():
    a = Asset(1.0, dividend_yield=0.05, payouts_per_year=1, reinvest_dividends=False)
    p = simple(assets={"A": a, "C": Asset(0.0)}, initial_assets=100_000, monthly_salary=0,
               monthly_expenses=0, dividend_tax_rate=0.1, years=1)
    df = simulate(p)
    assert df["dividends"].iloc[-1] == pytest.approx(5_000)
    assert df["taxes"].iloc[-1] == pytest.approx(500)
    # 不再投入: 稅後股息 4,500 依配置比例買進 (A 佔 100%)
    assert df["A"].iloc[-1] == pytest.approx(104_500)


def test_rebalance_pays_costs():
    assets = {"A": Asset(0.5, price_return=0.2, fee_rate=0.001, sell_tax=0.003),
              "B": Asset(0.5, fee_rate=0.001)}
    df = simulate(simple(assets=assets, initial_assets=1_000_000, monthly_salary=0,
                         monthly_expenses=0, rebalance=True, years=1))
    assert df["fees"].iloc[-1] > 0 and df["taxes"].iloc[-1] > 0
    assert df.loc[12, "A"] == pytest.approx(df.loc[12, "B"], rel=1e-3)
    assert df.loc[12, "total"] < 500_000 * 1.2 + 500_000


# --- 驗證與序列化 ---

def test_from_dict_round_trip():
    p = Params()
    assert Params.from_dict(asdict(p)) == p


@pytest.mark.parametrize("bad", [
    dict(assets={"A": Asset(0.5)}),
    dict(assets={"A": Asset(1.5), "B": Asset(-0.5)}),
    dict(assets={"A": Asset(1.0, payouts_per_year=5)}),
    dict(assets={"A": Asset(1.0, expense_ratio=-0.01)}),
    dict(assets={"total": Asset(1.0)}),
    dict(assets={}),
    dict(monthly_expenses=-1),
    dict(years=0),
])
def test_invalid_params_raise(bad):
    with pytest.raises(ValueError):
        simulate(Params(**bad))


# --- 實質總資產 (real total), 對應 specs/real-total.md 的 P1-P4 ---

INFLATIONS = [0.0, 0.02, 0.05]


def price_index(month, inflation: float):
    """spec 的定義: t = max((month - 1) // 12, 0), 物價指數 = (1 + inflation) ** t."""
    return (1 + inflation) ** ((month - 1) // 12).clip(lower=0)


@pytest.mark.parametrize("inflation", INFLATIONS)
def test_real_total_follows_definition(inflation):
    """P1: real_total = total / (1 + inflation) ** t."""
    df = simulate(Params(inflation=inflation, years=5))
    expected = df["total"] / price_index(df["month"], inflation)
    assert df["real_total"].to_numpy() == pytest.approx(expected.to_numpy())


def test_real_total_example_values():
    """P1 代入數字: 第 12 個月 t = 0, 第 13 個月 t = 1, 第 25 個月 t = 2."""
    df = simulate(Params(inflation=0.02, years=3)).set_index("month")
    for month, t in [(0, 0), (12, 0), (13, 1), (25, 2)]:
        assert df.loc[month, "real_total"] == pytest.approx(df.loc[month, "total"] / 1.02 ** t)
    assert df.loc[13, "real_total"] < df.loc[13, "total"]  # 抓得到偷懶的 real_total = total


def test_real_total_equals_total_without_inflation():
    """P2: inflation == 0 時, 每個月 real_total == total."""
    df = simulate(Params(inflation=0.0))
    assert df["real_total"].to_numpy() == pytest.approx(df["total"].to_numpy())


@pytest.mark.parametrize("inflation", INFLATIONS)
def test_real_total_equals_total_in_first_year(inflation):
    """P3: t == 0 (第 0-12 個月) 時, real_total == total."""
    first_year = simulate(Params(inflation=inflation, years=2)).query("month <= 12")
    assert first_year["real_total"].to_numpy() == pytest.approx(first_year["total"].to_numpy())


@pytest.mark.parametrize("inflation", INFLATIONS)
def test_real_expenses_stay_constant(inflation):
    """P4: 開銷用同一個物價指數換算後, 每列 (第 0 列除外) 都等於起始的 monthly_expenses.

    這條不重述 real_total 的公式, 而是檢查物價指數和 simulate() 調整開銷的時機一致.
    """
    p = Params(inflation=inflation, years=5)
    df = simulate(p).query("month >= 1")
    real_expenses = df["expenses"] / price_index(df["month"], inflation)
    assert real_expenses.to_numpy() == pytest.approx(p.monthly_expenses)
