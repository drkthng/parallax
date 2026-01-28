# ANTIGRAVITY AGENT CONTEXT (PARALLAX PROJECT)

> **CRITICAL INSTRUCTION:** All Agents must read this file before writing a single line of code.
> This file contains the "Blood Written Rules"—solutions to problems that killed previous agents.

## 1. Architectural Invariants (DO NOT BREAK)
- **Data Engine:** WE ONLY USE POLARS. `import pandas` is strictly forbidden.
- **UI Thread:** Never run `CorrelationEngine` calculations on the main UI thread. Use `threading` or `asyncio` wrappers.
- **Type Safety:** All core logic functions must have full type hinting (`series: pl.Series`).

## 2. The Graveyard (Problems & Solutions)
*Document every "Hallucination" or "Crash" here.*

### [Solved] Polars vs. Flet Threading
- **Problem:** The app froze when clicking "Calculate" on large datasets.
- **Cause:** Polars releases the GIL, but Flet's `on_click` is synchronous.
- **Solution:** We implemented `run_in_background` decorator in `src/utils/async_tools.py`. USE IT for all button clicks.

### [Solved] Norgate Mocking
- **Problem:** Agent tried to import `norgatedata` library which isn't installed in CI/CD.
- **Solution:** Use `MockLoader` interface in `src/data/loader.py` for all dev environments. Only load real drivers if `os.getenv("LIVE_TRADING")` is True.

### [Solved] Plotly Memory Leak
- **Problem:** Re-creating `ft.PlotlyChart` controls caused RAM spikes.
- **Solution:** Do not recreate the control. Create it once in `__init__` and only update `chart.figure` property.

### [Solved] Windows Shell Execution (uv/pytest)
- **Problem:** Running `uv run pytest` or `pytest` failed even if installed.
- **Cause:** Windows shell doesn't always inherit the `uv` path correctly in this environment.
- **Solution:** Use explicit venv path: `.venv/Scripts/python.exe -m pytest <path>`.

### [Solved] Polars Scalar Extraction
- **Problem:** `TypeError: float() argument must be a string or a real number, not 'Expr'` or issues with `pytest.approx`.
- **Cause:** `pl.corr()` and other Polars functions return an `Expr`, not a scalar, when called directly.
- **Solution:** Wrap in `pl.select(...).item()` to extract the scalar value for use in pure Python/Tests.