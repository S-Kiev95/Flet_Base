import flet as ft
import asyncio
from config.settings import Settings, AppColors
from core.state import GlobalState
from core.router import Router
from controllers.api_controller import APIController
from views.components.sidebar import Sidebar
from database.connection import get_session_context
from database.db_service import UsuarioRepository, SesionRepository

# Importar Pages
from views.login_page import LoginPage
from views.clientes_page import ClientesPage
from views.productos_page import ProductosPage
from views.ventas_page import VentasPage
from views.nueva_venta_page import NuevaVentaPage
from views.usuarios_page import UsuariosPage


class MainApp:
    """Aplicación principal con autenticación"""

    def __init__(self, page: ft.Page):
        self.page = page

        # Inicializar core
        self.state = GlobalState()
        self.router = Router()
        self.api = APIController(self.state)
        self.sidebar = None

        # Usuario y sesión actuales
        self.usuario_actual = None
        self.token_sesion = None

        self.content_loading = ft.Container(
            content=ft.Column([
                ft.ProgressRing(width=50, height=50),
                ft.Text("Cargando...", size=16, color=ft.Colors.GREY_600)
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True,
            alignment=ft.alignment.center,
        )

        # Contenedor de contenido
        self.content_area = ft.Container(
            content=self.content_loading,
            expand=True
        )
        self.main_container = None

        # Página de login
        self.login_page = None

        # Observar cambios de ruta
        self.router.on_route_change(self._on_route_change)

    def build(self):
        """Construye la interfaz inicial"""

        # Verificar si hay un usuario inicial, si no crearlo
        self._inicializar_usuario_admin()

        # Mostrar página de login
        self.login_page = LoginPage(self.page, self._on_login_success)

        return self.login_page.build()

    def _inicializar_usuario_admin(self):
        """Crea el usuario admin inicial si no existe"""
        try:
            session = get_session_context()
            UsuarioRepository.crear_usuario_inicial(session)
            session.close()
        except Exception as e:
            print(f"Error al inicializar usuario admin: {e}")

    def _on_login_success(self, usuario, token):
        """Callback cuando el login es exitoso"""
        self.usuario_actual = usuario
        self.token_sesion = token

        # Guardar usuario en el estado global
        self.state.set("usuario_actual", usuario)
        self.state.set("token_sesion", token)

        # Registrar rutas con el usuario actual
        self._registrar_rutas()

        # Construir la aplicación principal
        self._construir_app_principal()

    def _registrar_rutas(self):
        """Registra las rutas de la aplicación"""
        self.router.register_route("clientes", lambda: ClientesPage(self.state, self.api, self.page))
        self.router.register_route("productos", lambda: ProductosPage(self.state, self.api, self.page))
        self.router.register_route("ventas", lambda: VentasPage(self.state, self.api, self.page, self.router))
        self.router.register_route("nueva_venta", lambda: NuevaVentaPage(self.state, self.api, self.page, self.router))

        # Ruta de usuarios (solo para SuperAdmin)
        if self.usuario_actual and self.usuario_actual.es_superadmin():
            self.router.register_route("usuarios", lambda: UsuariosPage(self.state, self.api, self.page))

    def _construir_app_principal(self):
        """Construye la aplicación principal después del login"""

        # Crear sidebar con usuario actual
        self.sidebar = Sidebar(self.page, self.router, self.usuario_actual, self._cerrar_sesion)

        # Limpiar la página
        self.page.controls.clear()

        # Construir el layout principal
        self.main_container = ft.Row([
            self.sidebar.build(),
            ft.VerticalDivider(width=1),
            self.content_area,
        ], expand=True)

        # Agregar a la página
        self.page.add(self.main_container)

        # Programar la navegación para después de que se renderice
        self.page.run_task(self._load_initial_page)

        self.page.update()

    async def _load_initial_page(self):
        """Carga la página inicial después de mostrar el loader"""
        # Pequeña pausa para que se vea el loader
        await asyncio.sleep(0.1)
        # Navegar a clientes
        self.router.navigate("clientes")

    def _on_route_change(self, route: str):
        """Actualiza el contenido cuando cambia la ruta"""

        # Verificar que la sesión siga siendo válida
        if not self._validar_sesion():
            return

        self.content_area.content = self.content_loading
        self.page.update()

        page_obj = self.router.get_current_page()
        if page_obj:
            if self.sidebar and hasattr(self.sidebar, 'loading_indicator'):
                self.sidebar.loading_indicator.visible = False
            self.content_area.content = page_obj.build()
            self.page.update()

    def _validar_sesion(self) -> bool:
        """Valida que la sesión actual siga siendo válida"""
        if not self.token_sesion:
            return True  # No hay sesión que validar (estamos en login)

        try:
            session = get_session_context()
            usuario = SesionRepository.validar_sesion(session, self.token_sesion)
            session.close()

            if not usuario:
                # Sesión expirada
                self._mostrar_sesion_expirada()
                return False

            return True

        except Exception as e:
            print(f"Error al validar sesión: {e}")
            return True  # Continuar en caso de error

    def _mostrar_sesion_expirada(self):
        """Muestra un mensaje de sesión expirada y vuelve al login"""

        def cerrar_dialog(e):
            dialog.open = False
            self.page.update()
            self._volver_al_login()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Sesión Expirada", color=AppColors.TEXT_PRIMARY),
            content=ft.Text("Tu sesión ha expirado. Por favor, inicia sesión nuevamente.", color=AppColors.TEXT_SECONDARY),
            bgcolor=AppColors.MODAL_BG,
            actions=[
                ft.ElevatedButton("Aceptar", bgcolor=AppColors.PRIMARY, color=ft.Colors.WHITE, on_click=cerrar_dialog),
            ],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _cerrar_sesion(self):
        """Cierra la sesión del usuario actual"""

        def confirmar_cierre(e):
            try:
                # Cerrar sesión en la BD
                session = get_session_context()
                SesionRepository.cerrar_sesion(session, self.token_sesion)
                session.close()

                dialog.open = False
                self.page.update()

                self._volver_al_login()

            except Exception as error:
                print(f"Error al cerrar sesión: {error}")
                self._volver_al_login()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Cerrar Sesión", color=AppColors.TEXT_PRIMARY),
            content=ft.Text(f"¿Estás seguro de que deseas cerrar sesión, {self.usuario_actual.nombre}?", color=AppColors.TEXT_SECONDARY),
            bgcolor=AppColors.MODAL_BG,
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self._cerrar_dialog(dialog)),
                ft.ElevatedButton(
                    "Cerrar Sesión",
                    bgcolor=AppColors.DANGER,
                    color=ft.Colors.WHITE,
                    on_click=confirmar_cierre
                ),
            ],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _volver_al_login(self):
        """Vuelve a la pantalla de login"""

        # Limpiar estado
        self.usuario_actual = None
        self.token_sesion = None
        self.state.set("usuario_actual", None)
        self.state.set("token_sesion", None)

        # Cerrar todos los diálogos abiertos en el overlay
        for control in self.page.overlay:
            if hasattr(control, 'open'):
                control.open = False
        self.page.update()

        # Limpiar la página completamente
        self.page.controls.clear()
        self.page.overlay.clear()

        # Crear nueva instancia de login y limpiar formulario
        self.login_page = LoginPage(self.page, self._on_login_success)
        login_view = self.login_page.build()
        self.login_page.limpiar_formulario()

        self.page.add(login_view)
        self.page.update()

    def _cerrar_dialog(self, dialog):
        """Cierra un diálogo"""
        dialog.open = False
        self.page.update()


