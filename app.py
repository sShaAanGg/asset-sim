"""資產模擬器介面. 啟動: uv run streamlit run app.py"""

import streamlit as st

from assetsim.cashflow import (BROKER_FEE, ETF_SELL_TAX, STOCK_SELL_TAX, Asset, Params,
                               effective_return, simulate)
from assetsim.plans import get_default_plan, list_plans, load_plan, save_plan, set_default_plan

st.set_page_config(page_title="資產模擬器", layout="wide")
st.title("資產模擬器 — 第 0 階段: 固定報酬率")

SECURITIES = {"ETF": ETF_SELL_TAX, "股票": STOCK_SELL_TAX}  # 介面上的證券類資產與各自的證交稅
WEIGHT_KEYS = {"ETF": "etf_pct", "股票": "stock_pct"}
CASH = "現金"
PAYOUTS = (1, 2, 3, 4, 6, 12)


def pct(x: float) -> float:
    return round(x * 100, 4)


def to_widgets(p: Params) -> dict:
    """Params → 各個 widget 的值 (百分比用 % 表示)."""
    etf, stock, cash = p.assets["ETF"], p.assets["股票"], p.assets[CASH]
    w = {
        "initial": float(p.initial_assets), "salary": float(p.monthly_salary),
        "raise_pct": pct(p.annual_raise), "bonus_months": float(p.bonus_months),
        "expenses": float(p.monthly_expenses), "inflation_pct": pct(p.inflation),
        "emergency_months": float(p.emergency_months), "emergency_pct": pct(p.emergency_rate),
        "years": p.years, "rebalance": p.rebalance,
        **{key: round(p.assets[n].weight * 100) for n, key in WEIGHT_KEYS.items()},
        "cash_rate_pct": pct(cash.price_return),
        "fee_discount": round(etf.fee_rate / BROKER_FEE, 4),
        "sell_tax_on": etf.sell_tax > 0 or stock.sell_tax > 0,
        "div_tax_pct": pct(p.dividend_tax_rate), "nhi_on": p.nhi_rate > 0,
    }
    for n in SECURITIES:
        a = p.assets[n]
        w |= {f"{n}_pr": pct(a.price_return), f"{n}_dy": pct(a.dividend_yield),
              f"{n}_k": a.payouts_per_year, f"{n}_er": pct(a.expense_ratio),
              f"{n}_reinvest": a.reinvest_dividends}
    return w


def from_widgets(s) -> Params:
    """各個 widget 的值 → Params."""
    fee = BROKER_FEE * s.fee_discount
    assets = {
        n: Asset(s[WEIGHT_KEYS[n]] / 100, price_return=s[f"{n}_pr"] / 100, dividend_yield=s[f"{n}_dy"] / 100,
                 payouts_per_year=s[f"{n}_k"], expense_ratio=s[f"{n}_er"] / 100,
                 fee_rate=fee, sell_tax=tax if s.sell_tax_on else 0.0,
                 reinvest_dividends=s[f"{n}_reinvest"])
        for n, tax in SECURITIES.items()
    }
    assets[CASH] = Asset((100 - s.etf_pct - s.stock_pct) / 100, price_return=s.cash_rate_pct / 100)
    return Params(
        initial_assets=s.initial, monthly_salary=s.salary, annual_raise=s.raise_pct / 100,
        bonus_months=s.bonus_months, monthly_expenses=s.expenses, inflation=s.inflation_pct / 100,
        emergency_months=s.emergency_months, emergency_rate=s.emergency_pct / 100, assets=assets,
        nhi_rate=Params.nhi_rate if s.nhi_on else 0.0, dividend_tax_rate=s.div_tax_pct / 100,
        years=s.years, rebalance=s.rebalance,
    )


