import flet as ft

class Sidebar:
    """Sidebar con navegación"""
    
    def __init__(self, router):
        self.router = router
    
    def build(self):
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Text("Mi App", size=20, weight=ft.FontWeight.BOLD),
                    padding=20,
                ),
                ft.Divider(height=1),
                self._create_nav_button("Página 1", ft.Icons.HOME, "page1"),
                self._create_nav_button("Página 2", ft.Icons.DASHBOARD, "page2"),
            ]),
            width=200,
            bgcolor=ft.Colors.BLUE_GREY_900,  # Color oscuro para sidebar
            padding=10,
        )
    
    def _create_nav_button(self, text: str, icon, route: str):
        """Crea un botón de navegación"""
        return ft.TextButton(
            content=ft.Row([
                ft.Icon(icon),
                ft.Text(text),
            ]),
            on_click=lambda _: self.router.navigate(route),
        )