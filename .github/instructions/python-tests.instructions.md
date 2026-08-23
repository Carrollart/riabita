---
description: "Guidance for writing and reviewing Python tests in the tests directory."
applyTo: "tests/**/*.py"
---

# Python Test Guidance

- Test observable behavior and meaningful contracts rather than implementation details.
- Keep tests small, isolated, deterministic, and safe to run repeatedly.
- Cover the normal path, important boundary values, invalid input, and expected failure behavior where relevant.
- Use descriptive test names that state the scenario and expected outcome.
- Prefer simple local fixtures and test data. Avoid network calls, real credentials, machine-specific paths, and dependence on execution order.
- Mock or replace external systems only at the boundary where they are used, and verify important interactions without over-specifying incidental calls.
- Keep test setup close to the tests that use it unless a shared fixture genuinely improves clarity.
- Update tests when behavior changes, and remove assertions that no longer describe the supported contract.
- Run the narrowest relevant test command first, then the broader project checks when they are configured.