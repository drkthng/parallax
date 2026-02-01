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

### [Solved] Norgate Data Integration
- **Problem:** Norgate Data SDK import failed when not installed or when Norgate Data Updater is not running.
- **Solution:** 
  1. `NorgateLoader` now checks both SDK availability AND database connection status.
  2. `DataFactory.get_loader_safe()` provides graceful fallback to `MockLoader` with warning message.
  3. Symbol mapping in `NorgateLoader` translates common aliases (e.g., "Index" → "$SPX").
  4. Dashboard displays warning when fallback occurs (orange warning banner).
- **Usage:** Install `norgatedata` via pip. Ensure Norgate Data Updater is running for live data.

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

### [Solved] Settings Persistence
- **Problem:** User configuration (data source, assets, weights) was lost on restart.
- **Solution:** Implemented `src/utils/settings.py` (JSON-based).
- **Mechanism:** `SettingsManager` loads/saves to `data/settings.json`.
- **Usage:** Toggle "Remember Settings" in the UI to enable auto-save.
- **Invariant:** `asset_a` (Target) is now dynamic and stored in settings, allowing custom tickers.

## 5. Final Project Summary (Synthesis)

### The Great Pivot: Flet to Solara
- **The "Build Hell":** We started with Flet to build a native .EXE. It was a disaster. Packaging complications (`flet pack`), DLL missing errors, and the "White Screen of Death" plagued development.
- **The Solution:** We realized the browser *is* the best runtime. Solara allows us to write pure Python (no JS required) and deploy as a web app.
- **Native Feel:** By using the browser's `--app` flag (in `run_parallax.bat`), we strip the address bar and navigation controls, giving the user a native-like windowed experience without the compilation nightmare.

### The Stack: Why This Won
- **Polars Supremacy:** We rejected Pandas. Polars gives us speed, lazy evaluation, and strict schema enforcement.
  - *Quirk:* Scalars are `Expr` objects. We learned to use `.item()` to extract raw floats for the UI/Math.
- **Solara State:** `solara.reactive` provided the "glue" between our heavy Quant logic (Drift/Correlation) and the UI. It eliminated the complex event loops we fought in Flet.
- **Launcher Magic:** The `run_parallax.bat` is the unsung hero. It handles environment activation, port conflict resolution (stopping zombies), and the native-app launch sequence in one double-click.

## 6. Technical Appendix: Solara Pattern Library (Latest Fixes)

### [Solved] Solara Watermark Removal (The "Atom Bomb" Method)
- **Problem:** "This website runs on Solara" footer persisted despite standard CSS fixes.
- **Cause:** Solara/Vuetify dynamically renders this element, sometimes bypassing static CSS or overriding it.
- **Solution:** A 3-pronged approach is required:
  1. **Settings API:** Set `solara.server.settings.theme.show_banner = False`.
  2. **Environment:** Set `SOLARA_THEME_SHOW_BANNER=False` in the launcher.
  3. **DOM Hunter:** Inject a JS script that aggressively polls for the specific text and hides the element.

### [Solved] Responsive Layouts in Solara
- **Problem:** Need different layouts for Desktop (Side-by-Side) vs. Mobile (Sidebar) without complex media queries.
- **Solution:** Use **Vue/Vuetify classes** directly on `solara.Column`.
  - Mobile: `classes=["d-md-none"]` (Hidden on Medium+ screens).
  - Desktop: `classes=["d-none", "d-md-block"]` (Hidden on Small, Block on Medium+).
  - Define a reusable renderer function (e.g., `render_stats_table`) to call in both branches.

### [Solved] "Busy Button" State Lock
- **Problem:** Buttons relying on async actions stayed "Loading" forever if an exception occurred.
- **Solution:** ALWAYS use a `finally` block to reset the loading reactive variable (`is_loading.set(False)`). Pure `except` blocks are insufficient if the error handling itself crashes or returns early.

### [Solved] Mixed Data Sources (Routing)
- **Problem:** User needed some assets from Yahoo and others from Norgate in the same portfolio.
- **Solution:** Implemented `source_overrides = solara.reactive({})`.
  - Default: `data_source` (Global).
  - Function: `resolve_loader(symbol)` checks the override map first, then falls back to global.