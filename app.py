"""資產模擬器介面。啟動：uv run streamlit run app.py"""

import streamlit as st

from assetsim.cashflow import Params, simulate
from assetsim.plans import get_default_plan, list_plans, load_plan, save_plan, set_default_plan

st.set_page_config(page_title="資產模擬器", layout="wide")
st.title("資產模擬器 — 第 0 階段：固定報酬率")


def to_widgets(p: Params) -> dict:
    """Params → 各個 widget 的值（百分比用 % 表示）。"""
    pct = lambda x: round(x * 100, 2)  # noqa: E731
    return {
        "initial": int(p.initial_assets), "salary": int(p.monthly_salary),
        "raise_pct": pct(p.annual_raise), "savings_pct": round(p.savings_rate * 100),
        "years": p.years, "rebalance": p.rebalance,
        "etf_pct": round(p.allocation["ETF"] * 100), "stock_pct": round(p.allocation["股票"] * 100),
        "r_etf": pct(p.annual_returns["ETF"]), "r_stock": pct(p.annual_returns["股票"]),
        "r_cash": pct(p.annual_returns["現金"]),
    }


def apply_plan(name: str) -> bool:
    """把方案的值放進 session_state；失敗時留下錯誤訊息並回傳 False。"""
    try:
        st.session_state.update(to_widgets(load_plan(name)))
        return True
    except FileNotFoundError:
        st.session_state.plan_msg = ("error", f"找不到方案「{name}」")
        return False
    except (OSError, ValueError, KeyError, TypeError) as e:
        st.session_state.plan_msg = ("error", f"無法載入「{name}」：{e}")
        return False


def load_selected() -> None:
    # 在 callback 裡改 session_state，才會在 widget 建立前生效
    name = st.session_state.plan_choice
    if apply_plan(name):
        st.session_state.plan_msg = ("success", f"已載入「{name}」")


def toggle_default() -> None:
    name = st.session_state.plan_choice
    if get_default_plan() == name:
        set_default_plan(None)
        st.session_state.plan_msg = ("success", f"已取消預設方案「{name}」")
    else:
        set_default_plan(name)
        st.session_state.plan_msg = ("success", f"已把「{name}」設為預設方案")


# 每個瀏覽器 session 開始時：有預設方案就載入，否則（或載入失敗）用 Params() 的預設值
if "started" not in st.session_state:
    st.session_state.started = True
    st.session_state.update(to_widgets(Params()))
    try:
        default = get_default_plan()
    except (OSError, ValueError) as e:
        default = None
        st.session_state.plan_msg = ("error", f"無法讀取設定檔：{e}")
    if default and apply_plan(default):
        st.session_state.plan_choice = default
        st.session_state.plan_msg = ("info", f"已載入預設方案「{default}」")

with st.sidebar:
    st.header("收入與投入")
    initial = st.number_input("起始資產 (TWD)", 0, 100_000_000, step=100_000, key="initial")
    salary = st.number_input("月薪 (TWD)", 0, 2_000_000, step=5_000, key="salary")
    raise_pct = st.slider("每年加薪 %", 0.0, 10.0, step=0.5, key="raise_pct")
    savings_pct = st.slider("薪水投入比例 %", 0, 100, key="savings_pct")
    years = st.slider("模擬年數", 1, 50, key="years")

    st.header("配置比例")
    etf_pct = st.slider("ETF %", 0, 100, key="etf_pct")
    stock_pct = st.slider("股票 %", 0, 100, key="stock_pct")
    cash_pct = 100 - etf_pct - stock_pct
    if cash_pct < 0:
        st.error(f"ETF + 股票 = {etf_pct + stock_pct}%，不能超過 100%")
        st.stop()
    st.caption(f"現金 %：{cash_pct}")
    rebalance = st.checkbox("每年再平衡", key="rebalance")

    st.header("預期年化報酬率 %")
    r_etf = st.slider("ETF", -5.0, 15.0, step=0.5, key="r_etf")
    r_stock = st.slider("股票", -5.0, 20.0, step=0.5, key="r_stock")
    r_cash = st.slider("現金", 0.0, 5.0, step=0.25, key="r_cash")

p = Params(
    initial_assets=initial,
    monthly_salary=salary,
    annual_raise=raise_pct / 100,
    savings_rate=savings_pct / 100,
    allocation={"ETF": etf_pct / 100, "股票": stock_pct / 100, "現金": cash_pct / 100},
    annual_returns={"ETF": r_etf / 100, "股票": r_stock / 100, "現金": r_cash / 100},
    years=years,
    rebalance=rebalance,
)

with st.sidebar:
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
    name = st.text_input("方案名稱", placeholder="例如：保守、積極")
    if st.button("儲存目前設定", disabled=not name.strip()):
        try:
            save_plan(p, name)
            st.session_state.plan_msg = ("success", f"已儲存「{name.strip()}」"
                                         + ("（覆蓋舊檔）" if name.strip() in saved else ""))
            st.rerun()
        except ValueError as e:
            st.error(str(e))
    if msg := st.session_state.pop("plan_msg", None):
        getattr(st, msg[0])(msg[1])

df = simulate(p)
last = df.iloc[-1]

c1, c2, c3 = st.columns(3)
c1.metric(f"{years} 年後總資產", f"{last['total']:,.0f}")
c2.metric("累計投入本金", f"{last['invested']:,.0f}")
c3.metric("投資收益", f"{last['gain']:,.0f}", f"{last['gain'] / last['invested']:.0%} 報酬")

yearly = df[df["month"] % 12 == 0].set_index("year")
st.subheader("總資產 vs 投入本金")
st.line_chart(yearly[["total", "invested"]].rename(columns={"total": "總資產", "invested": "投入本金"}))
st.subheader("各資產價值")
st.area_chart(yearly[list(p.allocation)])

with st.expander("逐年明細"):
    st.dataframe(yearly[["salary", "contribution", *p.allocation, "total", "invested", "gain"]]
                 .style.format("{:,.0f}"))
