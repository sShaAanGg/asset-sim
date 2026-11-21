# ADR 0001: Learning path (學習路線)

- Status (狀態): **Proposed**
- Date: 2026-11-21

## Context (背景)

[plan.md](../../plan.md) has me derive the math and implement each model by hand in numpy before using a library. Phase 0 code is done; its exercises are in progress.

1. I find AI infrastructure, software and system design more interesting than the math basics.
2. Ignoring the math basics entirely may leave me unable to understand and verify the code an AI writes for me.

## Options (選項)

| Option | What I would learn | Pros | Cons |
|---|---|---|---|
| A. Original plan: derive the math, implement by hand | Probability, statistics and ML math, in depth | Deepest understanding of the models | Slowest; little practice in engineering (performance, concurrency, verification tooling) |
| B. Middle ground (折衷): the AI implements, I write the spec and properties first, and learn the math when I can't | Reading unfamiliar code, accepting work by spec and tests, statistical testing, as much math as each feature needs | Fast; math learned in a concrete context sticks better; stronger motivation | Shallower math; if I stop writing properties first, it degrades into watching the AI write code |
| C. asset-sim as an engineering playground (工程練習場) | Profiling, vectorization (向量化), Numba, multiprocessing, Hypothesis and mutmut | CI and tests already exist, so I can start right away | Needs the phase 1 Monte Carlo before there is a heavy enough workload; the GIL rules out real concurrency practice |

## Decision (決定)

Proposed: take **B** first, then add **C**.

Under B, every feature and bug fix follows this gate:

1. Before any implementation, I write down what "correct" means, in a spec at `specs/<feature>.md`: the interface, and the expected properties or rough values.
   - Claude reviews the properties.
   - I check each one against an extreme setting where the answer is known (zero volatility, very large N, zero return), so it doesn't rest on anyone's judgment alone.
2. If I can't write them, I learn the math needed first.
3. The AI implements the change and its tests.
4. I review the change and decide whether it can be merged.

## Consequences (影響)

- The math stays shallower than plan.md intends. Phases 4–6 (regression, HMM, deep learning) carry the most risk: data leakage (資料洩漏) and look-ahead bias (前視偏差) produce code that runs and backtests well but is wrong, so those phases need more math and methodology up front.
- C starts once phase 1 gives a workload heavy enough to optimize.
- Neither B nor C covers concurrency (並行) beyond multiprocessing, because of the GIL.
- If this is accepted, plan.md needs updating to match.

## How this gets decided

Before starting phase 1, I write two or three properties I expect of the Monte Carlo simulation without reading any material first. If I can write them, or can learn what I'm missing quickly, mark this ADR **Accepted**. If not, revisit the options.
