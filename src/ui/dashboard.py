
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
        vol_spread = vol_b - vol_a # Positive means Proxy is more volatile
        
        # Pack results
        results = {
            "correlation": corr,
            "vol_a": vol_a,
            "vol_b": vol_b,
            "vol_spread": vol_spread,
            "data": combined
        }
        calculation_result.set(results)
        
    except Exception as e:
        calculation_result.set({"error": str(e)})
    finally:
        is_loading.set(False)


@solara.component
def Dashboard():
    
    with solara.Column(style={"padding": "24px", "height": "100%"}):
        
        # --- Header ---
        solara.Markdown("# 🔭 Drift Analysis")
        
        # --- Controls ---
        with solara.Card():
            with solara.Column(gap="15px"):
                # Asset Selection Row
                with solara.Row(gap="20px", style={"align-items": "center"}):
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
                    solara.Button(
                        "Analyze Drift", 
                        on_click=calculate_analytics,
                        color="primary",
                        icon_name="mdi-chart-line",
                        loading=is_loading.value
                    )
                
                # Settings Row
                solara.Text("Lookback Window (Days):", style={"font-weight": "bold", "font-size": "0.9em"})
                solara.SliderInt(
                    label="",
                    value=lookback_window,
                    min=30,
                    max=365,
                    thumb_label=True
                )

        # --- Results ---
        if calculation_result.value:
            res = calculation_result.value
            
            if "error" in res:
                solara.Error(res["error"])
            else:
                data = res["data"]
                corr = res["correlation"]
                vol_spread = res["vol_spread"]
                vol_a = res["vol_a"]
                vol_b = res["vol_b"]
                
                # Metrics Row
                with solara.Row(gap="20px", style={"margin-top": "20px"}):
                    
                    # Correlation Card
                    with solara.Card("Correlation"):
                        color = "green" if corr > 0.8 else "orange" if corr > 0.5 else "red"
                        solara.Text(f"{corr:.4f}", style={"font-size": "28px", "font-weight": "bold", "color": color})
                        solara.Text("Pearson Coeff (Returns)", style={"font-size": "0.8em", "opacity": "0.7"})

                    # Volatility Spread Card
                    with solara.Card("Volatility Spread"):
                        # If spread is positive, Proxy is more volatile (Riskier)
                        spread_color = "red" if vol_spread > 0.05 else "green" if vol_spread < 0.02 else "orange"
                        prefix = "+" if vol_spread > 0 else ""
                        solara.Text(f"{prefix}{vol_spread:.2%}", style={"font-size": "28px", "font-weight": "bold", "color": spread_color})
                        solara.Text(f"Target: {vol_a:.1%} | Proxy: {vol_b:.1%}", style={"font-size": "0.8em", "opacity": "0.7"})

                # Chart
                # Use plotly.graph_objects to avoid ANY dependency on pandas (Plotly Express requires pandas)
                import plotly.graph_objects as go
                
                fig = go.Figure()
                
                # Trace for Asset A
                fig.add_trace(go.Scatter(
                    x=data["date"].to_list(),
                    y=data["Asset A"].to_list(),
                    mode='lines',
                    name=asset_a.value
                ))
                
                # Trace for Asset B
                fig.add_trace(go.Scatter(
                    x=data["date"].to_list(),
                    y=data["Asset B"].to_list(),
                    mode='lines',
                    name=asset_b.value
                ))
                
                fig.update_layout(
                    title=f"Price History: {asset_a.value} vs {asset_b.value}",
                    template="plotly_dark",
                    height=500,
                    xaxis_title="Date",
                    yaxis_title="Price"
                )
                
                with solara.Card("Price Action", style={"margin-top": "20px"}):
                    solara.FigurePlotly(fig)
