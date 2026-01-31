
import solara
from src.ui.dashboard import Dashboard

@solara.component
def Page():
    # Application State / Theme
    solara.Title("Parallax Drift Analyzer")
    
    with solara.AppLayout(navigation=False, sidebar_open=False):
        with solara.AppBar():
            solara.Text("Parallax v0.2")
            
        with solara.Sidebar():
            solara.Markdown("## Navigation")
            # Future nav items here
            solara.Button("Dashboard", icon_name="mdi-view-dashboard", color="primary", text=True)
            solara.Button("Settings", icon_name="mdi-cog", text=True)

        Dashboard()

