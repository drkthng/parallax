import solara
from src.ui.dashboard import Dashboard, show_settings

@solara.component
def Page():
    # Application State / Theme
    solara.Title("Parallax Drift Analyzer")
    
    # AppLayout is required for the AppBar (defined in Dashboard) to render.
    # We turn off navigation/sidebar since we are handling that via our own UI.
    with solara.AppLayout(navigation=False, sidebar_open=False):
        # Using solara.v (Vuetify) directly for maximum control over the header
        with solara.AppBar():
            solara.v.ToolbarTitle(children=["🔭 Parallax Drift Analyzer"], style_="margin-left: 20px")
            solara.v.Spacer() # Pushes anything after it to the right
            
            # redundantly add a text button and an icon button
            solara.Button("Settings", on_click=lambda: show_settings.set(not show_settings.value), text=True, color="white")
            solara.Button(icon_name="mdi-settings", on_click=lambda: show_settings.set(not show_settings.value), icon=True, color="white")
            
        Dashboard()
