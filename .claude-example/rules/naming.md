# Naming Conventions

Consistent names reduce cognitive load and help ruff lint rules (E, F, I, B, UP) pass without surprises.

## Python

| Kind                    | Convention               | Example                               |
| ----------------------- | ------------------------ | ------------------------------------- |
| Functions and variables | `snake_case`             | `estimate_cost`, `ticket_id`          |
| Classes                 | `PascalCase`             | `SupportTriageAgent`, `CostBreakdown` |
| Constants               | `SCREAMING_SNAKE_CASE`   | `DEFAULT_TIMEOUT`, `MAX_RETRIES`      |
| Test files              | `test_<module>.py`       | `test_cost_calculator.py`             |
| Test functions          | `test_<what>_<scenario>` | `test_estimate_cost_unknown_model`    |

## Git

- **Branches**: `<type>/<issue-number>-<short-description>` — e.g. `feature/31-claude-example`
- **Commits**: [Conventional Commits](https://www.conventionalcommits.org/) — `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`

## General

- No abbreviations in public API names (`calculate` not `calc`, `configuration` not `cfg`)
- Short, single-purpose functions are preferred over long ones
- File names: `snake_case.py` (never camelCase or PascalCase for files)
