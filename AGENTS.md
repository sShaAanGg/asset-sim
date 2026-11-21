# AGENTS.md

asset-sim is a personal asset growth simulator and a project for learning ML and the math behind it. See [README.md](README.md) for the layout and [plan.md](plan.md) for the learning plan.

Before changing anything, read the docs in [docs/](docs/): they hold the repo's conventions, and [docs/adr/](docs/adr/) holds the decisions behind them.

The ADRs are the source of truth. The rules below summarize them; if a rule here disagrees with an ADR, follow the ADR and point out the mismatch so this file can be fixed.

## Rules

1. **Record major decisions as an ADR** (Architecture Decision Record) in `docs/adr/`, numbered in order (`0002-<topic>.md`, ...), with a status of Proposed, Accepted or Superseded. Follow the format of [0001](docs/adr/0001-learning-path.md).
2. **Every change goes through a pull request.** Never push to `main`. The gate is described in [docs/continuous-integration.md](docs/continuous-integration.md).
3. **The user writes the spec before you implement** (see [ADR 0001](docs/adr/0001-learning-path.md)). Before implementing a feature or fixing a bug, the user writes down what "correct" means in `specs/<feature>.md`, one file per feature, with the headings of [specs/monte-carlo.md](specs/monte-carlo.md). The spec's interface and properties (expected behavior or rough values) are the user's to write, not yours.
   - You may create a new spec file with the headings, a one-line summary and a draft Goal. Everything below Goal is the user's.
   - If the spec is missing or empty, ask for it before you start.
   - You may review the spec and ask questions that expose gaps, but don't fill the gaps yourself.
   - When the user says the spec is done, quiz them on it and the math behind it. Don't implement until they pass.
   - Then implement the change and its tests against the spec.
   - After implementing, quiz the user on the implementation before they review it.
   - To pass either quiz, the user needs 80% of the answers right and every key question right. When you set a quiz, mark the key questions: the ones the user must understand. For each wrong answer, the user learns the missing math in the notebook or discusses it with you, until you judge they understand it.

## Language and punctuation

- **Language:**
  - `docs/`, `specs/` and `AGENTS.md` are in English. Put the Chinese term in parentheses next to key concepts and headings, e.g. "Lazy migration (延遲遷移)".
  - `README.md`, `plan.md`, notebooks, code comments and UI text are in Chinese, with the English term in parentheses next to key concepts.
- **Punctuation:**
  - Use ASCII punctuation (`,` `.` `:` `;` `!` `?` `()`), including in Chinese text, never the full-width forms (`，` `。` `：` `（）`).
  - Put a space between CJK text and parentheses, e.g. `複利 (compound interest)`.
