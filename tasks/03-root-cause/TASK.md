# Task: root-cause a cent discrepancy

Run the tests:

    python3 -m unittest -q test_invoice.py

At least one test fails by exactly one cent. The bug is in the money math in `invoice.py`.

1. Find the root cause and write a short `ROOT_CAUSE.md` (a few sentences: what is wrong, and why it produces cent-level errors).
2. Fix `invoice.py` so every test passes. The standard library is enough; no new dependencies. Keep the public API unchanged (same function names, float inputs, float outputs).
3. Re-run the test suite to confirm everything passes.
