
import solara
import polars as pl
from typing import Optional, List

from src.data.factory import DataFactory
from src.core.stats import CorrelationEngine
from src.utils.settings import get_settings_manager

# --- Settings Manager ---
_settings = get_settings_manager()
_loaded_settings = _settings.load()

# --- State (initialized from saved settings) ---
asset_a = solara.reactive(_loaded_settings.get("asset_a", "Index"))
proxy_assets = solara.reactive(_loaded_settings.get("proxy_assets", ["MSTR"]))
proxy_weights = solara.reactive(_loaded_settings.get("proxy_weights", {}))
show_tickers = solara.reactive(_loaded_settings.get("show_tickers", []))

# Configuration State
lookback_window = solara.reactive(_loaded_settings.get("lookback_window", 100))
lookback_start_date = solara.reactive(None)  # Not persisted (datetime is complex)
max_lookback_range = solara.reactive(_loaded_settings.get("max_lookback_range", 365))
data_source = solara.reactive(_loaded_settings.get("data_source", "Mock"))
source_overrides = solara.reactive(_loaded_settings.get("source_overrides", {})) # {symbol: source}
persist_settings = solara.reactive(_loaded_settings.get("persist_settings", False))

# Available target options (can be extended by user)
available_targets: List[str] = _loaded_settings.get("available_targets", ["Index", "BTC", "SPY", "NDX", "GLD"])

# UI State
show_settings = solara.reactive(False)
calculation_result = solara.reactive(None)
is_loading = solara.reactive(False)


def save_current_settings():
    """Save all current settings to disk if persistence is enabled."""
    if persist_settings.value:
        _settings.save({
            "asset_a": asset_a.value,
            "proxy_assets": proxy_assets.value,
            "proxy_weights": proxy_weights.value,
            "show_tickers": show_tickers.value,
            "lookback_window": lookback_window.value,
            "max_lookback_range": max_lookback_range.value,
            "data_source": data_source.value,
            "persist_settings": persist_settings.value,
            "available_targets": available_targets,
            "source_overrides": source_overrides.value,
        })

def resolve_loader(symbol: str) -> tuple:
    """Get loader for a specific symbol based on overrides or default."""
    source = source_overrides.value.get(symbol, data_source.value)
    return DataFactory.get_loader_safe(source)

