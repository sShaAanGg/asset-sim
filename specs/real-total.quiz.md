# Quiz: Real total assets (實質總資產) spec

- Gate (關卡): spec quiz, before implementation (see [ADR 0001](../docs/adr/0001-learning-path.md))
- Spec: [real-total.md](real-total.md)
- Pass mark: at least 7 of 8 answers right (80%), and all 4 key questions right
- Key questions: 1, 2, 3 and 4, approved by me

| # | Property | Key? | Why it is key |
|---|---|---|---|
| 1 | P1 | ✅ | Computing a value from the definition, including the formula for t. Both the implementation and the tests rest on it. |
| 2 | P1, P3 | ✅ | The choice between option A (in sync with expenses) and option B (the price index steps up at month 12), and the boundary most likely to go wrong. |
| 3 | P2 | ✅ | Knowing what a property can and cannot catch. |
| 4 | P4 | ✅ | P4 checks the formula along an independent path; you need to know what it checks. |
| 5 | P4 | | |
| 6 | The math behind it | | |
| 7 | P1, the math behind it | | |
| 8 | Goal | | |

## Questions (題目)

**1.** With π = 2%, `total` at month 25 is 1,000,000. What is t? Roughly what is `real_total`?

Answer:

**2.** What is t at month 12, and at month 13? Why does the price index step up at month 13 rather than month 12?

Answer:

**3.** Why does P2 hold for **every** month? If the implementation got t wrong (e.g. `month // 12`), would P2 catch it? Why?

Answer:

**4.** Suppose someone changes `cashflow.py` so expenses rise **before** the month-12 row is recorded, and leaves the `real_total` code untouched. Which fails, P1 or P4? Why?

Answer:

**5.** Why does P4 exclude row 0?

Answer:

**6.** Why is the real rate of return (實質報酬率) $\frac{1+r}{1+\pi}-1$ rather than $r-\pi$? When does the gap between the two grow?

Answer:

**7.** Suppose the annual return r = π = 2%, with no income or expenses, only the initial assets. Under option A, what does `real_total` look like from month 0 to month 24?

Answer:

**8.** Two runs differ only in π (2% and 3%). At month 360, which has the lower `real_total`? How many causes contribute to the difference?

Answer:

## Grading (批改)

(Claude grades after all answers are in.)
