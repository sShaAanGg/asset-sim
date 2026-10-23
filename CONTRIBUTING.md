# Contributing（貢獻指南）

How changes get into `main`, and the policy for the CI gate（CI 關卡）that guards it.

## How changes get into `main`

1. Create a branch from the latest `main`.
2. Commit, and run the tests locally (see [Running CI locally](#running-ci-locally)).
3. Push and open a pull request（PR）. Open it as a draft（草稿） while the work is in progress, if you like; CI runs on drafts too.
4. Merge once the `test` check is green and the branch is up to date with `main`.

Nobody pushes straight to `main`, including the repo owner.

## What the gate enforces

The `pytest` ruleset（規則集）on the default branch (Settings → Rules → Rulesets):

| Rule | Setting | What it means |
|---|---|---|
| Require a pull request before merging | 0 required approvals | Every change goes through a PR. Approvals aren't required because GitHub doesn't let you approve your own PR |
| Require status checks to pass | `test`, from GitHub Actions | The PR can't be merged until the `test` job passes on its latest commit |
| Require branches to be up to date | On | If `main` has moved on, update the branch (which re-runs `test`) before merging |
| Restrict deletions | On | `main` can't be deleted |
| Bypass list | Empty | No one can skip the rules |

## What CI runs

The workflow is [`.github/workflows/ci.yml`](.github/workflows/ci.yml): one job, `test`, on Ubuntu with Python 3.12 (from `.python-version`).

1. `uv sync --locked --no-group ml`: installs the exact versions in `uv.lock`, without the `ml` group (PyTorch + CUDA, several GB, which no test needs).
2. `uv run --no-sync pytest`: runs every test in `tests/`.

### When it runs

| Event | Runs? |
|---|---|
| Opening, reopening, or pushing to a PR (drafts included) | Yes |
| Clicking **Update branch**, or merging/rebasing `main` into the branch and pushing | Yes |
| Marking a draft **Ready for review** | No new run is needed: the latest commit already has a result |
| Pushing to `main` (i.e. merging a PR) | Yes, as a final check of `main` itself |
| A commit message containing `[skip ci]` | No, and the required check stays pending, so the PR can't be merged until a later push runs it |

To re-run by hand: **Re-run jobs** on the PR's Checks tab, or `gh run rerun <run-id>`.

## Running CI locally

Run the same steps CI does before pushing:

```bash
uv sync --locked --no-group ml && uv run --no-sync pytest
```

During day-to-day work, `uv run pytest` is enough. Note that it reinstalls the `ml` group because of `default-groups`.

## Policy（政策）

1. **A red check is never merged.** Fix the code or the test. Don't weaken, skip or delete a test just to get the check green; if a test is genuinely wrong, say why in the PR.
2. **New behaviour comes with tests.** Bug fixes come with a test that would have caught the bug.
3. **`uv.lock` stays in sync.** After changing dependencies in `pyproject.toml`, run `uv lock` and commit the lockfile; otherwise `--locked` fails the build.
4. **Tests stay fast and offline.** The suite takes about a second. Tests must not download data or need a GPU; use small fixtures under `tests/` instead.
5. **Tests that need PyTorch get their own job.** When stage 6 adds them, mark them (e.g. `@pytest.mark.ml`) and run them in a separate job with the `ml` group, rather than adding PyTorch to the `test` job.
6. **Changes to the gate go through a PR.** Changing `ci.yml`, the job name or the ruleset needs a PR that also updates this file. Renaming the `test` job breaks the required check: update the ruleset in the same change.
7. **Action versions are pinned.** `astral-sh/setup-uv` has no floating major tag, so it's pinned to an exact version (`v10.3.2`). Bump it on purpose, in its own PR.

## When CI fails

| Failure | Likely cause | Fix |
|---|---|---|
| `Unable to resolve action` | An action version or tag that doesn't exist | Use a tag listed on the action's releases page |
| `uv sync` fails with a lockfile error | `pyproject.toml` changed without `uv lock` | Run `uv lock` and commit `uv.lock` |
| A test fails in CI but passes locally | Your local environment has something CI doesn't (an extra package, local `data/`, the `ml` group) | Reproduce with the commands in [Running CI locally](#running-ci-locally) |
| The check stays at "Expected — waiting" | The workflow didn't run (e.g. `[skip ci]`, or the branch predates the workflow) | Push a new commit, or update the branch from `main` |
