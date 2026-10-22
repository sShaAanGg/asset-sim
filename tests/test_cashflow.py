import pytest

from assetsim.cashflow import Params, monthly_rate, simulate
from assetsim.formulas import fv_annuity, fv_lump_sum


def single_asset(**kw) -> Params:
    defaults = dict(allocation={"A": 1.0}, annual_returns={"A": 0.07},
                    annual_raise=0.0, rebalance=False)
    return Params(**(defaults | kw))


def test_monthly_rate_compounds_to_annual():
    assert (1 + monthly_rate(0.07)) ** 12 == pytest.approx(1.07)


def test_lump_sum_matches_closed_form():
    p = single_asset(initial_assets=1_000_000, savings_rate=0.0, years=30)
    assert simulate(p)["total"].iloc[-1] == pytest.approx(fv_lump_sum(1_000_000, 0.07, 30))


def test_monthly_contribution_matches_annuity_formula():
    p = single_asset(initial_assets=0, monthly_salary=50_000, savings_rate=0.2, years=20)
    expected = fv_annuity(10_000, monthly_rate(0.07), 240)
    assert simulate(p)["total"].iloc[-1] == pytest.approx(expected)


def test_zero_return_is_just_the_sum_of_contributions():
    p = single_asset(annual_returns={"A": 0.0}, initial_assets=100, savings_rate=0.5,
                     monthly_salary=1000, annual_raise=0.05, years=3)
    df = simulate(p)
    assert df["total"].iloc[-1] == pytest.approx(df["invested"].iloc[-1])
    assert df["gain"].abs().max() == pytest.approx(0, abs=1e-6)


def test_salary_raise_applies_every_12_months():
    df = simulate(single_asset(monthly_salary=1000, annual_raise=0.1, years=2))
    assert df.loc[12, "salary"] == pytest.approx(1000)
    assert df.loc[13, "salary"] == pytest.approx(1100)


def test_rebalance_irrelevant_when_all_returns_equal():
    kw = dict(allocation={"A": 0.5, "B": 0.5}, annual_returns={"A": 0.05, "B": 0.05})
    on = simulate(Params(**kw, rebalance=True))["total"].iloc[-1]
    off = simulate(Params(**kw, rebalance=False))["total"].iloc[-1]
    assert on == pytest.approx(off)


@pytest.mark.parametrize("bad", [
    dict(allocation={"A": 0.5}, annual_returns={"A": 0.05}),
    dict(allocation={"A": 1.0}, annual_returns={}),
    dict(allocation={"A": 1.5, "B": -0.5}, annual_returns={"A": 0.05, "B": 0.05}),
])
def test_invalid_params_raise(bad):
    with pytest.raises(ValueError):
        simulate(Params(**bad))
