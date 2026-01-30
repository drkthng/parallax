"""
Parallax - Solara App Entry Point
A Walking Skeleton UI for the Parallax Drift Analyzer.
"""

import solara


# Reactive state for correlation result
correlation_result = solara.reactive(None)
is_calculating = solara.reactive(False)


def test_correlation_connection():
    """
    Performs a test correlation calculation between two mock assets.
    Updates the reactive state with the result.
    """
    # Lazy import to speed up initial app startup
    import polars as pl
    from src.core.stats import CorrelationEngine
    from src.data.loader import MockLoader

    is_calculating.set(True)
    try:
        loader = MockLoader()
        
        # Load two sets of mock price data
        # Note: MockLoader uses seed=42, so we get deterministic data
        asset1_df = loader.load_price_history("ASSET_A")
        asset2_df = loader.load_price_history("ASSET_B")
        
        # Extract price series for correlation
        series1 = asset1_df["close"]
        series2 = asset2_df["close"]
        
        # Calculate correlation using the existing engine
        result = CorrelationEngine.calculate_correlation(series1, series2)
        correlation_result.set(result)
    except Exception as e:
        correlation_result.set(f"Error: {e}")
    finally:
        is_calculating.set(False)


@solara.component
def Page():
    """Main Parallax application page."""
    
    with solara.Column(style={"padding": "40px", "max-width": "800px", "margin": "0 auto"}):
        # Header
        solara.Markdown(
            """
            # 🚀 Parallax v0.1
            
            **Drift Analyzer** - Powered by Polars & Solara
            
            ---
            """
        )
        
        # Test Connection Section
        solara.Markdown("### Core Engine Test")
        solara.Markdown(
            "Click the button below to verify the connection between the UI "
            "and the `CorrelationEngine` using mock data."
        )
        
        with solara.Row(style={"margin-top": "16px", "gap": "16px", "align-items": "center"}):
            solara.Button(
                "Test Connection",
                on_click=lambda: test_correlation_connection(),
                disabled=is_calculating.value,
                color="primary",
            )
            
            if is_calculating.value:
                solara.SpinnerSolara(size="24px")
        
        # Result Display
        if correlation_result.value is not None:
            result = correlation_result.value
            
            if isinstance(result, float):
                solara.Success(
                    f"✅ Connection Successful! Correlation: **{result:.6f}**",
                    style={"margin-top": "16px"},
                )
                solara.Info(
                    "The `MockLoader` provided synthetic data and the "
                    "`CorrelationEngine` computed the Pearson correlation coefficient. "
                    "Note: Both assets use the same seed, so correlation is 1.0.",
                    style={"margin-top": "8px"},
                )
            else:
                solara.Error(
                    f"❌ {result}",
                    style={"margin-top": "16px"},
                )
        
        # Footer Info
        solara.Markdown(
            """
            ---
            
            **Tech Stack:**
            - 📊 **Data Engine:** Polars (no pandas!)
            - 🎨 **UI Framework:** Solara
            - 🧮 **Statistics:** CorrelationEngine, MockLoader
            """
        )
