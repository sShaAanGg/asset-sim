# asset-sim

個人資產成長模擬器，同時是學習 ML 與相關數學的專案：每個階段替模擬器加一個新功能，並學一個數學 / ML 主題
Built with Claude Code

## 快速開始

```bash
uv sync                              # 安裝全部套件 (含 dev 與 ml 群組)
uv run streamlit run app.py          # 開啟介面，在 Windows 瀏覽器打開 http://localhost:8501
uv run jupyter lab                   # 開啟 notebooks
uv run pytest                        # 執行測試
```

介面怎麼用 (每個欄位的意思、怎麼看結果、怎麼存方案)：請見 [使用說明 docs/usage.md](docs/usage.md)。

## 結構

```
notebooks/        每個階段的學習筆記與練習題
src/assetsim/     模擬引擎與共用程式
  cashflow.py     逐月現金流模擬 (Params, Asset, simulate)：開銷、年終、緊急預備金、股息、費用與稅
  formulas.py     複利與年金的封閉解，用來驗證模擬
  plotting.py     matplotlib 中文字型設定
  plans.py        把設定存成具名方案 (plan，JSON)，可再載入，也可指定預設方案
tests/            驗證數學與模擬的正確性
docs/             文件：usage.md (使用說明)、data-migration.md (資料格式改版時怎麼安全遷移)、
                  continuous-integration.md (CI 關卡的規則)
data/             下載的價格資料、存下的方案 (不進 git；可用 ASSETSIM_DATA_DIR 改位置)
app.py            Streamlit 介面
.github/workflows/ci.yml  CI：每個 PR 與 main 上都跑 pytest
```

## 持續整合 (CI)

所有修改都透過 PR 合進 `main`，CI 的 `test` 檢查要通過才能合併。流程與規則請見 [docs/continuous-integration.md](docs/continuous-integration.md)。

## 學習計畫

學習路線、各階段的完成條件與進度，請見 [plan.md](plan.md)。

## 授權與免責聲明

- 授權：[MIT License](LICENSE)。
- 本專案是學習用的模擬器，結果取決於你輸入的假設，**不構成任何投資建議**。不要直接拿模型的預測決定真錢怎麼投資。
