import flet as ft
from src.ui.layout import ParallaxLayout
from src.data.loader import MockLoader
from src.core.stats import CorrelationEngine
from src.utils.async_tools import run_in_background

def main(page: ft.Page):
    page.title = "Parallax"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 1000
    page.window.height = 800
    page.padding = 40

    # Instantiate logic and data layers
    loader = MockLoader()
    engine = CorrelationEngine()

    @run_in_background
    def handle_calculate(e):
        asset_a = layout.asset_a.value
        asset_b = layout.asset_b.value
        
        layout.calc_button.disabled = True
        layout.result_text.value = "Calculating..."
        layout.update()
        
        try:
            # Fetch data
            df_a = loader.load_price_history(asset_a)
            df_b = loader.load_price_history(asset_b)
            
            if df_a is None or df_b is None:
                layout.show_error("Could not load data for assets.")
                return

            # Pass 'close' columns to engine
            correlation = engine.calculate_correlation(df_a["close"], df_b["close"])
            
            # Update UI
            layout.update_result(correlation)
        except Exception as ex:
            layout.show_error(f"Error: {str(ex)}")
        finally:
            layout.calc_button.disabled = False
            layout.update()

    # Create layout
    layout = ParallaxLayout(on_calculate=handle_calculate)
    
    page.add(layout)

if __name__ == "__main__":
    ft.app(main)