def main(page: ft.Page):
    page.title = Settings.APP_TITLE
    page.bgcolor = AppColors.BACKGROUND

    # Configuraciones de ventana solo para desktop
    if not page.web:
        page.window.width = Settings.WINDOW_WIDTH
        page.window.height = Settings.WINDOW_HEIGHT
        page.window.min_width = Settings.WINDOW_MIN_WIDTH
        page.window.min_height = Settings.WINDOW_MIN_HEIGHT

    # Configurar tema global
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=AppColors.PRIMARY,
            on_primary=ft.Colors.WHITE,
            surface=AppColors.CARD_BG,
            on_surface=AppColors.TEXT_PRIMARY,
            surface_variant=AppColors.INPUT_BG,
            outline=AppColors.INPUT_BORDER,
        ),
    )

    app = MainApp(page)
    page.add(app.build())


if __name__ == "__main__":
    # Para web, usar: flet run --web main.py
    # Para desktop, usar: python main.py o flet run main.py
    ft.app(target=main, assets_dir="assets")
    
    
"""
🚀 Para usar el sistema:
Ejecutar migración:
python database/migrate_add_abonos.py
Iniciar aplicación:
python main.py
Login inicial:
Usuario: admin
Contraseña: admin
Crear usuarios adicionales:
Solo SuperAdmin puede acceder a la opción "Usuarios"
Crear vendedores y/o más SuperAdmins
"""
