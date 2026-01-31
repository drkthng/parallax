
import solara
import polars as pl
from typing import Optional

from src.data.factory import DataFactory
from src.core.stats import CorrelationEngine
# --- State ---
asset_a = solara.reactive("Index")
proxy_assets = solara.reactive(["MSTR"]) 
proxy_weights = solara.reactive({}) # {symbol: weight_decimal}

# Configuration State
lookback_window = solara.reactive(100)
# Start date overrides lookback_window if set
lookback_start_date = solara.reactive(None) 
# Default max is 1 year, user can extend via settings
max_lookback_range = solara.reactive(365) 
data_source = solara.reactive("Mock")

# UI State
show_settings = solara.reactive(False)
calculation_result = solara.reactive(None)
is_loading = solara.reactive(False)

def calculate_analytics():
    """Triggered by the UI to perform analysis."""
    is_loading.set(True)
    try:
        # factory.get_loader might raise ImportError for Norgate, handled here
        loader = DataFactory.get_loader(data_source.value)
        n = lookback_window.value
        s_date = lookback_start_date.value
        
        # 1. Load TARGET Data
        df_target = loader.load_price_history(asset_a.value, n_days=n, start_date=s_date)
        df_target = df_target.rename({"close": "close_target"})
        
        # 2. Load PROXY Data (Multi-Asset)
        if not proxy_assets.value:
            raise ValueError("Please select at least one asset for the Proxy Portfolio.")
            
        proxy_dfs = []
        for asset in proxy_assets.value:
            df = loader.load_price_history(asset, n_days=n, start_date=s_date)
            # Rename close col to avoid collision (e.g. "close_MSTR")
            df = df.rename({"close": f"close_{asset}"})
            proxy_dfs.append(df)
        
        # 3. Join All Data
        combined = df_target
        for df in proxy_dfs:
            combined = combined.join(df, on="date", how="inner")
            
        # 4. Calculate Returns for ALL columns
        price_cols = [c for c in combined.columns if c.startswith("close_")]
        combined = combined.with_columns([
            pl.col(c).pct_change().alias(c.replace("close_", "ret_")) 
            for c in price_cols
        ]).drop_nulls()
        
        # 5. Synthesize Proxy Return (Custom Weights)
        # If weights are provided, use them. Otherwise, default to equal weight.
        weights_map = proxy_weights.value or {}
        proxy_ret_cols = [f"ret_{a}" for a in proxy_assets.value]
        
        # Ensure all selected assets have a weight defined, or default to 1/N
        final_weights = {}
        total_weight_input = sum(weights_map.values()) if weights_map else 0
        
        if total_weight_input > 0:
            # Normalize user weights to sum to 1.0
            for a in proxy_assets.value:
                final_weights[a] = weights_map.get(a, 0.0) / total_weight_input
        else:
            # Fallback to equal weight
            n_assets = len(proxy_assets.value)
            for a in proxy_assets.value:
                final_weights[a] = 1.0 / n_assets
                
        # Weighted Return: Sum(W_i * R_i)
        combined = combined.with_columns(
            pl.sum_horizontal([
                pl.col(f"ret_{a}") * final_weights[a] 
                for a in proxy_assets.value
            ]).alias("ret_proxy_synthetic")
        )
        
        # 6. Reconstruct Proxy Price (Base 100)
        combined = combined.with_columns(
             (100 * (1 + pl.col("ret_proxy_synthetic")).cum_prod()).alias("close_proxy_synthetic")
        )

        # Also rebase Target to 100
        combined = combined.with_columns(
             (100 * (1 + pl.col("ret_target")).cum_prod()).alias("close_target_rebased")
        )

        # --- Statistics Engine ---
        corr = CorrelationEngine.calculate_correlation(
            combined["ret_target"], 
            combined["ret_proxy_synthetic"]
        )

        vol_a = CorrelationEngine.calculate_volatility(combined["ret_target"])
        vol_b = CorrelationEngine.calculate_volatility(combined["ret_proxy_synthetic"])
        vol_spread = vol_b - vol_a 
        
        te = CorrelationEngine.calculate_tracking_error(combined["ret_target"], combined["ret_proxy_synthetic"])
        
        results = {
            "correlation": corr,
            "vol_a": vol_a,
            "vol_b": vol_b,
            "vol_spread": vol_spread,
            "tracking_error": te,
            "data": combined,
            "weights": final_weights
        }
        calculation_result.set(results)
        
    except Exception as e:
        calculation_result.set({"error": str(e)})
    finally:
        is_loading.set(False)


