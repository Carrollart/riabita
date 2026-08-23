---
description: "Guidance for implementing and reviewing Python source files."
applyTo: "**/*.py"
---

# Python Source Guidance

- Follow the surrounding project's Python version, style, and module structure when they are established.
- Prefer readable, direct code and clear names over clever or unnecessarily abstract solutions.
- Keep functions and classes focused on one responsibility with explicit inputs and outputs.
- Add type annotations where they clarify an interface or prevent ambiguity; keep annotations accurate and maintainable.
- Handle expected errors deliberately. Do not catch broad exceptions unless there is a clear recovery or reporting strategy.
- Avoid hidden global state, surprising side effects, and mutable default arguments.
- Use standard-library functionality when it is sufficient. Add a third-party dependency only when it provides meaningful value and fits the project's dependency workflow.
- Keep configuration and secrets outside source code. Do not log credentials, tokens, or sensitive personal data.
- Preserve the project's formatting and import ordering. Use configured formatters, linters, and type checkers when present rather than introducing new tools by default.
- Prefer deterministic behavior and make I/O, time, randomness, and external services easy to isolate in tests.

# Python coding standards

- Follow the PEP 8 style guide.
- Use type hints for all function signatures.
- Write docstrings for public functions.
- Use 4 spaces for indentation.