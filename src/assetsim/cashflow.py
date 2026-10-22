"""第 0 階段：固定報酬率的現金流模擬（deterministic cash-flow simulation）。

每個月的順序：
1. 各資產依各自的月報酬率（monthly return）成長
2. 薪水 × 投入比例 的金額，依配置比例（allocation weights）投入各資產
   （月底投入，對應期末年金 ordinary annuity）
3. 每滿 12 個月：薪水調漲；若開啟再平衡（rebalancing），把總資產重新依配置比例分配
"""

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class Params:
    initial_assets: float = 1_000_000  # 起始資產（TWD），依配置比例分配
    monthly_salary: float = 60_000  # 月薪
    annual_raise: float = 0.03  # 每年加薪幅度
    savings_rate: float = 0.30  # 每月薪水投入的比例
    allocation: dict[str, float] = field(
        default_factory=lambda: {"ETF": 0.6, "股票": 0.3, "現金": 0.1}
    )
    annual_returns: dict[str, float] = field(
        default_factory=lambda: {"ETF": 0.07, "股票": 0.09, "現金": 0.01}
    )
    years: int = 30
    rebalance: bool = True  # 每年再平衡回目標配置

    def validate(self) -> None:
        if abs(sum(self.allocation.values()) - 1) > 1e-9:
            raise ValueError(f"配置比例總和必須是 1，目前是 {sum(self.allocation.values())}")
        if any(w < 0 for w in self.allocation.values()):
            raise ValueError("配置比例不能是負數")
        missing = set(self.allocation) - set(self.annual_returns)
        if missing:
            raise ValueError(f"缺少這些資產的報酬率：{missing}")
        if not 0 <= self.savings_rate <= 1:
            raise ValueError("投入比例必須介於 0 和 1 之間")


def monthly_rate(annual_rate: float) -> float:
    """年化報酬率（annualized return）換成等效月報酬率（equivalent monthly rate）：(1 + r)^(1/12) - 1。

    不用 r/12：那是名目利率（nominal rate）的換算，複利一年後會超過 r。
    """
    return (1 + annual_rate) ** (1 / 12) - 1


def simulate(p: Params) -> pd.DataFrame:
    """逐月模擬，回傳每個月月底的狀態（第 0 列是起始狀態）。"""
    p.validate()
    assets = list(p.allocation)
    rates = {a: monthly_rate(p.annual_returns[a]) for a in assets}
    holdings = {a: p.initial_assets * p.allocation[a] for a in assets}
    salary = p.monthly_salary
    invested = p.initial_assets

    rows = [{"month": 0, "salary": 0.0, "contribution": 0.0, **holdings,
             "total": p.initial_assets, "invested": invested}]
    for m in range(1, p.years * 12 + 1):
        for a in assets:
            holdings[a] *= 1 + rates[a]
        contribution = salary * p.savings_rate
        for a in assets:
            holdings[a] += contribution * p.allocation[a]
        invested += contribution
        total = sum(holdings.values())
        rows.append({"month": m, "salary": salary, "contribution": contribution,
                     **holdings, "total": total, "invested": invested})

        if m % 12 == 0:
            salary *= 1 + p.annual_raise
            if p.rebalance:
                holdings = {a: total * p.allocation[a] for a in assets}

    df = pd.DataFrame(rows)
    df["year"] = df["month"] / 12
    df["gain"] = df["total"] - df["invested"]
    return df
