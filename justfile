# clearance dev commands. Run `just` to list them.

default:
    @just --list

# Deterministic checks on the skills and the eval harness (no model)
test *args:
    uv run --with pytest pytest -q {{ args }}

# Run the evals against the real skills (costs tokens). e.g. `just eval --case setup-approve-off`
eval *args:
    python3 tests/evals/run.py {{ args }}
