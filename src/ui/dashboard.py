
import solara
import polars as pl
from typing import Optional

from src.data.loader import MockLoader
from src.core.stats import CorrelationEngine

# --- State ---
asset_a = solara.reactive("Index")
asset_b = solara.reactive("Proxy")
lookback_window = solara.reactive(100)
calculation_result = solara.reactive(None)
is_loading = solara.reactive(False)

def calculate_analytics():
    """Triggered by the UI to perform analysis."""
    is_loading.set(True)
    try:
        loader = MockLoader()
        
        # Load Data with dynamic window
        n = lookback_window.value
        df_a = loader.load_price_history(asset_a.value, n_days=n)
        df_b = loader.load_price_history(asset_b.value, n_days=n)
        
        # Join on Date
        df_a = df_a.rename({"close": "close_a"})
        df_b = df_b.rename({"close": "close_b"})
        
        combined = pl.DataFrame({
            "date": df_a["date"],
            "Asset A": df_a["close_a"],
            "Asset B": df_b["close_b"]
        })

        # --- Statistics Engine ---
        # 1. Calculate Returns (Drop nulls from first row)
        combined = combined.with_columns([
            pl.col("Asset A").pct_change().alias("ret_a"),
            pl.col("Asset B").pct_change().alias("ret_b")
        ]).drop_nulls()

        # 2. Correlation (on Returns)
        corr = CorrelationEngine.calculate_correlation(
            combined["ret_a"], 
            combined["ret_b"]
        )

        # 3. Volatility (Annualized)
        vol_a = CorrelationEngine.calculate_volatility(combined["ret_a"])
        vol_b = CorrelationEngine.calculate_volatility(combined["ret_b"])
        vol_spread = vol_b - vol_a 
        
        # 4. Tracking Error
        te = CorrelationEngine.calculate_tracking_error(combined["ret_a"], combined["ret_b"])
        
        # Pack results
        results = {
            "correlation": corr,
            "vol_a": vol_a,
            "vol_b": vol_b,
            "vol_spread": vol_spread,
            "tracking_error": te,
            "data": combined
        }
        calculation_result.set(results)
        
    except Exception as e:
        calculation_result.set({"error": str(e)})
    finally:
        is_loading.set(False)


@solara.component
def Dashboard():
    
    # Use full height for easier layout management
    with solara.Column(style={"padding": "24px", "height": "100vh"}):
        
        # --- Header ---
        solara.Markdown("# 🔭 Drift Analysis")
        
        # --- Main Layout (Grid) ---
        # Flex Row: Left (Controls/Metrics) | Right (Chart)
        with solara.Row(style={"height": "100%", "gap": "24px", "align-items": "start"}):
            
            # --- LEFT COLUMN: Controls & Metrics ---
            with solara.Column(style={"width": "350px", "min-width": "300px", "flex-shrink": "0"}):
                
                # Controls Card
                with solara.Card("Configuration"):
                    with solara.Column(gap="15px"):
                        solara.Select(
                            label="Target (Underlying)", 
                            values=["Index", "BTC", "SPY", "NDX", "GLD"], 
                            value=asset_a
                        )
                        solara.Select(
                            label="Proxy Portfolio", 
                            values=["Proxy", "ETH", "MSTR", "COIN", "QQQ"], 
                            value=asset_b
                        )
                        
                        solara.Text("Lookback Window:", style={"font-weight": "bold", "font-size": "0.9em", "margin-top": "10px"})
                        solara.SliderInt(
                            label="",
                            value=lookback_window,
                            min=30,
                            max=365,
                            thumb_label=True
                        )
                        
                        solara.Button(
                            "Analyze Drift", 
                            on_click=calculate_analytics,
                            color="primary",
                            icon_name="mdi-chart-line",
                            loading=is_loading.value,
                            style={"width": "100%", "margin-top": "10px"}
                        )

                # Metrics (If Ready)
                if calculation_result.value:
                    res = calculation_result.value
                    if "error" in res:
                        solara.Error(res["error"])
                    else:
                        corr = res["correlation"]
                        vol_spread = res["vol_spread"]
                        te = res["tracking_error"]
                        
                        # Stacked Cards for Vertical Layout
                        with solara.Column(gap="15px", style={"margin-top": "20px"}):
                            
                            # Correlation
                            with solara.Card("Correlation"):
                                color = "green" if corr > 0.8 else "orange" if corr > 0.5 else "red"
                                solara.Text(f"{corr:.4f}", style={"font-size": "26px", "font-weight": "bold", "color": color})
                            
                            # Tracking Error (New)
                            with solara.Card("Tracking Error (Ann.)"):
                                # Lower is better. <5% Great, >15% Poor?
                                te_color = "green" if te < 0.10 else "orange" if te < 0.20 else "red"
                                solara.Text(f"{te:.2%}", style={"font-size": "26px", "font-weight": "bold", "color": te_color})

                            # Volatility Spread
                            with solara.Card("Vol. Spread"):
                                spread_color = "red" if vol_spread > 0.05 else "green" if vol_spread < 0.02 else "orange"
                                prefix = "+" if vol_spread > 0 else ""
                                solara.Text(f"{prefix}{vol_spread:.2%}", style={"font-size": "26px", "font-weight": "bold", "color": spread_color})    

            # --- RIGHT COLUMN: Chart ---
            with solara.Column(style={"flex": "1", "min-width": "0", "height": "100%"}):
                if calculation_result.value and "error" not in calculation_result.value:
                    res = calculation_result.value
                    data = res["data"]
                    
                    # Chart
                    import plotly.graph_objects as go
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=data["date"].to_list(), y=data["Asset A"].to_list(), mode='lines', name=asset_a.value))
                    fig.add_trace(go.Scatter(x=data["date"].to_list(), y=data["Asset B"].to_list(), mode='lines', name=asset_b.value))
                    
                    fig.update_layout(
                        title=f"{asset_a.value} vs {asset_b.value} (Last {lookback_window.value} Days)",
                        template="plotly_dark",
                        height=600, # Taller chart
                        xaxis_title="Date",
                        yaxis_title="Price (Rebased to 100)",
                        margin=dict(l=40, r=40, t=60, b=40)
                    )
                    
                    with solara.Card(style={"height": "100%"}):
                        solara.FigurePlotly(fig)
                else:
                    # Placeholder or Empty State
                    if not calculation_result.value:
                         with solara.Card(style={"height": "400px", "display": "flex", "align-items": "center", "justify-content": "center"}):
                            solara.Text("Select assets and click 'Analyze Drift' to see the chart.", style={"opacity": "0.5"})
