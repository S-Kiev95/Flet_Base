from typing import Callable, Any, Dict, List


class GlobalState:
    """Estado global de la aplicación con sistema de observadores"""
    
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._observers: Dict[str, List[Callable]] = {}
    
    def set(self, key: str, value: Any):
        """Establece un valor y notifica a los observadores"""
        self._data[key] = value
        self._notify(key, value)
    
    def get(self, key: str, default=None):
        """Obtiene un valor del estado"""
        return self._data.get(key, default)
    
    def subscribe(self, key: str, callback: Callable):
        """Suscribe un callback para ser notificado cuando cambie un valor"""
        if key not in self._observers:
            self._observers[key] = []
        self._observers[key].append(callback)
    
    def _notify(self, key: str, value: Any):
        """Notifica a todos los observadores de un key"""
        if key in self._observers:
            for callback in self._observers[key]:
                callback(value)