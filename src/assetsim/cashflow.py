"""第 0 階段：固定報酬率的現金流模擬（deterministic cash-flow simulation）。

每個月的順序：
1. 各資產依價格報酬（price return）成長，再扣掉當月的內扣費用（expense ratio）
2. 配息月份：股息（dividend）扣掉二代健保補充保費與股利所得稅後，
   再投入同一資產，或併入當月可投入的現金
3. 收入（薪水；每年第 12 個月加上年終獎金）減掉生活開銷 = 結餘（surplus）
   - 結餘 ≥ 0：先補足緊急預備金（emergency fund），剩下的依配置比例買進（付手續費）
   - 結餘 < 0：先動用緊急預備金，不夠再依市值比例賣出資產（付證交稅與手續費）
   月底才投入，對應期末年金（ordinary annuity）
4. 每滿 12 個月：若開啟再平衡（rebalancing），賣出超配的資產、買進低配的資產；
   記錄完這個月之後，薪水調漲、開銷隨通膨（inflation）調整

注意：price_return 要填「不含股息、尚未扣內扣費用」的價格報酬。
ETF 公布的歷史年化報酬通常已經含息、也已扣掉內扣費用，直接填進來會重複計算。
effective_return() 會換算回可以和歷史數字比較的總報酬（total return）。
"""

from dataclasses import dataclass, field

import pandas as pd

BROKER_FEE = 0.001425  # 券商手續費牌告費率（買、賣都收）
ETF_SELL_TAX = 0.001  # ETF 證交稅（只在賣出時收）
STOCK_SELL_TAX = 0.003  # 個股證交稅

# simulate() 輸出的欄位名稱，資產不能用這些名字
RESERVED_COLUMNS = {
    "month", "year", "salary", "income", "expenses", "surplus", "emergency", "total",
    "liquidation", "invested", "gain", "dividends", "fees", "taxes", "shortfall",
}


@dataclass
class Asset:
    weight: float  # 配置比例（allocation weight）
    price_return: float = 0.0  # 年化價格報酬：不含股息、未扣內扣費用
    dividend_yield: float = 0.0  # 年化股息殖利率（dividend yield）
    payouts_per_year: int = 1  # 每年配息次數，必須整除 12
    expense_ratio: float = 0.0  # 年化內扣費用（經理費、保管費等），按月從淨值扣除
    fee_rate: float = 0.0  # 券商手續費率（已含折扣），買、賣都收
    sell_tax: float = 0.0  # 證交稅率，只在賣出時收
    reinvest_dividends: bool = True  # True：再投入同一資產；False：併入當月可投入的現金


def default_assets() -> dict[str, Asset]:
    return {
        "ETF": Asset(0.6, price_return=0.043, dividend_yield=0.03, payouts_per_year=4,
                     expense_ratio=0.003, fee_rate=BROKER_FEE, sell_tax=ETF_SELL_TAX),
        "股票": Asset(0.3, price_return=0.065, dividend_yield=0.025, payouts_per_year=1,
                      fee_rate=BROKER_FEE, sell_tax=STOCK_SELL_TAX),
        "現金": Asset(0.1, price_return=0.01),
    }


@dataclass
class Params:
    initial_assets: float = 1_000_000  # 起始資產（TWD）：先放進緊急預備金，其餘視為已依配置比例持有
    monthly_salary: float = 60_000  # 月薪
    annual_raise: float = 0.03  # 每年加薪幅度
    bonus_months: float = 1.0  # 年終獎金（幾個月薪水），每年第 12 個月發放
    monthly_expenses: float = 35_000  # 每月生活開銷
    inflation: float = 0.02  # 通膨率：開銷每年依此調整
    emergency_months: float = 6.0  # 緊急預備金要維持幾個月的開銷
    emergency_rate: float = 0.01  # 緊急預備金的年利率（活存）
    assets: dict[str, Asset] = field(default_factory=default_assets)
    nhi_rate: float = 0.0211  # 二代健保補充保費率
    nhi_threshold: float = 20_000  # 單次股息達到這個金額才收補充保費
    dividend_tax_rate: float = 0.0  # 股利所得的有效稅率（合併計稅抵減後，很多人接近 0）
    years: int = 30
    rebalance: bool = True  # 每年再平衡回目標配置

    @classmethod
    def from_dict(cls, d: dict) -> "Params":
        """dataclasses.asdict() 的反向：把巢狀的 dict 轉回 Asset。"""
        return cls(**{**d, "assets": {n: Asset(**a) for n, a in d["assets"].items()}})

    def validate(self) -> None:
        if not self.assets:
            raise ValueError("至少要有一種資產")
        if clash := RESERVED_COLUMNS & set(self.assets):
            raise ValueError(f"資產名稱不能用：{clash}")
        weights = [a.weight for a in self.assets.values()]
        if abs(sum(weights) - 1) > 1e-9:
            raise ValueError(f"配置比例總和必須是 1，目前是 {sum(weights)}")
        if any(w < 0 for w in weights):
            raise ValueError("配置比例不能是負數")
        for name, a in self.assets.items():
            if a.payouts_per_year not in (1, 2, 3, 4, 6, 12):
                raise ValueError(f"{name} 的每年配息次數必須整除 12，目前是 {a.payouts_per_year}")
            if not (0 <= a.expense_ratio < 1 and 0 <= a.dividend_yield and 0 <= a.fee_rate
                    and 0 <= a.sell_tax and a.fee_rate + a.sell_tax < 1):
                raise ValueError(f"{name} 的費率或殖利率超出合理範圍")
        if self.monthly_expenses < 0 or self.emergency_months < 0 or self.bonus_months < 0:
            raise ValueError("開銷、緊急預備金月數、年終月數不能是負數")
        if not 0 <= self.dividend_tax_rate < 1 or not 0 <= self.nhi_rate < 1:
            raise ValueError("稅率必須介於 0 和 1 之間")
        if self.years < 1:
            raise ValueError("模擬年數至少 1 年")