def apply_plan(name: str) -> bool:
    """把方案的值放進 session_state; 失敗時留下錯誤訊息並回傳 False."""
    try:
        st.session_state.update(to_widgets(load_plan(name)))
        return True
    except FileNotFoundError:
        st.session_state.plan_msg = ("error", f"找不到方案 '{name}'")
        return False
    except (OSError, ValueError, KeyError, TypeError) as e:
        st.session_state.plan_msg = ("error", f"無法載入 '{name}': {e}")
        return False


def load_selected() -> None:
    # 在 callback 裡改 session_state, 才會在 widget 建立前生效
    name = st.session_state.plan_choice
    if apply_plan(name):
        st.session_state.plan_msg = ("success", f"已載入 '{name}'")


def toggle_default() -> None:
    name = st.session_state.plan_choice
    if get_default_plan() == name:
        set_default_plan(None)
        st.session_state.plan_msg = ("success", f"已取消預設方案 '{name}'")
    else:
        set_default_plan(name)
        st.session_state.plan_msg = ("success", f"已把 '{name}' 設為預設方案")


# 每個瀏覽器 session 開始時: 有預設方案就載入, 否則 (或載入失敗) 用 Params() 的預設值
if "started" not in st.session_state:
    st.session_state.started = True
    st.session_state.update(to_widgets(Params()))
    try:
        default = get_default_plan()
    except (OSError, ValueError) as e:
        default = None
        st.session_state.plan_msg = ("error", f"無法讀取設定檔: {e}")
    if default and apply_plan(default):
        st.session_state.plan_choice = default
        st.session_state.plan_msg = ("info", f"已載入預設方案 '{default}'")

money = dict(min_value=0.0, format="%.0f")
with st.sidebar:
    st.header("收入")
    st.number_input("起始資產 (TWD)", max_value=1e9, step=100_000.0, key="initial", **money)
    st.number_input("月薪 (TWD)", max_value=1e7, step=5_000.0, key="salary", **money)
    st.slider("每年加薪 %", 0.0, 50.0, step=0.5, key="raise_pct")
    st.number_input("年終獎金 (月)", 0.0, 24.0, step=0.5, key="bonus_months")

    st.header("開銷")
    st.number_input("每月生活開銷 (TWD)", max_value=1e7, step=1_000.0, key="expenses", **money)
    st.slider("通膨 % (開銷每年調整)", 0.0, 10.0, step=0.25, key="inflation_pct")
    st.number_input("緊急預備金 (幾個月開銷)", 0.0, 60.0, step=1.0, key="emergency_months")
    st.number_input("緊急預備金年利率 %", 0.0, 10.0, step=0.1, key="emergency_pct")

    st.header("配置比例")
    st.slider("ETF %", 0, 100, key="etf_pct")
    st.slider("股票 %", 0, 100, key="stock_pct")
    cash_pct = 100 - st.session_state.etf_pct - st.session_state.stock_pct
    if cash_pct < 0:
        st.error(f"ETF + 股票 = {100 - cash_pct}%, 不能超過 100%")
        st.stop()
    st.caption(f"現金 %: {cash_pct}")
    st.checkbox("每年再平衡", key="rebalance")
    st.slider("模擬年數", 1, 50, key="years")

    st.header("各資產")
    st.caption("價格報酬要填**不含股息, 未扣內扣費用**的數字; 下方的 '總報酬' 可以和 ETF 公布的含息報酬比較.")
    for n in SECURITIES:
        with st.expander(n):
            st.number_input("價格報酬 %", -20.0, 30.0, step=0.5, key=f"{n}_pr")
            st.number_input("股息殖利率 %", 0.0, 20.0, step=0.25, key=f"{n}_dy")
            st.selectbox("每年配息次數", PAYOUTS, key=f"{n}_k")
            st.number_input("內扣費用 %", 0.0, 5.0, step=0.05, key=f"{n}_er")
            st.checkbox("股息再投入 (否則併入當月可投入的現金)", key=f"{n}_reinvest")
    with st.expander(CASH):
        st.number_input("年利率 %", 0.0, 10.0, step=0.1, key="cash_rate_pct")

    st.header("費用與稅")
    st.slider("手續費折扣 (1 = 不打折)", 0.0, 1.0, step=0.05, key="fee_discount")
    st.checkbox("計入證交稅 (ETF 0.1%, 股票 0.3%)", key="sell_tax_on")
    st.checkbox("計入二代健保補充保費 (單次股息 ≥ 20,000 收 2.11%)", key="nhi_on")
    st.number_input("股利所得有效稅率 %", 0.0, 40.0, step=1.0, key="div_tax_pct")

