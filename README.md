# asset-sim

個人資產成長模擬器，同時是學習 ML 與相關數學的專案：每個階段替模擬器加一個新功能，並學一個數學 / ML 主題。

## 快速開始

```bash
uv sync                              # 安裝核心套件
uv sync --group ml                   # （第 6 階段才需要）PyTorch + CUDA 12.8
uv run streamlit run app.py          # 開啟介面，在 Windows 瀏覽器打開 http://localhost:8501
uv run jupyter lab                   # 開啟 notebooks
uv run pytest                        # 執行測試
```

## 結構

```
notebooks/        每個階段的學習筆記與練習題
src/assetsim/     模擬引擎與共用程式
  cashflow.py     逐月現金流模擬（Params, simulate）
  formulas.py     複利與年金的封閉解，用來驗證模擬
  plotting.py     matplotlib 中文字型設定
tests/            驗證數學與模擬的正確性
data/             下載的價格資料（不進 git）
app.py            Streamlit 介面
```

## 學習路線

| 階段 | 模擬器功能 | 數學 / ML |
|---|---|---|
| ✅ 0 | 固定報酬率的現金流模擬 | 複利、等比級數 |
| 1 | 蒙地卡羅模擬，畫出 P10/P50/P90 區間 | 機率分布、對數報酬、期望值與變異數、大數法則 |
| 2 | 多資產相關性 | 共變異數矩陣、Cholesky 分解 |
| 3 | 從歷史資料估計參數、處理肥尾 | MLE、t 分布、bootstrap |
| 4 | 手刻線性迴歸預測波動度 | 梯度下降、正則化、walk-forward 驗證 |
| 5 | 判斷市場狀態（regime） | GARCH、HMM、EM 演算法 |
| 6 | PyTorch 在 GPU 上跑 MLP / LSTM | 反向傳播、autograd |
| 7 | 自動算出最佳配置比例 | 凸優化、拉格朗日乘數、mean-variance |

原則：先用 numpy 手刻再用套件；每個模型都要和簡單的基準比較。