@solara.component
def Dashboard():
    
    # --- View Switching ---
    if show_settings.value:
        # SETTINGS VIEW
        with solara.Column(style={"padding": "40px", "max-width": "800px", "margin": "0 auto"}):
            with solara.Card("Global Settings"):
                with solara.Column(gap="20px"):
                    solara.Text("Data Source configuration is global.", style={"font-style": "italic"})
                    solara.Select(
                        label="Data Source",
                        values=["Mock", "Norgate", "CSV"],
                        value=data_source
                    )
                    
                    solara.Select(
                        label="Max Lookback Range (Days)",
                        values=[365, 730, 1825, 3650, 7300],
                        value=max_lookback_range
                    )
                    
                    solara.Button("Save & Return", on_click=lambda: show_settings.set(False), color="primary", size="large")

    else:
        # DASHBOARD VIEW
        with solara.Column(style={"padding": "24px", "height": "calc(100vh - 64px)"}): 
            
            with solara.Row(style={"height": "100%", "gap": "24px", "align-items": "start"}):
                
                # --- LEFT COLUMN ---
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
                            
                            # Custom Ticker Entry
                            with solara.Row(style={"align-items": "center", "margin-top": "-10px"}):
                                custom_ticker = solara.use_reactive("")
                                def add_ticker():
                                    if custom_ticker.value:
                                        t = custom_ticker.value.upper().strip()
                                        if t not in proxy_assets.value:
                                            proxy_assets.set(proxy_assets.value + [t])
                                        custom_ticker.set("")
                                
                                solara.InputText(label="Add Custom Ticker", value=custom_ticker, on_value=lambda _: None) # Controlled
                                solara.Button("Add", on_click=add_ticker, icon_name="mdi-plus", classes=["mt-6"])
                            
                            # Custom Weights UI (If assets are selected)
                            if proxy_assets.value:
                                with solara.Card("Weights (%)", style={"margin-top": "10px", "padding": "10px"}):
                                    for asset in proxy_assets.value:
                                        def set_w(v, a=asset):
                                            new_weights = dict(proxy_weights.value)
                                            new_weights[a] = v / 100.0 if v is not None else 0.0
                                            proxy_weights.set(new_weights)
                                        
                                        current_val = int(proxy_weights.value.get(asset, 0) * 100)
                                        solara.InputInt(label=f"{asset}", value=current_val, on_value=set_w)
                                    solara.Text("Weights will be auto-normalized to 100%.", style={"font-size": "0.7em", "color": "gray"})
                            
                            # Lookback Controls
                            with solara.Column(gap="10px", style={"margin-top": "10px"}):
                                solara.Text("Lookback Period:", style={"font-weight": "bold", "font-size": "0.9em"})
                                
                                # Toggle between Days and Start Date
                                use_start_date = solara.use_reactive(lookback_start_date.value is not None)
                                
                                def on_toggle_start_date(v):
                                    use_start_date.set(v)
                                    if not v:
                                        lookback_start_date.set(None)
                                    else:
                                        import datetime as dt
                                        lookback_start_date.set(dt.datetime.now() - dt.timedelta(days=100))
                                
                                solara.Checkbox(label="Use Start Date", value=use_start_date.value, on_value=on_toggle_start_date)
                                
                                if use_start_date.value:
                                    import datetime as dt
                                    curr_date_val = lookback_start_date.value or (dt.datetime.now() - dt.timedelta(days=100))
                                    
                                    solara.InputText(
                                        label="Start Date (YYYY-MM-DD)", 
                                        value=curr_date_val.strftime("%Y-%m-%d"),
                                        on_value=lambda v: lookback_start_date.set(dt.datetime.strptime(v, "%Y-%m-%d"))
                                    )
                                
                                # Always show duration controls
                                solara.InputInt(label="Duration (Days)", value=lookback_window)
                                solara.SliderInt(
                                    label="",
                                    value=lookback_window,
                                    min=30,
                                    max=max_lookback_range.value,
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

                    # Metrics
                    if calculation_result.value:
                        res = calculation_result.value
                        if "error" in res:
                            solara.Error(res["error"])
                        else:
                            corr = res["correlation"]
                            vol_spread = res["vol_spread"]
                            te = res["tracking_error"]
                            
                            with solara.Column(gap="15px", style={"margin-top": "20px"}):
                                with solara.Card("Correlation"):
                                    color = "green" if corr > 0.8 else "orange" if corr > 0.5 else "red"
                                    solara.Text(f"{corr:.4f}", style={"font-size": "26px", "font-weight": "bold", "color": color})
                                
                                with solara.Card("Tracking Error (Ann.)"):
                                    te_color = "green" if te < 0.10 else "orange" if te < 0.20 else "red"
                                    solara.Text(f"{te:.2%}", style={"font-size": "26px", "font-weight": "bold", "color": te_color})

                                with solara.Card("Vol. Spread"):
                                    spread_color = "red" if vol_spread > 0.05 else "green" if vol_spread < 0.02 else "orange"
                                    prefix = "+" if vol_spread > 0 else ""
                                    solara.Text(f"{prefix}{vol_spread:.2%}", style={"font-size": "26px", "font-weight": "bold", "color": spread_color})    

                # --- RIGHT COLUMN ---
                with solara.Column(style={"flex": "1", "min-width": "0", "height": "100%"}):
                    if calculation_result.value and "error" not in calculation_result.value:
                        res = calculation_result.value
                        data = res["data"]
                        weights = res.get("weights", {})
                        
                        import plotly.graph_objects as go
                        fig = go.Figure()
                        
                        fig.add_trace(go.Scatter(
                            x=data["date"].to_list(),
                            y=data["close_target_rebased"].to_list(),
                            mode='lines',
                            name=f"{asset_a.value} (Target)",
                            line=dict(color='white', width=2)
                        ))
                        
                        # Label showing weights
                        weight_str = ", ".join([f"{a}:{w:.0%}" for a, w in weights.items() if w > 0])
                        proxy_label = f"Proxy ({weight_str})" if len(weight_str) < 40 else "Proxy Portfolio"
                        
                        fig.add_trace(go.Scatter(
                            x=data["date"].to_list(),
                            y=data["close_proxy_synthetic"].to_list(),
                            mode='lines',
                            name=proxy_label,
                            line=dict(color='#00d1b2', width=2)
                        ))
                        
                        fig.update_layout(
                            title=f"Performance Comparison",
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
                        if not calculation_result.value:
                             with solara.Card(style={"height": "400px", "display": "flex", "align-items": "center", "justify-content": "center"}):
                                solara.Text("Construct a portfolio and click 'Analyze Drift'.", style={"opacity": "0.5"})

