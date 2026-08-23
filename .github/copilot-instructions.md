# Repository Instructions

## Working Practices

- Inspect the relevant existing files and nearby tests before making changes.
- Preserve user changes and avoid modifying unrelated files.
- Prefer the smallest clear change that solves the request.
- Keep public APIs and existing behavior stable unless the task explicitly requires a change.
- Do not add dependencies when the standard library or existing project code is sufficient.
- Use the repository's virtual environment and established commands when they are available.
- If the project does not document a tool or convention, make the least-assumptive choice and record important assumptions.

## Validation

- Add or update focused tests when behavior changes.
- Run the narrowest relevant test, lint, format, or type-check command after editing.
- Report what was validated and call out checks that were unavailable or not configured.
- Keep generated files, caches, credentials, and local environment files out of source control.