def monthly_rate(annual_rate: float) -> float:
    """年化報酬率（annualized return）換成等效月報酬率（equivalent monthly rate）：(1 + r)^(1/12) - 1。

    不用 r/12：那是名目利率（nominal rate）的換算，複利一年後會超過 r。
    """
    return (1 + annual_rate) ** (1 / 12) - 1


def effective_return(a: Asset) -> float:
    """股息全部再投入、不計手續費與稅時的等效年化總報酬（total return）。

    一年內：價格成長 (1 + price_return)，扣內扣費用 (1 - expense_ratio)，
    每次配息再投入乘上 (1 + dividend_yield / k)，共 k 次。
    """
    k = a.payouts_per_year
    return (1 + a.price_return) * (1 - a.expense_ratio) * (1 + a.dividend_yield / k) ** k - 1


def simulate(p: Params) -> pd.DataFrame:
    """逐月模擬，回傳每個月月底的狀態（第 0 列是起始狀態）。

    total 是市值；liquidation 是全部賣出、扣掉證交稅與手續費後拿到的錢。
    dividends、fees、taxes、shortfall 都是累計值；shortfall 是資產賣光後仍付不出的開銷。
    """
    p.validate()
    assets = p.assets
    names = list(assets)
    growth = {n: (1 + monthly_rate(assets[n].price_return)) * (1 - assets[n].expense_ratio) ** (1 / 12)
              for n in names}
    emergency_growth = 1 + monthly_rate(p.emergency_rate)

    salary, expenses = p.monthly_salary, p.monthly_expenses
    emergency = min(p.initial_assets, p.emergency_months * expenses)
    holdings = {n: (p.initial_assets - emergency) * assets[n].weight for n in names}
    invested = p.initial_assets
    acc = {"dividends": 0.0, "fees": 0.0, "taxes": 0.0, "shortfall": 0.0}

    def buy(n: str, cash: float) -> None:
        notional = cash / (1 + assets[n].fee_rate)
        holdings[n] += notional
        acc["fees"] += cash - notional

    def sell(n: str, notional: float) -> float:
        """賣出市值 notional，回傳扣掉證交稅與手續費後拿到的現金。"""
        holdings[n] -= notional
        fee, tax = notional * assets[n].fee_rate, notional * assets[n].sell_tax
        acc["fees"] += fee
        acc["taxes"] += tax
        return notional - fee - tax

    def raise_cash(need: float) -> float:
        """依市值比例賣出，湊出 need 元，回傳湊不到的金額。"""
        mv = sum(holdings.values())
        if mv <= 0:
            return need
        weights = {n: holdings[n] / mv for n in names}
        net_per_dollar = sum(weights[n] * (1 - assets[n].fee_rate - assets[n].sell_tax) for n in names)
        notional = min(need / net_per_dollar, mv)
        got = sum(sell(n, notional * weights[n]) for n in names)
        return max(0.0, need - got)

    def rebalance() -> None:
        mv = sum(holdings.values())
        target = {n: mv * assets[n].weight for n in names}
        proceeds = sum(sell(n, holdings[n] - target[n]) for n in names if holdings[n] > target[n])
        deficit = {n: target[n] - holdings[n] for n in names if holdings[n] < target[n]}
        total_deficit = sum(deficit.values())
        for n, d in deficit.items():
            buy(n, proceeds * d / total_deficit)

    def row(m: int, income: float, surplus: float) -> dict:
        liquidation = sum(holdings[n] * (1 - assets[n].fee_rate - assets[n].sell_tax) for n in names)
        return {"month": m, "salary": salary if m else 0.0, "income": income,
                "expenses": expenses if m else 0.0, "surplus": surplus, **holdings,
                "emergency": emergency, "total": sum(holdings.values()) + emergency,
                "liquidation": liquidation + emergency, "invested": invested, **acc}

    rows = [row(0, 0.0, 0.0)]
    for m in range(1, p.years * 12 + 1):
        for n in names:
            holdings[n] *= growth[n]
        emergency *= emergency_growth

        cash = 0.0  # 這個月可以投入的現金
        for n in names:
            a = assets[n]
            if a.dividend_yield and m % (12 // a.payouts_per_year) == 0:
                gross = holdings[n] * a.dividend_yield / a.payouts_per_year
                tax = gross * p.dividend_tax_rate + (gross * p.nhi_rate if gross >= p.nhi_threshold else 0.0)
                acc["dividends"] += gross
                acc["taxes"] += tax
                if a.reinvest_dividends:
                    buy(n, gross - tax)
                else:
                    cash += gross - tax

        year_end = m % 12 == 0
        income = salary * (1 + (p.bonus_months if year_end else 0))
        surplus = income - expenses
        invested += surplus
        cash += surplus
        if cash >= 0:
            top_up = min(cash, max(0.0, p.emergency_months * expenses - emergency))
            emergency += top_up
            for n in names:
                buy(n, (cash - top_up) * assets[n].weight)
        else:
            draw = min(-cash, emergency)
            emergency -= draw
            unpaid = raise_cash(-cash - draw)
            acc["shortfall"] += unpaid
            invested += unpaid  # 沒付出去的開銷，沒有真的從資產裡拿走

        if year_end and p.rebalance:
            rebalance()
        rows.append(row(m, income, surplus))
        if year_end:
            salary *= 1 + p.annual_raise
            expenses *= 1 + p.inflation

    df = pd.DataFrame(rows)
    df["year"] = df["month"] / 12
    df["gain"] = df["total"] - df["invested"]
    return df
