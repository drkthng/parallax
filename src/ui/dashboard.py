
import solara
import polars as pl
from typing import Optional

from src.data.loader import MockLoader
from src.core.stats import CorrelationEngine

# --- State ---
asset_a = solara.reactive("Index")
proxy_assets = solara.reactive(["MSTR"]) 
lookback_window = solara.reactive(100)
calculation_result = solara.reactive(None)
is_loading = solara.reactive(False)

def calculate_analytics():
    """Triggered by the UI to perform analysis."""
    is_loading.set(True)
    try:
        loader = MockLoader()
        n = lookback_window.value
        
        # 1. Load TARGET Data
        df_target = loader.load_price_history(asset_a.value, n_days=n)
        df_target = df_target.rename({"close": "close_target"})
        
        # 2. Load PROXY Data (Multi-Asset)
        if not proxy_assets.value:
            raise ValueError("Please select at least one asset for the Proxy Portfolio.")
            
        proxy_dfs = []
        for asset in proxy_assets.value:
            df = loader.load_price_history(asset, n_days=n)
            # Rename close col to avoid collision (e.g. "close_MSTR")
            df = df.rename({"close": f"close_{asset}"})
            proxy_dfs.append(df)
        
        # 3. Join All Data
        # Base is target df
        combined = df_target
        
        # Join all proxy assets on 'date'
        # Since MockLoader uses same dates, we can assume alignment, but let's be safe(ish) using join
        for df in proxy_dfs:
            combined = combined.join(df, on="date", how="inner")
            
        # 4. Calculate Returns for ALL columns
        # Filter explicitly for price columns
        price_cols = [c for c in combined.columns if c.startswith("close_")]
        
        # Calculate percent change for all price columns
        # resulting cols: "ret_target", "ret_MSTR", "ret_COIN", etc.
        combined = combined.with_columns([
            pl.col(c).pct_change().alias(c.replace("close_", "ret_")) 
            for c in price_cols
        ]).drop_nulls()
        
        # 5. Synthesize Proxy Return (Equal Weight)
        # Avg(Returns of all selected proxy assets)
        proxy_ret_cols = [f"ret_{a}" for a in proxy_assets.value]
        
        # Sum horizontal / Count
        combined = combined.with_columns(
            (pl.sum_horizontal(proxy_ret_cols) / len(proxy_ret_cols)).alias("ret_proxy_synthetic")
        )
        
        # 6. Reconstruct Proxy Price (Base 100)
        # P_t = P_t-1 * (1 + R_t)
        # Using cumprod: 100 * Product(1 + R)
        # We need to add 1 to returns, then cumprod
        combined = combined.with_columns(
             (100 * (1 + pl.col("ret_proxy_synthetic")).cum_prod()).alias("close_proxy_synthetic")
        )

        # Also rebase Target to 100 for fair comparison on chart
        combined = combined.with_columns(
             (100 * (1 + pl.col("ret_target")).cum_prod()).alias("close_target_rebased")
        )

        # --- Statistics Engine ---
        # 2. Correlation
        corr = CorrelationEngine.calculate_correlation(
            combined["ret_target"], 
            combined["ret_proxy_synthetic"]
        )

        # 3. Volatility (Annualized)
        vol_a = CorrelationEngine.calculate_volatility(combined["ret_target"])
        vol_b = CorrelationEngine.calculate_volatility(combined["ret_proxy_synthetic"])
        vol_spread = vol_b - vol_a 
        
        # 4. Tracking Error
        te = CorrelationEngine.calculate_tracking_error(combined["ret_target"], combined["ret_proxy_synthetic"])
        
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
                        
                        solara.SelectMultiple(
                            label="Proxy Portfolio (Assets)", 
                            all_values=["MSTR", "COIN", "MARA", "RIOT", "ETH", "QQQ"], 
                            values=proxy_assets
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
                            
                            # Tracking Error
                            with solara.Card("Tracking Error (Ann.)"):
                                # Lower is better.
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
                    
                    # 1. Target Line
                    fig.add_trace(go.Scatter(
                        x=data["date"].to_list(),
                        y=data["close_target_rebased"].to_list(),
                        mode='lines',
                        name=f"{asset_a.value} (Target)",
                        line=dict(color='white', width=2)
                    ))
                    
                    # 2. Proxy Line (Synthetic)
                    proxy_name = f"Proxy ({', '.join(proxy_assets.value[:2])}{'...' if len(proxy_assets.value)>2 else ''})"
                    fig.add_trace(go.Scatter(
                        x=data["date"].to_list(),
                        y=data["close_proxy_synthetic"].to_list(),
                        mode='lines',
                        name=proxy_name,
                        line=dict(color='#00d1b2', width=2, dash='solid') # Cyan for proxy
                    ))
                    
                    fig.update_layout(
                        title=f"Performance: {asset_a.value} vs Synthetic Proxy",
                        template="plotly_dark",
                        height=600, 
                        xaxis_title="Date",
                        yaxis_title="Price (Rebased to 100)",
                        margin=dict(l=40, r=40, t=60, b=40),
                        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
                    )
                    
                    with solara.Card(style={"height": "100%"}):
                        solara.FigurePlotly(fig)
                else:
                    # Placeholder or Empty State
                    if not calculation_result.value:
                         with solara.Card(style={"height": "400px", "display": "flex", "align-items": "center", "justify-content": "center"}):
                            solara.Text("Construct a portfolio and click 'Analyze Drift'.", style={"opacity": "0.5"})
