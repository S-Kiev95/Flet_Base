"""Vista de gestión de usuarios"""

import flet as ft
from typing import List
from datetime import datetime
from models.usuario import Usuario, RolUsuario
from database.connection import get_session_context
from database.db_service import UsuarioRepository
from config.settings import AppColors


class UsuariosPage:
    """Página de gestión de usuarios (solo para SuperAdmin)"""

    def __init__(self, state, api, page):
        self.state = state
        self.api = api
        self.page = page
        self.container = None

        # Componentes
        self.search_field = ft.TextField(
            label="Buscar usuario por nombre",
            prefix_icon=ft.Icons.SEARCH,
            color=AppColors.PRIMARY,
            bgcolor=AppColors.INPUT_BG,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
            on_change=self._on_search_change,
            expand=True,
        )

        self.usuarios_list = ft.Column(
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )

        self.loading = ft.ProgressRing(visible=False)

        # Lista completa de usuarios (para filtrar)
        self.todos_usuarios: List[Usuario] = []

    def build(self):
        """Construye la interfaz de la página"""

        self.container = ft.Container(
            content=ft.Column([
                # Header
                ft.Row([
                    ft.Text(
                        "Gestión de Usuarios",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.PRIMARY
                    ),
                    ft.IconButton(
                        icon=ft.Icons.REFRESH,
                        tooltip="Recargar lista",
                        on_click=self._cargar_usuarios,
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                ft.Divider(),

                # Barra de búsqueda
                ft.Row([
                    self.search_field,
                    ft.ElevatedButton(
                        "Nuevo Usuario",
                        icon=ft.Icons.PERSON_ADD,
                        bgcolor=AppColors.PRIMARY,
                        color=ft.Colors.WHITE,
                        on_click=self._nuevo_usuario,
                    ),
                ]),

                # Indicador de carga
                self.loading,

                # Lista de usuarios
                ft.Container(
                    content=self.usuarios_list,
                    expand=True,
                ),

            ]),
            padding=20,
            expand=True,
        )

        # Cargar usuarios al iniciar
        self._cargar_usuarios(None)

        return self.container

    def _cargar_usuarios(self, e):
        """Carga la lista de usuarios desde la base de datos"""
        self.loading.visible = True
        self.page.update()

        try:
            session = get_session_context()
            self.todos_usuarios = UsuarioRepository.listar_todos(session)
            session.close()

            self._aplicar_filtros()

        except Exception as error:
            self._mostrar_error(f"Error al cargar usuarios: {error}")
        finally:
            self.loading.visible = False
            self.page.update()

    def _on_search_change(self, e):
        """Filtra la lista cuando cambia el texto de búsqueda"""
        self._aplicar_filtros()

    def _aplicar_filtros(self):
        """Aplica todos los filtros activos"""
        texto_busqueda = self.search_field.value.lower().strip() if self.search_field.value else ""

        # Filtrar por nombre
        usuarios_filtrados = self.todos_usuarios

        if texto_busqueda:
            usuarios_filtrados = [
                u for u in usuarios_filtrados
                if texto_busqueda in u.nombre.lower()
            ]

        self._actualizar_lista(usuarios_filtrados)

    def _actualizar_lista(self, usuarios: List[Usuario]):
        """Actualiza la lista visual de usuarios"""
        self.usuarios_list.controls.clear()

        if not usuarios:
            self.usuarios_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No se encontraron usuarios",
                        size=16,
                        color=AppColors.PRIMARY,
                        italic=True,
                    ),
                    padding=20,
                    alignment=ft.alignment.center,
                )
            )
        else:
            for usuario in usuarios:
                self.usuarios_list.controls.append(
                    self._crear_card_usuario(usuario)
                )

        self.page.update()

    def _crear_card_usuario(self, usuario: Usuario) -> ft.Card:
        """Crea una tarjeta para mostrar un usuario"""

        # Color según rol
        rol_color = ft.Colors.PURPLE_600 if usuario.es_superadmin() else ft.Colors.BLUE_600
        estado_color = AppColors.SUCCESS if usuario.activo else AppColors.DANGER
        estado_texto = "Activo" if usuario.activo else "Inactivo"

        # Botones de acción
        botones_accion = [
            ft.IconButton(
                icon=ft.Icons.EDIT,
                icon_color=ft.Colors.ORANGE_400,
                tooltip="Editar",
                on_click=lambda e, u=usuario: self._editar_usuario(u),
            ),
        ]

        # Solo permitir eliminar si no es el último SuperAdmin
        if not (usuario.es_superadmin() and self._es_ultimo_superadmin()):
            botones_accion.append(
                ft.IconButton(
                    icon=ft.Icons.DELETE if usuario.activo else ft.Icons.RESTORE,
                    icon_color=AppColors.DANGER if usuario.activo else AppColors.SUCCESS,
                    tooltip="Desactivar" if usuario.activo else "Reactivar",
                    on_click=lambda e, u=usuario: self._toggle_estado_usuario(u),
                )
            )

        return ft.Card(
            content=ft.Container(
                content=ft.Row([
                    # Información principal
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.PERSON, size=20, color=ft.Colors.WHITE),
                                ft.Text(
                                    usuario.nombre,
                                    size=18,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                ),
                            ]),

                            ft.Row([
                                ft.Container(
                                    content=ft.Text(
                                        usuario.rol,
                                        size=12,
                                        color=ft.Colors.WHITE,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    bgcolor=rol_color,
                                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                    border_radius=5,
                                ),
                                ft.Container(
                                    content=ft.Text(
                                        estado_texto,
                                        size=12,
                                        color=ft.Colors.WHITE,
                                    ),
                                    bgcolor=estado_color,
                                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                    border_radius=5,
                                ),
                            ], spacing=10),

                            ft.Text(
                                f"Último acceso: {usuario.ultimo_acceso.strftime('%d/%m/%Y %H:%M') if usuario.ultimo_acceso else 'Nunca'}",
                                size=12,
                                color=ft.Colors.WHITE70,
                            ),

                        ], spacing=8),
                        expand=True,
                    ),

                    # Botones de acción
                    ft.Container(
                        content=ft.Row(botones_accion, spacing=0),
                        width=100,
                    ),

                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=15,
                bgcolor=AppColors.CARD_DARK,
                border_radius=10,
            ),
            elevation=2 if usuario.activo else 1,
        )

    def _es_ultimo_superadmin(self) -> bool:
        """Verifica si solo hay un SuperAdmin activo"""
        superadmins_activos = [u for u in self.todos_usuarios if u.es_superadmin() and u.activo]
        return len(superadmins_activos) == 1

    def _nuevo_usuario(self, e):
        """Abre el modal para crear un nuevo usuario"""

        # Campos del formulario
        nombre_field = ft.TextField(
            label="Nombre de usuario *",
            hint_text="juan_perez",
            autofocus=True,
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )

        rol_dropdown = ft.Dropdown(
            label="Rol *",
            options=[
                ft.dropdown.Option(RolUsuario.VENDEDOR.value, "Vendedor"),
                ft.dropdown.Option(RolUsuario.SUPERADMIN.value, "SuperAdmin"),
            ],
            value=RolUsuario.VENDEDOR.value,
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
            bgcolor=ft.Colors.WHITE,
            fill_color=ft.Colors.WHITE,
        )

        contraseña_field = ft.TextField(
            label="Contraseña *",
            password=True,
            can_reveal_password=True,
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )

        def guardar_usuario(e):
            # Validar campos requeridos
            if not nombre_field.value or nombre_field.value.strip() == "":
                self._mostrar_error("El nombre es obligatorio")
                return

            if not contraseña_field.value:
                self._mostrar_error("La contraseña es obligatoria")
                return

            try:
                # Verificar que el nombre no exista
                session = get_session_context()
                usuario_existente = UsuarioRepository.obtener_por_nombre(session, nombre_field.value.strip())

                if usuario_existente:
                    session.close()
                    self._mostrar_error("Ya existe un usuario con ese nombre")
                    return

                # Crear usuario
                nuevo_usuario = Usuario(
                    nombre=nombre_field.value.strip(),
                    rol=rol_dropdown.value,
                    contraseña=contraseña_field.value,
                )

                UsuarioRepository.crear(session, nuevo_usuario)
                session.close()

                # Cerrar modal y recargar lista
                modal.open = False
                self.page.update()
                self._mostrar_exito(f"Usuario '{nuevo_usuario.nombre}' creado exitosamente")
                self._cargar_usuarios(None)

            except Exception as error:
                self._mostrar_error(f"Error al crear usuario: {error}")

        # Crear modal
        modal = ft.AlertDialog(
            modal=True,
            bgcolor=AppColors.MODAL_BG,
            title=ft.Text("Nuevo Usuario", size=20, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
            content=ft.Container(
                content=ft.Column([
                    nombre_field,
                    rol_dropdown,
                    contraseña_field,
                    ft.Text(
                        "Nota: La contraseña se almacena en texto plano",
                        size=11,
                        color=ft.Colors.ORANGE_700,
                        italic=True,
                    ),
                ], tight=True, spacing=15),
                width=400,
            ),
            actions=[
                ft.TextButton("Cancelar", style=ft.ButtonStyle(color=AppColors.PRIMARY), on_click=lambda e: self._cerrar_modal(modal)),
                ft.ElevatedButton("Guardar", bgcolor=AppColors.PRIMARY, color=ft.Colors.WHITE, on_click=guardar_usuario),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(modal)
        modal.open = True
        self.page.update()

    def _editar_usuario(self, usuario: Usuario):
        """Abre el modal para editar un usuario"""

        # Campos del formulario pre-llenados
        nombre_field = ft.TextField(
            label="Nombre de usuario *",
            value=usuario.nombre,
            autofocus=True,
            disabled=True,  # No permitir cambiar el nombre
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )

        rol_dropdown = ft.Dropdown(
            label="Rol *",
            options=[
                ft.dropdown.Option(RolUsuario.VENDEDOR.value, "Vendedor"),
                ft.dropdown.Option(RolUsuario.SUPERADMIN.value, "SuperAdmin"),
            ],
            value=usuario.rol,
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )

        contraseña_field = ft.TextField(
            label="Nueva contraseña (dejar vacío para no cambiar)",
            password=True,
            can_reveal_password=True,
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )

        def actualizar_usuario(e):
            try:
                # Validar que no sea el último SuperAdmin si se intenta cambiar el rol
                if usuario.es_superadmin() and rol_dropdown.value != RolUsuario.SUPERADMIN.value:
                    if self._es_ultimo_superadmin():
                        self._mostrar_error("No puedes cambiar el rol del último SuperAdmin")
                        return

                # Actualizar datos del usuario
                usuario.rol = rol_dropdown.value

                if contraseña_field.value:
                    usuario.contraseña = contraseña_field.value

                usuario.fecha_actualizacion = datetime.now()

                # Guardar en BD
                session = get_session_context()
                UsuarioRepository.actualizar(session, usuario)
                session.close()

                # Cerrar modal y recargar lista
                modal.open = False
                self.page.update()
                self._mostrar_exito(f"Usuario '{usuario.nombre}' actualizado exitosamente")
                self._cargar_usuarios(None)

            except Exception as error:
                self._mostrar_error(f"Error al actualizar usuario: {error}")

        modal = ft.AlertDialog(
            modal=True,
            bgcolor=AppColors.MODAL_BG,
            title=ft.Text("Editar Usuario", size=20, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
            content=ft.Container(
                content=ft.Column([
                    nombre_field,
                    rol_dropdown,
                    contraseña_field,
                ], tight=True, spacing=15),
                width=400,
            ),
            actions=[
                ft.TextButton("Cancelar", style=ft.ButtonStyle(color=AppColors.PRIMARY), on_click=lambda e: self._cerrar_modal(modal)),
                ft.ElevatedButton("Actualizar", bgcolor=AppColors.PRIMARY, color=ft.Colors.WHITE, on_click=actualizar_usuario),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(modal)
        modal.open = True
        self.page.update()

    def _toggle_estado_usuario(self, usuario: Usuario):
        """Activa o desactiva un usuario"""

        accion = "desactivar" if usuario.activo else "reactivar"

        def confirmar(e):
            try:
                # Validar que no sea el último SuperAdmin
                if usuario.es_superadmin() and usuario.activo:
                    if self._es_ultimo_superadmin():
                        self._mostrar_error("No puedes desactivar el último SuperAdmin")
                        return

                # Cambiar estado
                usuario.activo = not usuario.activo
                usuario.fecha_actualizacion = datetime.now()

                # Guardar en BD
                session = get_session_context()
                UsuarioRepository.actualizar(session, usuario)
                session.close()

                # Cerrar modal y recargar lista
                modal.open = False
                self.page.update()
                self._mostrar_exito(f"Usuario '{usuario.nombre}' {accion}do exitosamente")
                self._cargar_usuarios(None)

            except Exception as error:
                self._mostrar_error(f"Error al {accion} usuario: {error}")

        modal = ft.AlertDialog(
            modal=True,
            bgcolor=AppColors.MODAL_BG,
            title=ft.Text(f"Confirmar {accion}ción", size=18, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
            content=ft.Text(
                f"¿Estás seguro de que deseas {accion} al usuario '{usuario.nombre}'?",
                size=16,
            ),
            actions=[
                ft.TextButton("Cancelar", style=ft.ButtonStyle(color=AppColors.PRIMARY), on_click=lambda e: self._cerrar_modal(modal)),
                ft.ElevatedButton(
                    accion.capitalize(),
                    bgcolor=AppColors.DANGER if usuario.activo else AppColors.SUCCESS,
                    color=ft.Colors.WHITE,
                    on_click=confirmar,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(modal)
        modal.open = True
        self.page.update()

    # ============================================
    # HELPERS
    # ============================================
    def _cerrar_modal(self, modal):
        """Cierra un modal"""
        modal.open = False
        self.page.update()

    def _mostrar_error(self, mensaje: str):
        """Muestra un mensaje de error"""
        snack = ft.SnackBar(
            content=ft.Text(mensaje),
            bgcolor=AppColors.DANGER,
        )
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

    def _mostrar_exito(self, mensaje: str):
        """Muestra un mensaje de éxito"""
        snack = ft.SnackBar(
            content=ft.Text(mensaje),
            bgcolor=AppColors.SUCCESS,
        )
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()