p = from_widgets(st.session_state)

with st.sidebar:
    for n in SECURITIES:
        st.caption(f"{n} 總報酬 (股息再投入, 不計稅費): {effective_return(p.assets[n]):.2%}")

    st.header("方案")
    saved = list_plans()
    try:
        default = get_default_plan()
    except (OSError, ValueError):
        default = None
    if saved:
        if st.session_state.get("plan_choice") not in saved:
            st.session_state.plan_choice = default if default in saved else saved[0]
        st.selectbox("已存的方案", saved, key="plan_choice",
                     format_func=lambda n: f"★ {n}" if n == default else n)
        c1, c2 = st.columns(2)
        c1.button("載入", on_click=load_selected, width="stretch")
        c2.button("取消預設" if st.session_state.plan_choice == default else "設為預設",
                  on_click=toggle_default, width="stretch")
    name = st.text_input("方案名稱", placeholder="例如: 保守, 積極")
    if st.button("儲存目前設定", disabled=not name.strip()):
        try:
            save_plan(p, name)
            st.session_state.plan_msg = ("success", f"已儲存 '{name.strip()}'"
                                         + ("(覆蓋舊檔)" if name.strip() in saved else ""))
            st.rerun()
        except ValueError as e:
            st.error(str(e))
    if msg := st.session_state.pop("plan_msg", None):
        getattr(st, msg[0])(msg[1])

try:
    df = simulate(p)
except ValueError as e:
    st.error(str(e))
    st.stop()
last = df.iloc[-1]
first_year = df.loc[1:12]

c1, c2, c3, c4 = st.columns(4)
c1.metric(f"{p.years} 年後總資產 (市值)", f"{last['total']:,.0f}")
c2.metric("全部賣出後淨值", f"{last['liquidation']:,.0f}")
c3.metric("累計投入本金", f"{last['invested']:,.0f}")
c4.metric("投資收益", f"{last['gain']:,.0f}",
          f"{last['gain'] / last['invested']:.0%} 報酬" if last["invested"] > 0 else None)

c1, c2, c3, c4 = st.columns(4)
c1.metric("第一年儲蓄率", f"{first_year['surplus'].sum() / first_year['income'].sum():.0%}"
          if first_year["income"].sum() > 0 else "—")
c2.metric("累計股息 (稅前)", f"{last['dividends']:,.0f}")
c3.metric("累計手續費", f"{last['fees']:,.0f}")
c4.metric("累計稅 (補充保費, 股利稅, 證交稅)", f"{last['taxes']:,.0f}")

if last["shortfall"] > 0:
    first = df.loc[df["shortfall"] > 0, "year"].iloc[0]
    st.error(f"資產在第 {first:.1f} 年用完, 之後付不出的開銷累計 {last['shortfall']:,.0f}")

yearly = df[df["month"] % 12 == 0].set_index("year")
holdings = [*p.assets, "emergency"]
st.subheader("總資產 vs 投入本金")
st.line_chart(yearly[["total", "invested"]].rename(columns={"total": "總資產", "invested": "投入本金"}))
st.subheader("各資產價值")
st.area_chart(yearly[holdings].rename(columns={"emergency": "緊急預備金"}))

with st.expander("逐年明細"):
    columns = ["salary", "income", "expenses", "surplus", *holdings, "total", "liquidation",
               "invested", "gain", "dividends", "fees", "taxes"]
    st.dataframe(yearly[columns].style.format("{:,.0f}"))
