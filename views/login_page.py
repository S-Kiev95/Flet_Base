"""Página de login"""

import flet as ft
from config.settings import AppColors
from database.connection import get_session_context
from database.db_service import UsuarioRepository, SesionRepository


class LoginPage:
    """Página de inicio de sesión"""

    def __init__(self, page: ft.Page, on_login_success):
        self.page = page
        self.on_login_success = on_login_success  # Callback cuando el login es exitoso
        self.container = None

        # Campos del formulario
        self.nombre_field = ft.TextField(
            label="Usuario",
            prefix_icon=ft.Icons.PERSON,
            autofocus=True,
            color=AppColors.TEXT_PRIMARY,
            bgcolor=AppColors.INPUT_BG,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
            on_submit=lambda e: self._intentar_login(e),
        )

        self.contraseña_field = ft.TextField(
            label="Contraseña",
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            color=AppColors.TEXT_PRIMARY,
            bgcolor=AppColors.INPUT_BG,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
            on_submit=lambda e: self._intentar_login(e),
        )

        self.error_text = ft.Text(
            "",
            color=AppColors.DANGER,
            size=14,
            visible=False,
        )

        self.loading = ft.ProgressRing(visible=False, width=30, height=30)

    def build(self):
        """Construye la interfaz de login"""

        self.container = ft.Container(
            content=ft.Column([
                # Logo o título
                ft.Container(
                    content=ft.Column([
                        ft.Icon(
                            ft.Icons.STORE,
                            size=80,
                            color=AppColors.PRIMARY,
                        ),
                        ft.Text(
                            "La Milagrosa",
                            size=32,
                            weight=ft.FontWeight.BOLD,
                            color=AppColors.TEXT_PRIMARY,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            "Sistema de Ventas",
                            size=16,
                            color=AppColors.TEXT_SECONDARY,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10),
                    margin=ft.margin.only(bottom=40),
                ),

                # Card de login
                ft.Container(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(
                                "Iniciar Sesión",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color=AppColors.TEXT_PRIMARY,
                                text_align=ft.TextAlign.CENTER,
                            ),

                            ft.Divider(color=AppColors.CARD_BORDER),

                            self.nombre_field,
                            self.contraseña_field,
                            self.error_text,

                            ft.Container(height=10),

                            ft.ElevatedButton(
                                "Iniciar Sesión",
                                icon=ft.Icons.LOGIN,
                                width=300,
                                height=50,
                                bgcolor=AppColors.PRIMARY,
                                color=ft.Colors.WHITE,
                                on_click=self._intentar_login,
                            ),

                            self.loading,

                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=15),
                        padding=40,
                        width=400,
                    ),
                    bgcolor=AppColors.LOGIN_CARD,
                    border_radius=12,
                    shadow=ft.BoxShadow(
                        spread_radius=0,
                        blur_radius=10,
                        color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                        offset=ft.Offset(0, 4),
                    ),
                ),

                # Info adicional
                ft.Container(
                    content=ft.Text(
                        "Usuario por defecto: admin / admin",
                        size=12,
                        color=AppColors.TEXT_SECONDARY,
                        italic=True,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    margin=ft.margin.only(top=20),
                ),

            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=0),
            expand=True,
            alignment=ft.alignment.center,
            bgcolor=AppColors.LOGIN_BG,
        )

        return self.container

    def _intentar_login(self, e):
        """Intenta autenticar al usuario"""

        # Validar campos
        nombre = self.nombre_field.value.strip() if self.nombre_field.value else ""
        contraseña = self.contraseña_field.value if self.contraseña_field.value else ""

        if not nombre:
            self._mostrar_error("Por favor ingrese su usuario")
            return

        if not contraseña:
            self._mostrar_error("Por favor ingrese su contraseña")
            return

        # Mostrar loading
        self.loading.visible = True
        self.error_text.visible = False
        self.page.update()

        try:
            session = get_session_context()

            # Autenticar usuario
            usuario = UsuarioRepository.autenticar(session, nombre, contraseña)

            if not usuario:
                session.close()
                self._mostrar_error("Usuario o contraseña incorrectos")
                self.loading.visible = False
                self.page.update()
                return

            # Crear sesión
            sesion = SesionRepository.iniciar_sesion(session, usuario.id, duracion_horas=8)

            # Extraer datos ANTES de cerrar la sesión para evitar DetachedInstanceError
            usuario_data = {
                "id": usuario.id,
                "nombre": usuario.nombre,
                "rol": usuario.rol,
                "activo": usuario.activo,
            }
            token = sesion.token

            session.close()

            # Crear objeto usuario con los datos extraídos para pasar al callback
            from models.usuario import Usuario
            usuario_obj = Usuario(
                id=usuario_data["id"],
                nombre=usuario_data["nombre"],
                rol=usuario_data["rol"],
                activo=usuario_data["activo"],
            )

            # Llamar al callback de éxito
            self.on_login_success(usuario_obj, token)

        except Exception as error:
            self._mostrar_error(f"Error al iniciar sesión: {error}")
            self.loading.visible = False
            self.page.update()

    def _mostrar_error(self, mensaje: str):
        """Muestra un mensaje de error"""
        self.error_text.value = mensaje
        self.error_text.visible = True
        self.loading.visible = False
        self.page.update()

    def limpiar_formulario(self):
        """Limpia los campos del formulario"""
        self.nombre_field.value = ""
        self.contraseña_field.value = ""
        self.error_text.visible = False
        self.loading.visible = False
