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

### [Solved] Polars DataFrame Comparison
- **Problem:** `AttributeError: 'DataFrame' object has no attribute 'frame_equal'`.
- **Cause:** Newer Polars versions use `df.equals(other)` for boolean comparison.
- **Solution:** Use `df.equals(other)` for simple assertions, or `pl.testing.assert_frame_equal(df, other)` for detailed test failures.

### [Solved] Artifact Creation Tooling
- **Problem:** `write_to_file` failed with "artifact metadata is required when IsArtifact is true".
- **Cause:** Setting `IsArtifact: true` requires `ArtifactMetadata` object with `ArtifactType` and `Summary`.
- **Solution:** Always provide `ArtifactMetadata` when creating or updating artifacts via `write_to_file`.

### [Solved] Flet UserControl AttributeError
- **Problem:** `AttributeError: module 'flet' has no attribute 'UserControl'`.
- **Cause:** Flet v0.21+ deprecated `UserControl`.
- **Solution:** Inherit directly from `ft.Column`, `ft.Row`, or `ft.Container` and define controls in `__init__`.

### [Solved] ModuleNotFoundError on Execution
- **Problem:** Running `src\main.py` directly caused `ModuleNotFoundError: No module named 'src'`.
- **Cause:** Python script execution context and package structure.
- **Solution:** Created `__init__.py` files and added `sys.path` logic in `main.py`. Execute as module: `python -m src.main`.

## 4. Tech Stack Pivot: Flet to Solara (Jan 2026)

### [Solved] Solara Startup: Timeout & Zombie Processes
- **Problem:** `python -m solara` sometimes hangs or fails to bind quickly, causing timeouts. Old processes lock port 8501.
- **Solution:** 
    1. **Auto-Kill:** `run_parallax.bat` automatically kills any process on port 8501 using `stop_parallax.bat`.
    2. **PowerShell Check:** Replaced flaky `netstat` checks with `New-Object Net.Sockets.TcpClient` for robust port detection.
    3. **Windowless:** Run via `start /MIN cmd` to keep logs reliable while hiding the console.

### THE ASSETS (KEEP THESE)
- **Logic:** `src/core/stats.py` is perfect. The Polars math and `CorrelationEngine` are stack-agnostic. DO NOT REWRITE.
- **Data:** `src/data/loader.py` and the `MockLoader` protocol are perfect. Keep the interfaces as they are.
- **Tests:** All `pytest` files for core and data layers remain valid.

### THE CHANGES (REPLACE THESE)
- **UI Framework:** We are moving from Flet to **Solara**.
- **Execution Model:** Instead of a native EXE build, we use a "Local Browser App" model.
- **State Management:** Use Solara's reactive variables (`solara.reactive()`) instead of Flet's page state.

### REUSE PROTOCOL
- When building the new UI, import the existing `CorrelationEngine` and `MockLoader`. 
- Focus only on the **Solara Component Tree**.

### [Solved] Plotly Express vs. Polars (No Pandas Rule)
- **Problem:** `plotly.express` functions require `pandas` or `pyarrow` even when passing dictionaries.
- **Cause:** Express has hard dependencies for internal data frame handling.
- **Solution:** Use **`plotly.graph_objects`** (`go.Scatter`, etc.) with `polars.Series.to_list()`. It is dependency-free and adheres to the "No Pandas" rule.

### [Solved] PowerShell Command Chaining
- **Problem:** `git add . & git commit` fails in PowerShell.
- **Cause:** `&` is a Call Operator in PowerShell, not a command separator like in Bash (`&&` or `;`).
- **Solution:** Execute commands sequentially as separate tool calls, or use `;` if absolutely necessary (but separate calls are safer).