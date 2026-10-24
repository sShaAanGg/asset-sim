"""複利 (compound interest) 與等比級數 (geometric series) 的封閉解 (closed-form solution),
用來驗證逐月模擬的結果.

推導見 notebooks/00_compound_interest.ipynb.
"""

# 複利計算公式 (compound interest formula)
def fv_lump_sum(principal: float, i: float, n: int) -> float:
    """單筆投入 (lump sum) n 期後的終值 (future value): P(1+i)^n."""
    return principal * (1 + i) ** n


def fv_annuity(payment: float, i: float, n: int) -> float:
    """期末年金 (ordinary annuity): 每期期末投入固定金額 C, n 期後的終值.

    C(1+i)^(n-1) + ... + C(1+i) + C = C((1+i)^n - 1) / i (等比級數求和, sum of a geometric series)
    """
    if i == 0:
        return payment * n
    return payment * ((1 + i) ** n - 1) / i
