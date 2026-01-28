import flet as ft

def main(page: ft.Page):
    page.title = "Parallax v0.1"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 1280
    page.window.height = 800
    
    page.add(
        ft.Container(
            content=ft.Text("Welcome to Parallax", size=30, weight=ft.FontWeight.BOLD),
            alignment=ft.Alignment(0, 0),
            expand=True
        )
    )

if __name__ == "__main__":
    ft.app(main)
