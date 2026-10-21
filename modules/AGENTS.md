# Module Rules

## TDD Workflow

- Every new feature, adapter, service, endpoint, and task must start with a failing test.
- Write tests that cover the public module API, not private helpers.
- For each acceptance criterion, create at least one focused test.
- Run the target tests first:

```bash
python -m unittest -v
```

- Add implementation only after the test fails.
- Keep behavior and adapters separated from transaction and payment logic.
- Every adapter must have a mock or test double for local testing.
- Every external integration must be testable without real hardware.
- Keep tests inside the module under `tests/`.
- Name test files using the `test_<feature>.py` pattern.

