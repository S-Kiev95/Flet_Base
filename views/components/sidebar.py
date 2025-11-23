import flet as ft
from config.settings import AppColors


class Sidebar:
    """Sidebar con navegación moderna y expansible"""

    def __init__(self, page, router, usuario=None, on_logout=None):
        self.page = page
        self.router = router
        self.usuario = usuario  # Usuario logueado
        self.on_logout = on_logout  # Callback para cerrar sesión
        self.active_route = None
        self.buttons = []
        self.is_expanded = True
        self.container = None
        self.sidebar_container = None

    def build(self):
        # Botón de toggle
        self.toggle_btn = ft.IconButton(
            icon=ft.Icons.MENU,
            icon_color=ft.Colors.WHITE,
            tooltip="Expandir/Colapsar menú",
            on_click=self._toggle_sidebar
        )

        # Logo y título
        self.logo_text = ft.Text(
            "LaMilagrosa",
            size=18,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE,
            visible=True,
        )
        
        logo_content = ft.Column(
            [
                self.logo_text,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=5,
        )

        self.logo_container = ft.Container(
            content=logo_content,
            padding=15,
            bgcolor=AppColors.SIDEBAR_HEADER,
            border_radius=ft.border_radius.all(12),
            margin=ft.margin.only(bottom=15),
            alignment=ft.alignment.center,
        )

        # Información del usuario
        self.usuario_text = ft.Text(
            self.usuario.nombre if self.usuario else "Usuario",
            size=14,
            color=ft.Colors.WHITE,
            weight=ft.FontWeight.BOLD,
            visible=True,
        )

        self.rol_text = ft.Text(
            self.usuario.rol if self.usuario else "",
            size=11,
            color=ft.Colors.GREY_400,
            visible=True,
        )

        usuario_info = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.ACCOUNT_CIRCLE, color=ft.Colors.WHITE, size=40),
                self.usuario_text,
                self.rol_text,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=5),
            padding=10,
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
            border_radius=8,
            margin=ft.margin.only(bottom=15),
        )

        # Botones de navegación (incluir usuarios solo para SuperAdmin)
        nav_buttons = [
            self._create_nav_button("Clientes", ft.Icons.PEOPLE, "clientes"),
            self._create_nav_button("Productos", ft.Icons.INVENTORY_2, "productos"),
            self._create_nav_button("Ventas", ft.Icons.POINT_OF_SALE, "ventas"),
        ]

        # Agregar botón de usuarios solo para SuperAdmin
        if self.usuario and self.usuario.es_superadmin():
            nav_buttons.append(
                self._create_nav_button("Usuarios", ft.Icons.ADMIN_PANEL_SETTINGS, "usuarios", color=ft.Colors.WHITE)
            )

        # Contenido de la sidebar
        sidebar_content = ft.Column(
            [
                ft.Row(
                    [self.toggle_btn],
                    alignment=ft.MainAxisAlignment.END,
                ),
                self.logo_container,
                usuario_info,
                *nav_buttons,
                ft.Container(expand=True),
                self._create_action_button("Cerrar Sesión", ft.Icons.LOGOUT, self._cerrar_sesion, color=ft.Colors.WHITE),
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Container principal con animación
        self.sidebar_container = ft.Container(
            content=sidebar_content,
            width=220,
            bgcolor=AppColors.SIDEBAR_BG,
            padding=15,
            border_radius=ft.border_radius.only(top_right=12, bottom_right=12),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=8,
                color=ft.Colors.BLACK26,
                offset=ft.Offset(2, 0),
            ),
            animate=ft.Animation(300, ft.AnimationCurve.EASE_IN_BACK),
        )

        return self.sidebar_container

    def _create_nav_button(self, text: str, icon, route: str, color=ft.Colors.WHITE):
        base_color = ft.Colors.with_opacity(0.05, ft.Colors.WHITE)
        hover_color = ft.Colors.with_opacity(0.15, ft.Colors.WHITE)
        active_color = AppColors.SIDEBAR_ACCENT

        icon_ref = ft.Icon(icon, color=color, size=15)
        text_ref = ft.Text(
            text, 
            color=color, 
            size=15, 
            weight=ft.FontWeight.W_500,
            visible=True
        )
        
        btn_row = ft.Row(
            [icon_ref, text_ref],
            spacing=10,
            alignment=ft.MainAxisAlignment.START,
        )
        
        btn_container = ft.Container(
            content=btn_row,
            padding=ft.padding.symmetric(horizontal=15, vertical=12),
            border_radius=ft.border_radius.all(8),
            bgcolor=base_color,
            alignment=ft.alignment.center_left,
        )

        def update_active_style(is_active: bool):
            btn_container.bgcolor = active_color if is_active else base_color
            icon_ref.color = ft.Colors.WHITE if is_active else color
            text_ref.color = ft.Colors.WHITE if is_active else color
            btn_container.update()

        def on_tap(e):
            self.active_route = route
            self.router.navigate(route)
            self._refresh_sidebar()

        def on_hover(e):
            if route != self.active_route:
                btn_container.bgcolor = hover_color if e.data == "true" else base_color
                btn_container.update()

        btn = ft.GestureDetector(
            content=btn_container,
            on_tap=on_tap,
            on_hover=on_hover,
        )

        # Guardamos el botón con su texto para poder ocultarlo/mostrarlo
        self.buttons.append((btn, update_active_style, route, text_ref))
        return btn

    def _toggle_sidebar(self, e):
        """Alterna entre sidebar expandida y colapsada"""
        self.is_expanded = not self.is_expanded

        if self.is_expanded:
            # Expandir
            self.sidebar_container.width = 220
            self.logo_text.visible = True
            self.usuario_text.visible = True
            self.rol_text.visible = True
            # Mostrar todos los textos de los botones y alinear a la izquierda
            for btn, update_style, route, text_ref in self.buttons:
                text_ref.visible = True
                btn.content.alignment = ft.alignment.center_left
                btn.content.padding = ft.padding.symmetric(horizontal=15, vertical=12)
        else:
            # Colapsar
            self.sidebar_container.width = 70
            self.logo_text.visible = False
            self.usuario_text.visible = False
            self.rol_text.visible = False
            # Ocultar todos los textos de los botones y centrar íconos
            for btn, update_style, route, text_ref in self.buttons:
                text_ref.visible = False
                btn.content.alignment = ft.alignment.center
                btn.content.padding = ft.padding.all(12)

        self.page.update()

    def _refresh_sidebar(self):
        """Actualiza el estilo de los botones según la ruta activa"""
        for btn, update_style, route, text_ref in self.buttons:
            update_style(route == self.active_route)
        self.page.update()

    def _create_action_button(self, text: str, icon, on_click_handler, color=ft.Colors.WHITE):
        """Crea un botón de acción (no de navegación)"""
        base_color = ft.Colors.with_opacity(0.05, ft.Colors.WHITE)
        hover_color = ft.Colors.with_opacity(0.15, ft.Colors.WHITE)

        icon_ref = ft.Icon(icon, color=color, size=15)
        text_ref = ft.Text(
            text,
            color=color,
            size=15,
            weight=ft.FontWeight.W_500,
            visible=True
        )

        btn_row = ft.Row(
            [icon_ref, text_ref],
            spacing=10,
            alignment=ft.MainAxisAlignment.START,
        )

        btn_container = ft.Container(
            content=btn_row,
            padding=ft.padding.symmetric(horizontal=15, vertical=12),
            border_radius=ft.border_radius.all(8),
            bgcolor=base_color,
            alignment=ft.alignment.center_left,
        )

        def on_tap(e):
            on_click_handler()

        def on_hover(e):
            btn_container.bgcolor = hover_color if e.data == "true" else base_color
            btn_container.update()

        btn = ft.GestureDetector(
            content=btn_container,
            on_tap=on_tap,
            on_hover=on_hover,
        )

        # Guardamos también el text_ref para ocultarlo/mostrarlo al colapsar
        self.buttons.append((btn, lambda x: None, "action", text_ref))
        return btn

    def _cerrar_sesion(self):
        """Maneja el cierre de sesión"""
        if self.on_logout:
            self.on_logout()