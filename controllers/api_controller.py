import asyncio
from core.state import GlobalState


class APIController:
    """Controlador para manejar llamadas a APIs"""
    
    def __init__(self, state: GlobalState):
        self.state = state
        self.base_url = "https://api.example.com"  # Configura tu URL base
    
    async def fetch_data(self, endpoint: str):
        """
        Simula una llamada a API
        En producción, usa aiohttp o httpx para llamadas reales
        """
        # Simulación de carga
        await asyncio.sleep(1)
        
        # Simula datos de respuesta
        fake_data = {
            "users": [
                {"id": 1, "name": "Usuario 1"},
                {"id": 2, "name": "Usuario 2"},
            ],
            "items": [
                {"id": 1, "title": "Item 1", "count": 42},
                {"id": 2, "title": "Item 2", "count": 17},
            ]
        }
        
        return fake_data.get(endpoint, {})
    
    async def load_users(self):
        """Carga usuarios y actualiza el estado global"""
        self.state.set("loading", True)
        try:
            data = await self.fetch_data("users")
            self.state.set("users", data)
            self.state.set("error", None)
        except Exception as e:
            self.state.set("error", str(e))
        finally:
            self.state.set("loading", False)
    
    async def load_items(self):
        """Carga items y actualiza el estado global"""
        self.state.set("loading", True)
        try:
            data = await self.fetch_data("items")
            self.state.set("items", data)
            self.state.set("error", None)
        except Exception as e:
            self.state.set("error", str(e))
        finally:
            self.state.set("loading", False)