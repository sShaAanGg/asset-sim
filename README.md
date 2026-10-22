# asset-sim

個人資產成長模擬器，同時是學習 ML 與相關數學的專案：每個階段替模擬器加一個新功能，並學一個數學 / ML 主題。

## 快速開始

```bash
uv sync                              # 安裝全部套件（含 dev 與 ml 群組）
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

## 學習計畫

學習路線、各階段的完成條件與進度，請見 [plan.md](plan.md)。
