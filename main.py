import flet as ft
from config.settings import Settings
from core.state import GlobalState
from core.router import Router
from controllers.api_controller import APIController
from views.components.sidebar import Sidebar
from views.page1 import Page1
from views.page2 import Page2


class MainApp:
    """Aplicación principal"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        
        # Inicializar core
        self.state = GlobalState()
        self.router = Router()
        self.api = APIController(self.state)
        
        # Inicializar estado
        self.state.set("counter", 0)
        
        # Registrar rutas (ahora pasando page)
        self.router.register_route("page1", lambda: Page1(self.state, self.api, self.page))
        self.router.register_route("page2", lambda: Page2(self.state, self.api, self.page))
        
        # Contenedor de contenido
        self.content_area = ft.Container(expand=True)
        self.main_container = None
        
        # Observar cambios de ruta
        self.router.on_route_change(self._on_route_change)
    
    def build(self):
        sidebar = Sidebar(self.router)
        self.router.navigate("page1")
        
        self.main_container = ft.Row([
            sidebar.build(),
            ft.VerticalDivider(width=1),
            self.content_area,
        ], expand=True)
        
        return self.main_container
    
    def _on_route_change(self, route: str):
        """Actualiza el contenido cuando cambia la ruta"""
        page_obj = self.router.get_current_page()
        if page_obj:
            self.content_area.content = page_obj.build()
            self.page.update()


def main(page: ft.Page):
    page.title = Settings.APP_TITLE
    page.window.width = Settings.WINDOW_WIDTH
    page.window.height = Settings.WINDOW_HEIGHT
    page.window.min_width = Settings.WINDOW_MIN_WIDTH
    page.window.min_height = Settings.WINDOW_MIN_HEIGHT
    
    app = MainApp(page)
    page.add(app.build())


if __name__ == "__main__":
    ft.app(target=main)