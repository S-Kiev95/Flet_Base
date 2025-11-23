import flet as ft


class Settings:
    APP_TITLE = "La Milagrosa - Sistema de Ventas"
    WINDOW_WIDTH = 900
    WINDOW_HEIGHT = 600
    WINDOW_MIN_WIDTH = 800
    WINDOW_MIN_HEIGHT = 500

    # API Configuration
    API_BASE_URL = "https://api.example.com"
    API_TIMEOUT = 30


class AppColors:
    """Paleta de colores de la aplicación"""
    # Fondo principal
    BACKGROUND = ft.Colors.WHITE

    # Cards y contenedores - Celeste suave
    CARD_BG = "#E3F2FD"  # Celeste muy suave
    CARD_BORDER = "#BBDEFB"
    CARD_DARK = "#1F3A6A"  # Azul oscuro para cards de listados

    # Sidebar - Celeste oscuro
    SIDEBAR_BG = "#1976D2"  # Azul/Celeste intenso
    SIDEBAR_HEADER = "#1565C0"  # Celeste más oscuro
    SIDEBAR_TEXT = ft.Colors.WHITE
    SIDEBAR_ACCENT = "#42A5F5"  # Celeste claro para hover/activo

    # Modales - Fondo blanco con cards celestes
    MODAL_BG = ft.Colors.WHITE
    MODAL_HEADER = "#1976D2"
    MODAL_CARD = "#E3F2FD"  # Celeste suave para cards internas

    # Login - Celeste suave
    LOGIN_BG = "#E3F2FD"
    LOGIN_CARD = ft.Colors.WHITE

    # Inputs - Celeste
    INPUT_BG = "#E3F2FD"
    INPUT_BORDER = "#90CAF9"
    INPUT_FOCUS = "#1976D2"

    # Acentos
    PRIMARY = "#1976D2"  # Celeste/Azul
    SUCCESS = "#4CAF50"  # Verde para abonos/sin deuda
    WARNING = "#FF9800"  # Naranja
    DANGER = "#F44336"   # Rojo para deudas

    # Texto
    TEXT_PRIMARY = "#1A237E"  # Azul oscuro
    TEXT_SECONDARY = "#546E7A"