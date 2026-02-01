# PARALLAX // DRIFT ANALYZER
> **"Synthesize the Underlying. Minimize the Drift."**

---

## 1. THE MISSION
**Parallax** is a high-precision tool for constructing synthetic assets. It measures the "drift"—the tracking error between a target asset (e.g., BTC) and a basket of proxies (e.g., MSTR, COIN). 

**NO FLUFF. PURE MATH. REACTIVE SPEED.**

---

## 2. THE ARSENAL (FEATURES)

### [A] DATA NEXUS
**Polars-Powered Engine.**
Ingests historical price data with zero latency. Agnostic to source (Norgate, CSV, Parquet).
*Strict Schema Enforcement.*

### [B] THE MIXER
**Reactive Weighting.**
Adjust proxy allocations in real-time. The Solara-based interface recalculates composite performance instantly as you drag sliders.
*No "Refresh" Buttons. Just Flow.*

### [C] DRIFT ANALYSIS
**Visual Truth.**
Interactive Plotly surfaces reveal the deviation over time.
- **Correlation Heatmaps:** See where your proxies align.
- **Drift Cone:** Visualize the cumulative tracking error.

---

## 3. DEPLOYMENT (WINDOWS)

### THE "ONE-CLICK" LAUNCH
We don't ship a bloated `.exe`. We ship a **Launcher**.

1. **Install Python:** Ensure Python 3.10+ is installed.
2. **Run `setup.bat`:** (First time only) This builds the `.venv` and installs dependencies.
3. **Double-Click `run_parallax.bat`:**
   - Activates the environment.
   - Kills zombie processes.
   - Launches in **NATIVE APP MODE** (Edge/Chrome).

> **PRO TIP:** Right-click `run_parallax.bat` -> **Send to Desktop (create shortcut)**. Then right-click the shortcut -> **Properties** -> **Change Icon** to customize your dock.

---

## 4. OPERATIONAL GUIDE (3 STEPS)

### STEP 1: LOAD
Select your **Target Asset** (e.g., BTC) and your **Proxy Candidates** (e.g., MSTR, CLSK). The Data Nexus will align timestamps automatically.

### STEP 2: MIX
Use the connection sliders to assign weights.
*Example: 50% MSTR + 50% CLSK.*

### STEP 3: ANALYZE
Watch the **Drift Chart**. Minimize the spread.
- **Low Drift:** High fidelity synthesis.
- **High Friction:** Market inefficiencies or poor proxy selection.

---
*Built with Polars & Solara. 2026.*
