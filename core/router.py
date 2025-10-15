from typing import Dict, Callable


class Router:
    """Maneja la navegación entre páginas"""
    
    def __init__(self):
        self.routes: Dict[str, Callable] = {}
        self.current_route: str = ""
        self._on_route_change: Callable = None
    
    def register_route(self, name: str, page_builder: Callable):
        """Registra una ruta con su constructor de página"""
        self.routes[name] = page_builder
    
    def navigate(self, route: str):
        """Navega a una ruta"""
        if route in self.routes:
            self.current_route = route
            if self._on_route_change:
                self._on_route_change(route)
    
    def on_route_change(self, callback: Callable):
        """Registra callback para cambios de ruta"""
        self._on_route_change = callback
    
    def get_current_page(self):
        """Obtiene la página actual"""
        if self.current_route in self.routes:
            return self.routes[self.current_route]()
        return None