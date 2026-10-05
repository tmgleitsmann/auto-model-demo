# Task: add due dates to the todo CLI

`todo.py` is a small todo CLI. Extend it with due dates:

1. `add "title" --due YYYY-MM-DD` - store an ISO due date on the task; reject invalid dates with a clear error and exit code 1. Without `--due`, behavior is unchanged.
2. `list --sort due|created` - sort by due date (tasks without a due date last) or by creation time (default, current behavior).
3. `list --overdue` - show only tasks that are due before today and not done.
4. Unit tests for all of the above in `test_todo.py` (standard-library `unittest` only; no new dependencies). Tests must not leave a `.todo.json` behind in this directory - run them in a temporary working directory and clean up.
5. Update `README.md` to document the new options.

Keep the existing commands working as documented in `README.md`.
