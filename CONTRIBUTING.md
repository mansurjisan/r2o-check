# Contributing to r2o-check

## Development Setup

```bash
git clone https://github.com/mansurjisan/r2o-check.git
cd r2o-check
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest                              # all tests
pytest --cov=r2o_check              # with coverage
ruff check src/ tests/              # linting
mypy                                # type checking
r2o-check lint .                    # self-check
```

## Adding a New Rule

1. Choose the correct module in `src/r2o_check/rules/`.
2. Write the rule function with signature `(repo_path: Path, config: Config) -> list[LintResult]`.
3. Decorate with `@register_rule(applies_to=...)` using the Repo Type Rule Matrix in CLAUDE.md.
4. Add a docstring starting with the rule ID: `"""R2OXXX001 — Description."""`
5. Cite the NCO v11.0 section in the docstring and in result messages.
6. Add tests in the matching `tests/test_*.py` file.
7. Add fixtures in `tests/fixtures/` if needed.
8. Document in `docs/rules.md` with severity, NCO section, rationale, example, fix.
9. Update `docs/nco-standards-mapping.md`.

## Rule ID Convention

`R2O<CATEGORY><NNN>` where category is:
- STR: structure, NAM: naming, ENV: environment
- BLD: build, MOD: modules, VER: versions, ECF: ecflow

## PR Checklist

- [ ] All tests pass (`pytest`)
- [ ] ruff clean (`ruff check src/ tests/`)
- [ ] mypy clean (`mypy`)
- [ ] Coverage >= 85%
- [ ] Self-check passes (`r2o-check lint .`)
- [ ] New rules documented in `docs/rules.md`
- [ ] CHANGELOG.md updated
