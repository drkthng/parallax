import solara
from src.ui.dashboard import Dashboard, show_settings

@solara.component
def Page():
    # Force settings
    try:
        import solara.server.settings
        solara.server.settings.theme.show_banner = False
    except ImportError:
        pass

    # Application State / Theme
    solara.Title("Parallax Drift Analyzer")
    
    # "Atom Bomb" Fix for Footer
    solara.HTML(tag="script", unsafe_innerHTML="""
        document.addEventListener("DOMContentLoaded", () => {
             // 1. Inject Styles
             const style = document.createElement('style');
             style.innerHTML = `
                div[class*="solara-footer"], footer, .v-footer, .v-system-bar {
                    display: none !important;
                    opacity: 0 !important;
                    pointer-events: none !important;
                }
             `;
             document.head.appendChild(style);
             
             // 2. Text Content Hunter
             setInterval(() => {
                const targets = document.querySelectorAll('div, span, a, p, footer');
                targets.forEach(el => {
                    if (el.innerText && el.innerText.includes("This website runs on Solara")) {
                        el.style.display = "none";
                        el.style.visibility = "hidden";
                        el.style.opacity = "0";
                        el.style.pointerEvents = "none";
                        
                        // Hide parent container if it's small (likely a bar)
                        if (el.parentElement && el.parentElement.clientHeight < 60) {
                             el.parentElement.style.display = "none";
                        }
                    }
                });
             }, 500);
        });
    """)
    solara.Style("""
        .solara-footer, 
        .v-footer, 
        footer,
        div[class*="solara-footer"] {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            width: 0 !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }
    """)
    
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
