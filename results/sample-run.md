# Auto Model demo - routing report

_Real run, captured 2026-10-05 with Droid CLI 0.213.0 on Auto Model. The router decides per request, so your run will differ; that variance is part of the story._

_Generated 2026-10-05 17:50 UTC by `run_demo.py`._

Each row is one task run through `droid exec`. **Models** lists the model
that served each step, as recorded in the session transcript.

## Model: `auto`

| Task | Tier | Turns | Models (steps) | Credits | Wall time | Verify |
|---|---|---|---|---|---|---|
| 01-mechanical-edit | routine | 4 | `gpt-5.6-luna` x4 | 5,504 | 24.1s | pass |
| 02-bug-fix | debugging | 4 | `deepseek-v4-flash-0731` x4 | 5,921 | 21.7s | pass |
| 03-root-cause | reasoning | 5 | `deepseek-v4-flash-0731` x5 | 8,029 | 43.7s | pass |
| 04-feature-build | agentic | 10 | `claude-opus-5` x10 | 229,706 | 144.7s | pass |

**Total credits: 249,160**

### 01-mechanical-edit (`auto`)

- Router: `auto`
- `gpt-5.6-luna` x4, provider `snowflake`, effort `xhigh`
- Files changed: `greeting.py`
- Session: `078a095a-ba68-42ac-a43c-a836fcd333c3` - inspect with `droid --resume 078a095a-ba68-42ac-a43c-a836fcd333c3`
- Final message: Updated `greet()` and `farewell()` with `str` type hints and one-line docstrings.  Validation passed:  ```text Ran 2 tests ... OK ```

### 02-bug-fix (`auto`)

- Router: `auto`
- `deepseek-v4-flash-0731` x4, provider `fireworks`, effort `high`
- Files changed: `business_days.py`
- Session: `2f098ce7-fcc6-4804-8d92-244b14eb6bec` - inspect with `droid --resume 2f098ce7-fcc6-4804-8d92-244b14eb6bec`
- Final message: Fixed. The off-by-one in the weekday filter counted Saturday (weekday 5) as a business day; changing `day.weekday() <= 5` to `day.weekday() < 5` restricts the count to Monday–Friday. All 4 tests pass.

### 03-root-cause (`auto`)

- Router: `auto`
- `deepseek-v4-flash-0731` x5, provider `fireworks`, effort `high`
- Files changed: `ROOT_CAUSE.md`, `invoice.py`
- Session: `158a1d7e-d327-4166-8e9b-f7d0ee708aef` - inspect with `droid --resume 158a1d7e-d327-4166-8e9b-f7d0ee708aef`
- Final message: All tests pass.  ## Root cause  `invoice.py` did money math with binary `float` and Python's built-in `round()`. Two things go wrong:  1. **Binary floats can't represent most decimal cents exactly.** `2.675` is stored as `2.6749999999999998

### 04-feature-build (`auto`)

- Router: `auto`
- `claude-opus-5` x10, provider `snowflake`, effort `high`
- Files changed: `README.md`, `test_todo.py`, `todo.py`
- Session: `10a9622c-28a3-487f-83ec-b684622955cd` - inspect with `droid --resume 10a9622c-28a3-487f-83ec-b684622955cd`
- Final message: Due dates are implemented, tested, and documented. All 18 tests pass and the directory is left clean (no `.todo.json`, no `__pycache__`).  **`todo.py`** - `add "title" --due YYYY-MM-DD` validates with `datetime.strptime`, so both malformed 
