import flet as ft

class ParallaxLayout(ft.Column):
    def __init__(self, on_calculate: callable):
        super().__init__()
        self.on_calculate = on_calculate
        self.spacing = 20
        self.scroll = ft.ScrollMode.ADAPTIVE
        
        # UI Components
        self.asset_a = ft.Dropdown(
            label="Asset A",
            options=[
                ft.dropdown.Option("BTC"),
                ft.dropdown.Option("ETH"),
                ft.dropdown.Option("SOL"),
            ],
            width=200,
            value="BTC"
        )
        
        self.asset_b = ft.Dropdown(
            label="Asset B",
            options=[
                ft.dropdown.Option("BTC"),
                ft.dropdown.Option("ETH"),
                ft.dropdown.Option("SOL"),
            ],
            width=200,
            value="ETH"
        )
        
        self.calc_button = ft.ElevatedButton(
            text="Calculate Correlation",
            on_click=self.on_calculate,
            icon=ft.icons.CALCULATE
        )
        
        self.result_text = ft.Text(
            value="Correlation: ---",
            size=20,
            weight=ft.FontWeight.BOLD
        )
        
        self.result_card = ft.Card(
            content=ft.Container(
                content=self.result_text,
                padding=20
            )
        )

        self.controls = [
            ft.Text("Parallax Drift Analyzer", size=32, weight=ft.FontWeight.BOLD),
            ft.Row(
                controls=[
                    self.asset_a,
                    self.asset_b,
                ],
                alignment=ft.MainAxisAlignment.START
            ),
            self.calc_button,
            ft.Divider(),
            self.result_card
        ]

    def update_result(self, correlation: float):
        self.result_text.value = f"Correlation: {correlation:.4f}"
        self.result_text.color = ft.colors.GREEN if correlation > 0 else ft.colors.RED
        self.update()

    def show_error(self, message: str):
        self.result_text.value = f"Error: {message}"
        self.result_text.color = ft.colors.AMBER
        self.update()