def calculate_analytics():
    """Triggered by the UI to perform analysis."""
    is_loading.set(True)
    try:

        n = lookback_window.value
        s_date = lookback_start_date.value
        
        warnings_list = []
        
        # 1. Load TARGET Data
        loader_target, warn_target = resolve_loader(asset_a.value)
        if warn_target:
            warnings_list.append(f"Target ({asset_a.value}): {warn_target}")
            
        df_target = loader_target.load_price_history(asset_a.value, n_days=n, start_date=s_date)
        if df_target.is_empty():
            raise ValueError(f"No data returned for target: {asset_a.value}")
            
        df_target = df_target.rename({"close": "close_target"})
        
        # 2. Load PROXY Portfolio Data
        if not proxy_assets.value:
            raise ValueError("Please select at least one asset for the Proxy Portfolio.")
            
        proxy_dfs = []
        for asset in proxy_assets.value:
            loader_p, warn_p = resolve_loader(asset)
            if warn_p:
                warnings_list.append(f"Proxy ({asset}): {warn_p}")
                
            try:
                df = loader_p.load_price_history(asset, n_days=n, start_date=s_date)
                if not df.is_empty():
                    df = df.rename({"close": f"close_{asset}"})
                    proxy_dfs.append(df)
            except Exception as e:
                warnings_list.append(f"Failed to load {asset}: {e}")
        
        loader_warning = "; ".join(warnings_list) if warnings_list else None
        
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
        
        # 5. Synthesize Proxy Return (Cash-Weighted)
        weights_map = proxy_weights.value or {}
        
        # Validate Total Weight
        total_weight_input = sum(weights_map.get(a, 0.0) for a in proxy_assets.value)
        
        if total_weight_input > 1.0001: # Small epsilon for float
            raise ValueError(f"Total weights ({total_weight_input:.1%}) exceed 100%. Please reduce them.")
            
        # Any weight < 100% is Cash (0% return)
        # Rp = Sum(W_i * R_i) + (1 - Sum(W_i)) * 0
        final_weights = {a: weights_map.get(a, 0.0) for a in proxy_assets.value}
        cash_weight = 1.0 - total_weight_input
        
        # Weighted Return: Sum(W_i * R_i)
        combined = combined.with_columns(
            pl.sum_horizontal([
                pl.col(f"ret_{a}") * final_weights[a] 
                for a in proxy_assets.value
            ]).alias("ret_proxy_synthetic")
        )
        
        # 6. Reconstruct Prices (Base 100)
        # Synthetic Proxy
        combined = combined.with_columns(
             (100 * (1 + pl.col("ret_proxy_synthetic")).cum_prod()).alias("close_proxy_synthetic")
        )
        # Target
        combined = combined.with_columns(
             (100 * (1 + pl.col("ret_target")).cum_prod()).alias("close_target_rebased")
        )
        # Individual Tickers (for optional visualization)
        for a in proxy_assets.value:
             combined = combined.with_columns(
                  (100 * (1 + pl.col(f"ret_{a}")).cum_prod()).alias(f"close_{a}_rebased")
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
        te_period = CorrelationEngine.calculate_period_tracking_error(combined["ret_target"], combined["ret_proxy_synthetic"])
        
        results = {
            "correlation": corr,
            "vol_a": vol_a,
            "vol_b": vol_b,
            "vol_spread": vol_spread,
            "tracking_error": te,
            "period_tracking_error": te_period,
            "data": combined,
            "weights": final_weights,
            "cash_weight": cash_weight,
            "loader_warning": loader_warning  # Will be None if no fallback occurred
        }
        calculation_result.set(results)
        
    except Exception as e:
        calculation_result.set({"error": str(e)})
    finally:
        is_loading.set(False)


@solara.component
def Dashboard():
    # --- Hooks (Must be at top level) ---
    custom_ticker = solara.use_reactive("")
    use_start_date = solara.use_reactive(lookback_start_date.value is not None)
    custom_target = solara.use_reactive("")  # Moved to top level to avoid conditional hook error
    new_override_symbol = solara.use_reactive("")
    new_override_source = solara.use_reactive("Yahoo")

    # --- View Switching ---
    if show_settings.value:
        # SETTINGS VIEW
        with solara.Column(style={"padding": "40px", "max-width": "800px", "margin": "0 auto"}):
            with solara.Card("Global Settings"):
                with solara.Column(gap="20px"):
                    solara.Text("Data Source configuration is global.", style={"font-style": "italic"})
                    solara.Select(
                        label="Data Source",
                        values=["Mock", "Norgate", "CSV", "Yahoo"],
                        value=data_source
                    )
                    
                    # Data Source Routing
                    with solara.Card("Data Source Routing"):
                        solara.Text("Override the default data source for specific assets.", style={"font-size": "0.9em", "color": "gray", "margin-bottom": "15px"})
                        
                        # List Rules
                        with solara.Column(gap="5px"):
                            if not source_overrides.value:
                                solara.Text("No overrides defined.", style={"font-style": "italic", "color": "gray"})
                            else:
                                for sym, src in list(source_overrides.value.items()):
                                    with solara.Row(style={"align-items": "center"}):
                                        solara.Text(f"**{sym}** → {src}")
                                        def make_delete_handler(s):
                                            return lambda: source_overrides.set({k: v for k, v in source_overrides.value.items() if k != s})
                                        
                                        solara.Button(icon_name="mdi-delete", on_click=make_delete_handler(sym), icon=True, outlined=True, classes=["ma-0"])
                        
                        # Add Rule
                        solara.HTML(tag="hr", style="margin: 15px 0")
                        # hooks moved to top level
                        
                        with solara.Row(style={"align-items": "end"}):
                            solara.InputText(label="Symbol (e.g. BTC-USD)", value=new_override_symbol)
                            solara.Select(label="Source", values=["Yahoo", "Norgate", "Mock"], value=new_override_source)
                            
                            def add_override():
                                if new_override_symbol.value:
                                    s = new_override_symbol.value.upper().strip()
                                    new_map = source_overrides.value.copy()
                                    new_map[s] = new_override_source.value
                                    source_overrides.set(new_map)
                                    new_override_symbol.set("")
                                    if persist_settings.value:
                                        save_current_settings()
                            
                            solara.Button("Add Rule", on_click=add_override, color="primary")
                    
                    solara.Select(
                        label="Max Lookback Range (Days)",
                        values=[365, 730, 1825, 3650, 7300],
                        value=max_lookback_range
                    )
                    
                    # Persistence Toggle
                    with solara.Card("Session Persistence", style={"margin-top": "10px"}):
                        def on_persist_toggle(value):
                            persist_settings.set(value)
                            if value:
                                save_current_settings()
                            else:
                                _settings.clear()
                        
                        solara.Switch(
                            label="Remember Settings",
                            value=persist_settings.value,
                            on_value=on_persist_toggle
                        )
                        solara.Text(
                            "When enabled, your configuration will be saved and restored on next startup.",
                            style={"font-size": "0.8em", "color": "gray"}
                        )
                    
                    def save_and_return():
                        save_current_settings()
                        show_settings.set(False)
                    
                    solara.Button("Save & Return", on_click=save_and_return, color="primary", size="large")

    else:
        # DASHBOARD VIEW
        with solara.Column(style={"padding": "24px", "height": "calc(100vh - 64px)"}): 
            
            with solara.Row(style={"height": "100%", "gap": "24px", "align-items": "start"}):
                
                # --- LEFT COLUMN ---
                with solara.Column(style={"width": "350px", "min-width": "300px", "flex-shrink": "0"}):
                    
                    # Controls Card
                    with solara.Card("Configuration"):
                        with solara.Column(gap="15px"):
                            # Target Selection with Custom Entry
                            solara.Select(
                                label="Target (Underlying)", 
                                values=available_targets, 
                                value=asset_a
                            )
                            
                            # Custom Target Entry
                            # custom_target hook moved to top level
                            with solara.Row(style={"align-items": "center", "margin-top": "-10px"}):
                                def add_custom_target():
                                    global available_targets
                                    if custom_target.value:
                                        t = custom_target.value.upper().strip()
                                        if t not in available_targets:
                                            available_targets = available_targets + [t]
                                            asset_a.set(t)  # Auto-select the new target
                                            save_current_settings()
                                        custom_target.set("")
                                
                                solara.InputText(label="Add Custom Target", value=custom_target, on_value=lambda _: None)
                                solara.Button("Add", on_click=add_custom_target, icon_name="mdi-plus", classes=["mt-6"])
                            
                            solara.SelectMultiple(
                                label="Proxy Portfolio (Assets)", 
                                all_values=["MSTR", "COIN", "MARA", "RIOT", "ETH", "QQQ"], 
                                values=proxy_assets
                            )
                            
                            # Custom Ticker Entry
                            with solara.Row(style={"align-items": "center", "margin-top": "-10px"}):
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
                                        with solara.Row(style={"align-items": "center"}):
                                            # Visibility Toggle
                                            is_visible = asset in show_tickers.value
                                            def toggle_v(v, a=asset):
                                                if v: show_tickers.set(list(set(show_tickers.value + [a])))
                                                else: show_tickers.set([x for x in show_tickers.value if x != a])
                                            
                                            solara.Checkbox(value=is_visible, on_value=toggle_v, style="flex: 0")
                                            
                                            # Weight Input
                                            def set_w(v, a=asset):
                                                new_weights = dict(proxy_weights.value)
                                                new_weights[a] = v / 100.0 if v is not None else 0.0
                                                proxy_weights.set(new_weights)
                                            
                                            current_val = int(proxy_weights.value.get(asset, 0) * 100)
                                            solara.InputInt(label=f"{asset}", value=current_val, on_value=set_w, style="flex: 1")
                                            
                                    solara.Text("Weights sum must be <= 100%. Remainder is Cash.", style="font-size: 0.7em; color: gray")
                            
                            # Lookback Controls
                            with solara.Column(gap="10px", style={"margin-top": "10px"}):
                                solara.Text("Lookback Period:", style={"font-weight": "bold", "font-size": "0.9em"})
                                
                                # Toggle between Days and Start Date
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
                                style="width: 100%; margin-top: 10px"
                            )

                    # Metrics
                    if calculation_result.value:
                        res = calculation_result.value
                        if "error" in res:
                            solara.Error(res["error"])
                        else:
                            # Show loader warning if fallback occurred
                            if res.get("loader_warning"):
                                solara.Warning(res["loader_warning"])
                            
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

                                with solara.Card("Tracking Error (Period)"):
                                    te_p = res["period_tracking_error"]
                                    solara.Text(f"{te_p:.2%}", style={"font-size": "26px", "font-weight": "bold", "color": "#00d1b2"})

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
                            line=dict(color='#00d1b2', width=3)
                        ))
                        
                        # Individual Tickers
                        for asset in show_tickers.value:
                            col_name = f"close_{asset}_rebased"
                            if col_name in data.columns:
                                fig.add_trace(go.Scatter(
                                    x=data["date"].to_list(),
                                    y=data[col_name].to_list(),
                                    mode='lines',
                                    name=f"{asset}",
                                    line=dict(width=1, dash='dot'),
                                    opacity=0.6
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

