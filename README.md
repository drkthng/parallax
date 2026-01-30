# Parallax

> **"Synthesize the Underlying. Minimize the Drift."**

### The Concept
In astronomy, **Parallax** is the displacement or difference in the apparent position of an object viewed along two different lines of sight.

In quantitative finance, we face a similar phenomenon:
1.  **The Object:** The True Price (e.g., The Bitcoin Index).
2.  **Observer A:** The Direct Underlying (The Index itself).
3.  **Observer B:** The Proxy Portfolio (e.g., MSTR + COIN).

The difference between these two views is **Tracking Error** (Drift).

**Parallax** is a desktop tool built to measure, visualize, and minimize this displacement. It allows traders to construct synthetic proxies for assets they cannot trade directly, optimizing the weighting of available equities to create a "perfect" mirror of the target.

### The Stack (2026 Edition)
We prioritize local performance, strict typing, and browser-based reactivity.

*   **GUI:** [Solara](https://solara.dev) - React-based Python web framework.
*   **Data Engine:** [Polars](https://pola.rs) - Rust-based DataFrame library. Replaces Pandas for speed and strict schema enforcement.
*   **Math:** `scipy.optimize` (SLSQP/Minimize) for solving weight allocations.
*   **Environment:** Windows (Native Executable via Browser App Mode).

### Architecture
*   `src/core`: Pure logic and math. 100% covered by `pytest`.
*   `src/data`: Interface adapters for Norgate Data and CSV ingestion.
*   `src/app.py`: Main Solara application entry point.

### Usage

**1. One-Time Setup**
Initialize the environment and install dependencies.
```powershell
.\setup.bat
```

**2. Launch Application**
Start the Solara server and open the application window.
```powershell
.\run_parallax.bat
```
*Note: The launcher minimizes the server console to the system tray and ensures a single browser window opens.*
