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
We prioritize local performance, GPU acceleration, and strict typing.

*   **GUI:** [Flet](https://flet.dev) (Flutter for Python) - 60FPS, GPU-accelerated, compiled to native Windows executable.
*   **Data Engine:** [Polars](https://pola.rs) - Rust-based DataFrame library. Replaces Pandas for speed and strict schema enforcement.
*   **Math:** `scipy.optimize` (SLSQP/Minimize) for solving weight allocations.
*   **Visualization:** Plotly (via Flet) for interactive drift analysis.

### Architecture
*   `src/core`: Pure logic and math. 100% covered by `pytest`.
*   `src/data`: Interface adapters for Norgate Data and CSV ingestion.
*   `src/ui`: Declarative Flet components.

---
