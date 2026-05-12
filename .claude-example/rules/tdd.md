# TDD Workflow

Default workflow for all implementation tasks. Skip only if the user explicitly requests otherwise.

## Red-Green-Refactor Cycle

1. Write a failing test first (Red) — cover the happy path and at least one error case
2. Run the test suite and confirm the test **fails** (`uv run pytest`)
3. Write the minimum code needed to make the test pass (Green)
4. Run the full fast suite again — fix any regressions before continuing
5. Refactor for clarity without breaking tests (Refactor)
6. Repeat for the next test case

## Non-Negotiable

- Never write implementation code before a test exists
- Never skip the Red phase — tests must fail first
- Run `uv run pytest -m "not integration and not e2e"` after every implementation change, not just the new test
- Integration and e2e tests run on CI, not locally during the cycle

## Why

Writing tests first makes intent explicit, catches regressions early, and keeps the implementation to exactly what is needed — nothing more.
