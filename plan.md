# 學習計畫

每個階段替模擬器加一個新功能，並學一個數學 / ML 主題。

## 原則

1. **先用 numpy 手刻，再用套件**(scikit-learn、PyTorch)：手刻一次，數學才會真的懂。
2. **每個模型都要和簡單的基準 (baseline) 比較**，例如「直接用歷史平均」：贏不過基準，就代表模型沒學到東西。
3. **用兩種方法驗證**：模擬 vs 封閉解 (closed-form solution)、手刻 vs 套件，結果一致才算對，並寫成測試。
4. **金融資料雜訊很大 (low signal-to-noise ratio)**：模型預測的結果不要直接拿來決定真錢怎麼投資。

## 總覽

| 階段 | 模擬器功能 | 數學 / ML | 狀態 |
|---|---|---|---|
| 0 | 固定報酬率的現金流模擬 (deterministic cash-flow simulation) | 複利 (compound interest)、等比級數 (geometric series) | 🟡 程式完成，練習題進行中 |
| 1 | 蒙地卡羅模擬 (Monte Carlo simulation)，畫出 P10/P50/P90 區間 | 機率分布 (probability distribution)、對數報酬 (log return)、期望值與變異數 (expectation & variance)、大數法則 (law of large numbers) | ⬜ |
| 2 | 多資產相關性 (multi-asset correlation) | 共變異數矩陣 (covariance matrix)、Cholesky 分解 (Cholesky decomposition) | ⬜ |
| 3 | 從歷史資料估計參數、處理肥尾 (fat tails) | 最大概似估計 (maximum likelihood estimation, MLE)、t 分布 (Student's t-distribution)、bootstrap | ⬜ |
| 4 | 手刻線性迴歸 (linear regression) 預測波動度 (volatility) | 梯度下降 (gradient descent)、正則化 (regularization)、walk-forward 驗證 | ⬜ |
| 5 | 判斷市場狀態 (market regime) | GARCH、隱馬可夫模型 (hidden Markov model, HMM)、EM 演算法 (expectation–maximization) | ⬜ |
| 6 | PyTorch 在 GPU 上跑 MLP / LSTM | 反向傳播 (backpropagation)、自動微分 (automatic differentiation, autograd) | ⬜ |
| 7 | 自動算出最佳配置比例 (optimal allocation) | 凸優化 (convex optimization)、拉格朗日乘數 (Lagrange multipliers)、平均數-變異數最適化 (mean-variance optimization) | ⬜ |

## 各階段細節

### 第 0 階段：複利與等比級數 (compound interest & geometric series)

- 產出：`src/assetsim/cashflow.py`、`formulas.py`、`notebooks/00_compound_interest.ipynb`、`app.py`
- 概念：
  - 指數成長 (exponential growth)、終值 (future value, FV)
  - 等比級數求和 (sum of a geometric series)、年金 (annuity)
  - 有效利率 (effective rate) vs 名目利率 (nominal rate)
  - 72 法則 (rule of 72)、泰勒近似 (Taylor approximation)$\ln(1+i) \approx i$
  - 敏感度分析 (sensitivity analysis)、模擬 vs 封閉解
- 先修：3Blue1Brown〈What's so special about Euler's number e?〉、〈Taylor series〉
- 完成條件：
  - [x] 逐月現金流模擬，並用封閉解驗證 (測試)
  - [x] Streamlit 介面
  - [ ] 練習題 1：72 法則的誤差曲線
  - [ ] 練習題 2：達成 1,000 萬要幾年 (用對數解 $n$)
  - [ ] 練習題 3：推導成長年金 (growing annuity) 公式
  - [ ] 練習題 4：用 `Params.inflation` 輸出實質購買力 (real purchasing power) 欄位 `real_total`(含測試)
  - [ ] 練習題 5：比較再平衡 (rebalancing) 開 / 關

### 第 1 階段：蒙地卡羅模擬 (Monte Carlo simulation)

- 產出：`notebooks/01_monte_carlo.ipynb`、`src/assetsim/montecarlo.py`，介面加上 P10/P50/P90 區間圖
- 概念：
  - 隨機變數 (random variable)、期望值 (expected value)、變異數 (variance)、標準差 (standard deviation)
  - 常態分布 (normal / Gaussian distribution) vs 對數常態分布 (log-normal distribution)：為什麼價格不會變負數
  - 算術平均 (arithmetic mean) vs 幾何平均 (geometric mean)、波動拖累 (volatility drag)：中位數年化報酬 ≈ $\mu - \sigma^2/2$
  - 百分位數 (percentile)、中位數 (median)
  - 大數法則 (law of large numbers, LLN)、中央極限定理 (central limit theorem, CLT)、蒙地卡羅誤差 $\propto 1/\sqrt{N}$(標準誤，standard error)
  - numpy 向量化 (vectorization)、`@st.cache_data`
- 先修：Seeing Theory 第 1–3 章、《Think Stats》前幾章、3Blue1Brown〈But what is the Central Limit Theorem?〉
- 完成條件：
  - [ ] 向量化的蒙地卡羅模擬，波動度設為 0 時要等於第 0 階段的結果 (測試)
  - [ ] 驗證：模擬平均值收斂 (converge) 到理論期望值，誤差符合 $1/\sqrt{N}$
  - [ ] 介面顯示分布區間，以及「達成目標的機率」
  - [ ] 回答：再平衡在有波動時有什麼影響？

### 第 2 階段：多資產相關性 (multi-asset correlation)

- 概念：共變異數 (covariance)、相關係數 (correlation coefficient)、共變異數矩陣、矩陣分解 (matrix decomposition)、Cholesky 分解、產生相關的隨機變數 (correlated random variables)、分散投資 (diversification) 的數學
- 先修：3Blue1Brown〈Essence of Linear Algebra〉
- 完成條件：
  - [ ] 產生的樣本，相關係數要符合設定值 (測試)
  - [ ] 比較相關性高 / 低時，投資組合的波動度

### 第 3 階段：從歷史資料估計參數 (parameter estimation)

- 概念：
  - 抽樣分布 (sampling distribution)、標準誤、信賴區間 (confidence interval)
  - 最大概似估計 (MLE)、概似函數 (likelihood function)、對數概似 (log-likelihood)
  - 肥尾 (fat tails)、峰度 (kurtosis)、t 分布、QQ 圖 (QQ plot)
  - bootstrap 重抽樣 (bootstrap resampling)
- 資料：yfinance 下載 0050.TW、VT 等 (存到 `data/`，不進 git)
- 先修：《Think Stats》估計相關章節、StatQuest 的 MLE 與 bootstrap 影片
- 完成條件：
  - [ ] 手刻 MLE，和 scipy 的結果比較
  - [ ] 比較常態分布 vs t 分布 vs 歷史 bootstrap，對 P10 的影響

### 第 4 階段：經典 ML — 預測波動度 (classical ML: volatility forecasting)

- 概念：
  - 線性迴歸、損失函數 (loss function)、均方誤差 (mean squared error, MSE)
  - 梯度下降、偏微分 (partial derivative)、梯度 (gradient)
  - Ridge 正則化 (ridge / L2 regularization)、過度擬合 (overfitting)、偏差-變異權衡 (bias–variance tradeoff)
  - 資料洩漏 (data leakage)／前視偏差 (look-ahead bias)、walk-forward 驗證 (walk-forward validation)
- 先修：3Blue1Brown〈Essence of Calculus〉的連鎖律 (chain rule)、ISLP 第 3、5、6 章
- 完成條件：
  - [ ] 用 numpy 手刻梯度下降，和 scikit-learn 的結果一致
  - [ ] 用 walk-forward 驗證，和「用過去波動度當預測」的基準比較

### 第 5 階段：市場狀態 (market regimes)

- 概念：波動聚集 (volatility clustering)、GARCH、馬可夫鏈 (Markov chain)、隱馬可夫模型 (HMM)、EM 演算法、貝氏定理 (Bayes' theorem)
- 先修：3Blue1Brown〈Bayes theorem〉、Stat 110 的馬可夫鏈單元
- 完成條件：
  - [ ] 找出牛市 / 熊市 (bull / bear market) 狀態，並用來產生更真實的模擬路徑

### 第 6 階段：深度學習 (deep learning, GPU)

- 概念：神經網路 (neural network)、多層感知器 (multilayer perceptron, MLP)、長短期記憶網路 (long short-term memory, LSTM)、反向傳播、自動微分、優化器 (optimizer：SGD / Adam)、訓練技巧
- 先修：3Blue1Brown〈Neural Networks〉第 1–4 集、Karpathy《Neural Networks: Zero to Hero》
- 完成條件：
  - [ ] 先手刻一個小型的反向傳播，再改用 PyTorch
  - [ ] 在 GPU 上訓練 MLP / LSTM，和第 4 階段的模型、基準比較

### 第 7 階段：最佳配置 (optimal allocation)

- 概念：凸優化、拉格朗日乘數、效率前緣 (efficient frontier)、mean-variance 的缺點 (對輸入很敏感，estimation error)
- 先修：《Mathematics for Machine Learning》第 7 章 (連續優化，continuous optimization)
- 完成條件：
  - [ ] 手刻兩資產的解析解 (analytical solution)，和數值優化 (numerical optimization) 結果比較
  - [ ] 介面上可以選「目標：最大化 P10」等不同目標

## 模型待補 (不屬於特定階段)

- [x] 手續費、證交稅、ETF 內扣費用 (expense ratio)
- [x] 股息 (dividend yield、配息頻率、再投入)、二代健保補充保費、股利所得有效稅率
- [x] 生活開銷 (隨通膨調整)、年終獎金、緊急預備金 (emergency fund)
- [ ] 股利所得稅完整計算：依綜所稅級距比較合併計稅 (8.5% 抵減) 與分開計稅 (28%)
- [ ] 海外 ETF (複委託)：股息預扣 30% 美國稅、匯率、複委託手續費
- [ ] 一次性大額支出 (買房、買車)、收入中斷 (轉職、育兒)
- [ ] 退休後的提領階段 (decumulation)：4% 法則 (4% rule)、報酬順序風險 (sequence-of-returns risk)

## 學習資源

### 機率統計 (probability & statistics)

| 資源 | 特色 | 用在哪裡 |
|---|---|---|
| **Seeing Theory**(布朗大學，互動網站) | 用動畫和拉桿操作機率統計概念，最直覺 | 第 1 階段前，最先開始 |
| **《Think Stats》**(Allen Downey，免費線上版) | 用 Python 學統計，以模擬為主、公式為輔，和這個專案的做法最接近 | 第 1、3 階段的主要教材 |
| **StatQuest**(Josh Starmer，YouTube) | 統計和 ML 概念講得非常白話，一支一個主題 | 全程，遇到不懂的概念就查 |
| **Harvard Stat 110**(Joe Blitzstein)＋《Introduction to Probability》(Blitzstein & Hwang，免費 PDF) | 最紮實的機率課，難度較高 | 想深入時；第 5 階段的馬可夫鏈 |

### 其他數學工具

| 資源 | 必看 | 用在哪裡 |
|---|---|---|
| **3Blue1Brown〈Essence of Calculus〉** | e、泰勒級數；第 4 階段前再看導數與連鎖律 | 第 0、1 階段 (對數報酬、波動拖累)；第 4、6 階段 |
| **3Blue1Brown 機率單集** | 中央極限定理、常態分布 (Why π is there…)、貝氏定理 | 第 1、5 階段 |
| **3Blue1Brown〈Essence of Linear Algebra〉** | 向量、線性變換 (linear transformation)、矩陣乘法、行列式 (determinant)、反矩陣 (inverse matrix)、內積 (dot product)、基底變換 (change of basis)、特徵向量與特徵值 (eigenvectors & eigenvalues)；可跳過外積 (cross product)、克拉瑪公式 (Cramer's rule) | 第 2 階段前 |
| **《Mathematics for Machine Learning》**(Deisenroth 等人著，官方免費 PDF) | 對應章節的習題 | 看完影片後練計算 |
| Khan Academy | 練習題 | 任何需要補基礎計算的時候 |

### ML

| 資源 | 用在哪裡 |
|---|---|
| **ISLP**(《An Introduction to Statistical Learning》Python 版) | 第 4 階段起，經典 ML 的主要教材 |
| **3Blue1Brown〈Neural Networks〉**第 1–4 集 | 第 6 階段前，建立直覺 |
| **Andrej Karpathy《Neural Networks: Zero to Hero》** | 第 6 階段，從零手刻反向傳播 |

### 看影片的方法

1. **看到一半就暫停，先猜下一步**，再繼續看。
2. **每看完一個主題，就用 numpy 驗證一次**，例如用程式算 $(1+\frac{0.07}{n})^n$ 看它怎麼收斂到 $e^{0.07}$。
3. **一定要搭配練習題**：只看影片會有「好像懂了」的錯覺。
