"""資產模擬器介面。啟動：uv run streamlit run app.py"""

import streamlit as st

from assetsim.cashflow import Params, simulate

st.set_page_config(page_title="資產模擬器", layout="wide")
st.title("資產模擬器 — 第 0 階段：固定報酬率")

with st.sidebar:
    st.header("收入與投入")
    initial = st.number_input("起始資產 (TWD)", 0, 100_000_000, 1_000_000, step=100_000)
    salary = st.number_input("月薪 (TWD)", 0, 2_000_000, 60_000, step=5_000)
    raise_pct = st.slider("每年加薪 %", 0.0, 10.0, 3.0, 0.5)
    savings_pct = st.slider("薪水投入比例 %", 0, 100, 30)
    years = st.slider("模擬年數", 1, 50, 30)

    st.header("配置比例")
    etf_pct = st.slider("ETF %", 0, 100, 60)
    stock_pct = st.slider("股票 %", 0, 100, 30)
    cash_pct = 100 - etf_pct - stock_pct
    if cash_pct < 0:
        st.error(f"ETF + 股票 = {etf_pct + stock_pct}%，不能超過 100%")
        st.stop()
    st.caption(f"現金 %：{cash_pct}")
    rebalance = st.checkbox("每年再平衡", value=True)

    st.header("預期年化報酬率 %")
    r_etf = st.slider("ETF", -5.0, 15.0, 7.0, 0.5)
    r_stock = st.slider("股票", -5.0, 20.0, 9.0, 0.5)
    r_cash = st.slider("現金", 0.0, 5.0, 1.0, 0.25)

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
