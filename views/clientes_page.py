"""Vista de gestión de clientes"""

import flet as ft
from typing import List, Optional
from datetime import datetime
from models.cliente import Cliente
from database.connection import get_session_context
from database.db_service import ClienteRepository, VentaRepository, AbonoRepository
from config.settings import AppColors

from utils.pdf_generator import PDFGenerator


class ClientesPage:
    """Página de gestión de clientes"""
    
    def __init__(self, state, api, page):
        self.state = state
        self.api = api
        self.page = page
        self.container = None
        
        # Componentes
        self.search_field = ft.TextField(
            label="Buscar cliente por nombre",
            prefix_icon=ft.Icons.SEARCH,
            color=AppColors.PRIMARY,
            bgcolor=AppColors.INPUT_BG,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
            on_change=self._on_search_change,
            expand=True,
        )

        # Nuevo: Checkbox para filtrar clientes con deuda
        self.filter_deuda_checkbox = ft.Checkbox(
            label="Solo con deuda",
            value=False,
            label_style=ft.TextStyle(color=AppColors.PRIMARY),
            on_change=self._on_filter_change,
        )
        
        self.clientes_list = ft.Column(
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )
        
        self.loading = ft.ProgressRing(visible=False)
        
        # Lista completa de clientes (para filtrar)
        self.todos_clientes: List[Cliente] = []
    
    def build(self):
        """Construye la interfaz de la página"""
        
        self.container = ft.Container(
            content=ft.Column([
                # Header
                ft.Row([
                    ft.Text(
                        "Gestión de Clientes",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.PRIMARY
                    ),
                    ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.SYNC,
                            tooltip="Sincronizar todas las deudas",
                            icon_color=ft.Colors.ORANGE_600,
                            on_click=self._sincronizar_todas_deudas,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.REFRESH,
                            tooltip="Recargar lista",
                            on_click=self._cargar_clientes,
                        ),
                    ]),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Divider(),
                
                # Barra de búsqueda y filtros
                ft.Row([
                    self.search_field,
                    self.filter_deuda_checkbox,
                    ft.ElevatedButton(
                        "Nuevo Cliente",
                        icon=ft.Icons.ADD,
                        bgcolor=AppColors.PRIMARY,
                        color=ft.Colors.WHITE,
                        on_click=self._nuevo_cliente,
                    ),
                ]),
                
                # Indicador de carga
                self.loading,
                
                # Lista de clientes
                ft.Container(
                    content=self.clientes_list,
                    expand=True,
                ),
                
            ]),
            padding=20,
            expand=True,
        )
        
        # Cargar clientes al iniciar
        self._cargar_clientes(None)
        
        return self.container
    
    def _cargar_clientes(self, e):
        """Carga la lista de clientes desde la base de datos"""
        self.loading.visible = True
        self.page.update()

        try:
            session = get_session_context()

            # Obtener clientes
            self.todos_clientes = ClienteRepository.listar_activos(session)

            # Sincronizar deuda de cada cliente con la realidad
            for cliente in self.todos_clientes:
                deuda_real = ClienteRepository.calcular_deuda_real(session, cliente.id)
                # Actualizar en memoria para mostrar correctamente
                cliente.deuda_total = deuda_real

            session.close()

            self._aplicar_filtros()

        except Exception as error:
            self._mostrar_error(f"Error al cargar clientes: {error}")
        finally:
            self.loading.visible = False
            self.page.update()
    
    def _on_search_change(self, e):
        """Filtra la lista cuando cambia el texto de búsqueda"""
        self._aplicar_filtros()
    
    def _on_filter_change(self, e):
        """Filtra la lista cuando cambia el checkbox de deuda"""
        self._aplicar_filtros()
    
    def _aplicar_filtros(self):
        """Aplica todos los filtros activos"""
        texto_busqueda = self.search_field.value.lower().strip() if self.search_field.value else ""
        solo_con_deuda = self.filter_deuda_checkbox.value
        
        # Filtrar por nombre
        clientes_filtrados = self.todos_clientes
        
        if texto_busqueda:
            clientes_filtrados = [
                c for c in clientes_filtrados
                if texto_busqueda in c.nombre.lower()
            ]
        
        # Filtrar por deuda
        if solo_con_deuda:
            clientes_filtrados = [
                c for c in clientes_filtrados
                if c.tiene_deuda()
            ]
        
        self._actualizar_lista(clientes_filtrados)
    
    def _actualizar_lista(self, clientes: List[Cliente]):
        """Actualiza la lista visual de clientes"""
        self.clientes_list.controls.clear()
        
        if not clientes:
            self.clientes_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No se encontraron clientes",
                        size=16,
                        color=AppColors.PRIMARY,
                        italic=True,
                    ),
                    padding=20,
                    alignment=ft.alignment.center,
                )
            )
        else:
            for cliente in clientes:
                self.clientes_list.controls.append(
                    self._crear_card_cliente(cliente)
                )
        
        self.page.update()
    
    def _crear_card_cliente(self, cliente: Cliente) -> ft.Card:
        """Crea una tarjeta para mostrar un cliente"""
        
        # Indicador de deuda
        tiene_deuda = cliente.tiene_deuda()
        deuda_color = AppColors.DANGER if tiene_deuda else AppColors.SUCCESS
        deuda_texto = f"Deuda: ${cliente.deuda_total:.2f}" if tiene_deuda else "Sin deuda"
        
        # Botones de acción
        botones_accion = [
            ft.IconButton(
                icon=ft.Icons.VISIBILITY,
                icon_color=ft.Colors.BLUE_400,
                tooltip="Ver detalles",
                on_click=lambda e, c=cliente: self._ver_cliente(c),
            ),
            ft.IconButton(
                icon=ft.Icons.HISTORY,
                icon_color=ft.Colors.PURPLE_400,
                tooltip="Ver historial de compras y pagos",
                on_click=lambda e, c=cliente: self._ver_historial_cliente(c),
            ),
            ft.IconButton(
                icon=ft.Icons.EDIT,
                icon_color=ft.Colors.ORANGE_400,
                tooltip="Editar",
                on_click=lambda e, c=cliente: self._editar_cliente(c),
            ),
        ]
        
        # Agregar botón de gestionar pagos solo si tiene deuda
        if tiene_deuda:
            botones_accion.append(
                ft.IconButton(
                    icon=ft.Icons.PAYMENTS,
                    icon_color=ft.Colors.GREEN_600,
                    tooltip="Gestionar pagos",
                    on_click=lambda e, c=cliente: self._mostrar_opciones_pago(c),
                )
            )
        
        botones_accion.append(
            ft.IconButton(
                icon=ft.Icons.DELETE,
                icon_color=AppColors.DANGER,
                tooltip="Eliminar",
                on_click=lambda e, c=cliente: self._confirmar_eliminacion(c),
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
                                    cliente.nombre,
                                    size=18,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                ),
                            ]),

                            # Información de contacto
                            ft.Row([
                                ft.Icon(ft.Icons.PHONE, size=16, color=ft.Colors.WHITE70),
                                ft.Text(
                                    cliente.telefono or "Sin teléfono",
                                    size=14,
                                    color=ft.Colors.WHITE70,
                                ),
                            ], spacing=5) if cliente.telefono else ft.Container(),

                            ft.Row([
                                ft.Icon(ft.Icons.LOCATION_ON, size=16, color=ft.Colors.WHITE70),
                                ft.Text(
                                    cliente.direccion or "Sin dirección",
                                    size=14,
                                    color=ft.Colors.WHITE70,
                                ),
                            ], spacing=5) if cliente.direccion else ft.Container(),

                        ], spacing=5),
                        expand=True,
                    ),

                    # Información de crédito y deuda
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                deuda_texto,
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=deuda_color,
                            ),
                            ft.Text(
                                f"Límite: ${cliente.limite_credito:.2f}",
                                size=12,
                                color=ft.Colors.WHITE70,
                            ),
                        ], spacing=3),
                        width=150,
                    ),

                    # Botones de acción
                    ft.Container(
                        content=ft.Row(botones_accion, spacing=0),
                        width=tiene_deuda and 220 or 180,  # Más ancho si tiene botón de liquidar
                    ),

                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=15,
                bgcolor=AppColors.CARD_DARK,
                border_radius=10,
            ),
        )

    # ============================================
    # MODAL: OPCIONES DE PAGO
    # ============================================
    def _mostrar_opciones_pago(self, cliente: Cliente):
        """Muestra opciones para realizar pago parcial o liquidar total"""

        modal = ft.AlertDialog(
            modal=True,
            bgcolor=AppColors.MODAL_BG,
            title=ft.Row([
                ft.Icon(ft.Icons.PAYMENTS, color=ft.Colors.GREEN_600, size=30),
                ft.Text("Gestionar Pagos", size=20, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
            ]),
            content=ft.Column([
                ft.Text(
                    f"Cliente: {cliente.nombre}",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=AppColors.PRIMARY,
                ),
                ft.Container(
                    content=ft.Text(
                        f"Deuda total: ${cliente.deuda_total:.2f}",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.DANGER,
                    ),
                    bgcolor=ft.Colors.RED_50,
                    padding=15,
                    border_radius=8,
                    margin=ft.margin.only(top=10, bottom=20),
                ),
                ft.Text(
                    "Seleccione el tipo de pago:",
                    size=14,
                    color=AppColors.PRIMARY,
                ),
            ], tight=True, spacing=10),
            actions=[
                ft.TextButton("Cancelar", style=ft.ButtonStyle(color=AppColors.PRIMARY), on_click=lambda e: self._cerrar_modal(modal)),
                ft.ElevatedButton(
                    "Pago Parcial",
                    icon=ft.Icons.PAYMENTS_OUTLINED,
                    bgcolor=ft.Colors.BLUE_600,
                    color=ft.Colors.WHITE,
                    on_click=lambda e: [self._cerrar_modal(modal), self._realizar_pago_parcial(cliente)],
                ),
                ft.ElevatedButton(
                    "Liquidar Total",
                    icon=ft.Icons.PAID,
                    bgcolor=ft.Colors.GREEN_600,
                    color=ft.Colors.WHITE,
                    on_click=lambda e: [self._cerrar_modal(modal), self._confirmar_liquidacion_deuda(cliente)],
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(modal)
        modal.open = True
        self.page.update()

    # ============================================
    # MODAL: PAGO PARCIAL
    # ============================================
    def _realizar_pago_parcial(self, cliente: Cliente):
        """Permite realizar un abono parcial a la deuda del cliente"""

        # Campo para ingresar el monto
        monto_field = ft.TextField(
            label="Monto a abonar",
            hint_text="0.00",
            prefix_text="$",
            keyboard_type=ft.KeyboardType.NUMBER,
            autofocus=True,
            width=200,
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )

        # Mensaje de validación
        mensaje_error = ft.Text("", color=AppColors.DANGER, size=12, visible=False)

        def procesar_abono(e):
            try:
                # Validar monto
                monto = float(monto_field.value or 0)

                if monto <= 0:
                    mensaje_error.value = "El monto debe ser mayor a 0"
                    mensaje_error.visible = True
                    self.page.update()
                    return

                if monto > cliente.deuda_total:
                    mensaje_error.value = f"El monto no puede ser mayor a la deuda (${cliente.deuda_total:.2f})"
                    mensaje_error.visible = True
                    self.page.update()
                    return

                # Procesar el abono
                session = get_session_context()

                # Obtener todas las ventas fiadas pendientes del cliente
                ventas_pendientes = VentaRepository.listar_fiados_cliente(session, cliente.id)

                if not ventas_pendientes:
                    self._mostrar_info("El cliente no tiene ventas fiadas pendientes")
                    modal.open = False
                    self.page.update()
                    session.close()
                    return

                # Distribuir el abono entre las ventas pendientes (FIFO - primero las más antiguas)
                monto_restante = monto
                ventas_abonadas = []

                for venta in ventas_pendientes:
                    if monto_restante <= 0:
                        break

                    # Calcular cuánto abonar a esta venta
                    monto_a_abonar = min(monto_restante, venta.resto)

                    if monto_a_abonar > 0:
                        # Registrar el abono
                        VentaRepository.registrar_abono(session, venta.id, monto_a_abonar)

                        # Obtener la venta actualizada con todos los productos
                        venta_actualizada = VentaRepository.obtener_por_id(session, venta.id)

                        ventas_abonadas.append({
                            'venta': venta_actualizada,
                            'monto': monto_a_abonar
                        })
                        monto_restante -= monto_a_abonar

                # Obtener cliente actualizado
                cliente_actualizado = ClienteRepository.obtener_por_id(session, cliente.id)
                nuevo_saldo = cliente_actualizado.deuda_total

                session.close()

                # Cerrar modal
                modal.open = False
                self.page.update()

                # Mostrar diálogo para imprimir comprobante
                self._mostrar_dialogo_imprimir_liquidacion(
                    cliente_actualizado,
                    monto,
                    nuevo_saldo,
                    ventas_abonadas  # Pasar las ventas abonadas
                )

                # Recargar lista de clientes
                self._cargar_clientes(None)

            except ValueError:
                mensaje_error.value = "Ingrese un monto válido"
                mensaje_error.visible = True
                self.page.update()
            except Exception as error:
                self._mostrar_error(f"Error al procesar abono: {error}")

        modal = ft.AlertDialog(
            modal=True,
            bgcolor=AppColors.MODAL_BG,
            title=ft.Row([
                ft.Icon(ft.Icons.PAYMENTS_OUTLINED, color=ft.Colors.BLUE_600, size=30),
                ft.Text("Pago Parcial", size=20, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
            ]),
            content=ft.Column([
                ft.Text(
                    f"Cliente: {cliente.nombre}",
                    size=14,
                    color=AppColors.PRIMARY,
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            f"Deuda total: ${cliente.deuda_total:.2f}",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=AppColors.DANGER,
                        ),
                        ft.Text(
                            "Ingrese el monto que el cliente desea abonar:",
                            size=12,
                            color=AppColors.PRIMARY,
                        ),
                    ], spacing=5),
                    bgcolor=ft.Colors.BLUE_50,
                    padding=15,
                    border_radius=8,
                    margin=ft.margin.only(top=10, bottom=10),
                ),
                monto_field,
                mensaje_error,
                ft.Text(
                    "El abono se aplicará a las ventas más antiguas primero.",
                    size=11,
                    color=AppColors.PRIMARY,
                    italic=True,
                ),
            ], tight=True, spacing=10),
            actions=[
                ft.TextButton("Cancelar", style=ft.ButtonStyle(color=AppColors.PRIMARY), on_click=lambda e: self._cerrar_modal(modal)),
                ft.ElevatedButton(
                    "Procesar Abono",
                    bgcolor=ft.Colors.GREEN_600,
                    color=ft.Colors.WHITE,
                    icon=ft.Icons.CHECK_CIRCLE,
                    on_click=procesar_abono,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(modal)
        modal.open = True
        self.page.update()

    # ============================================
    # MODAL: LIQUIDAR DEUDA
    # ============================================
    def _confirmar_liquidacion_deuda(self, cliente: Cliente):
        """Muestra confirmación para liquidar todas las deudas del cliente"""
        
        def liquidar(e):
            try:
                session = get_session_context()
                
                # Obtener todas las ventas fiadas pendientes del cliente
                ventas_pendientes = VentaRepository.listar_fiados_cliente(session, cliente.id)
                
                if not ventas_pendientes:
                    self._mostrar_info("El cliente no tiene ventas fiadas pendientes")
                    modal.open = False
                    self.page.update()
                    return
                
                # Calcular saldo anterior
                saldo_anterior = cliente.deuda_total

                # Liquidar cada venta
                total_liquidado = 0
                ventas_abonadas = []

                for venta in ventas_pendientes:
                    monto_pendiente = venta.resto
                    if monto_pendiente > 0:
                        VentaRepository.registrar_abono(session, venta.id, monto_pendiente)

                        # Obtener la venta actualizada con todos los productos
                        venta_actualizada = VentaRepository.obtener_por_id(session, venta.id)

                        ventas_abonadas.append({
                            'venta': venta_actualizada,
                            'monto': monto_pendiente
                        })
                        total_liquidado += monto_pendiente

                # Actualizar cliente (recargar desde BD para obtener nuevo saldo)
                cliente_actualizado = ClienteRepository.obtener_por_id(session, cliente.id)
                nuevo_saldo = cliente_actualizado.deuda_total

                session.close()

                # Cerrar modal
                modal.open = False
                self.page.update()

                # Mostrar diálogo para imprimir comprobante
                self._mostrar_dialogo_imprimir_liquidacion(
                    cliente_actualizado,
                    total_liquidado,
                    nuevo_saldo,
                    ventas_abonadas  # Pasar las ventas abonadas
                )
                
                # Recargar lista de clientes
                self._cargar_clientes(None)
                
            except Exception as error:
                self._mostrar_error(f"Error al liquidar deudas: {error}")
        
        modal = ft.AlertDialog(
            modal=True,
            bgcolor=AppColors.MODAL_BG,
            title=ft.Row([
                ft.Icon(ft.Icons.PAYMENTS, color=ft.Colors.GREEN_600, size=30),
                ft.Text("Liquidar Deudas", size=20, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
            ]),
            content=ft.Column([
                ft.Text(
                    f"¿Confirmas que deseas liquidar todas las deudas de '{cliente.nombre}'?",
                    size=16,
                    color=AppColors.PRIMARY,
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            f"Deuda total: ${cliente.deuda_total:.2f}",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=AppColors.DANGER,
                        ),
                        ft.Text(
                            "Esta acción marcará todas las ventas fiadas como pagadas completamente.",
                            size=12,
                            color=AppColors.PRIMARY,
                            italic=True,
                        ),
                    ], spacing=5),
                    bgcolor=ft.Colors.AMBER_50,
                    padding=15,
                    border_radius=8,
                    margin=ft.margin.only(top=10, bottom=10),
                ),
            ], tight=True, spacing=10),
            actions=[
                ft.TextButton("Cancelar", style=ft.ButtonStyle(color=AppColors.PRIMARY), on_click=lambda e: self._cerrar_modal(modal)),
                ft.ElevatedButton(
                    "Liquidar Deudas",
                    bgcolor=ft.Colors.GREEN_600,
                    color=ft.Colors.WHITE,
                    icon=ft.Icons.CHECK_CIRCLE,
                    on_click=liquidar,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(modal)
        modal.open = True
        self.page.update()
    
    def _mostrar_dialogo_imprimir_liquidacion(self, cliente, abono, nuevo_saldo, ventas_pagadas=None):
        """Muestra diálogo preguntando si desea imprimir comprobante de liquidación"""

        # Referencias a los botones para poder deshabilitarlos
        btn_imprimir = None
        btn_no_imprimir = None
        progress_ring = ft.ProgressRing(visible=False, width=20, height=20)

        def imprimir_y_cerrar(e):
            try:
                es_web = getattr(self.page, 'web', False)

                # Cerrar el modal de confirmación primero
                modal.open = False
                self.page.update()

                # Usar método unificado (detecta web/desktop automáticamente)
                PDFGenerator.imprimir_o_mostrar(
                    self.page,
                    cliente=cliente,
                    abono=abono,
                    nuevo_saldo=nuevo_saldo,
                    ventas_pagadas=ventas_pagadas,
                    tipo='liquidacion'
                )

                # Solo mostrar snackbar en desktop (en web el modal del PDF ya informa)
                if not es_web:
                    self._mostrar_exito(f"Deuda liquidada. Comprobante enviado a impresora.")

            except Exception as error:
                self._mostrar_error(f"Error al generar comprobante: {error}")
        
        def no_imprimir(e):
            self._mostrar_exito(
                f"Deuda de '{cliente.nombre}' liquidada exitosamente"
            )
            modal.open = False
            self.page.update()
        
        # Crear botones con referencias
        btn_no_imprimir = ft.TextButton(
            "No, gracias",
            icon=ft.Icons.CANCEL,
            style=ft.ButtonStyle(color=AppColors.PRIMARY),
            on_click=no_imprimir,
        )

        btn_imprimir = ft.ElevatedButton(
            "Sí, imprimir",
            icon=ft.Icons.PRINT,
            bgcolor=AppColors.PRIMARY,
            color=ft.Colors.WHITE,
            on_click=imprimir_y_cerrar,
        )

        modal = ft.AlertDialog(
            modal=True,
            bgcolor=AppColors.MODAL_BG,
            title=ft.Row([
                ft.Icon(ft.Icons.PRINT, size=32, color=ft.Colors.GREEN_600),
                ft.Text("Liquidación completada", size=20, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
                progress_ring,
            ], spacing=10),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        f"Se liquidaron ${abono:.2f} de '{cliente.nombre}'",
                        size=14,
                        color=AppColors.PRIMARY,
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                f"Abono realizado: ${abono:.2f}",
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.GREEN_600,
                            ),
                            ft.Text(
                                f"Nuevo saldo: ${nuevo_saldo:.2f}",
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.GREEN_600 if nuevo_saldo == 0 else ft.Colors.ORANGE_600,
                            ),
                        ], spacing=5),
                        bgcolor=ft.Colors.GREEN_50,
                        padding=10,
                        border_radius=8,
                        margin=ft.margin.only(top=10, bottom=10),
                    ),
                    ft.Divider(),
                    ft.Text(
                        "¿Desea generar e imprimir el comprobante de pago?",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.PRIMARY,
                    ),
                ], spacing=10, tight=True),
                width=450,
            ),
            actions=[
                btn_no_imprimir,
                btn_imprimir,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(modal)
        modal.open = True
        self.page.update()
    # ============================================
    # MODAL: NUEVO CLIENTE
    # ============================================
    def _nuevo_cliente(self, e):
        """Abre el modal para crear un nuevo cliente"""
        
        # Campos del formulario
        nombre_field = ft.TextField(
            label="Nombre *",
            hint_text="Nombre completo del cliente",
            autofocus=True,
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )
        
        telefono_field = ft.TextField(
            label="Teléfono",
            hint_text="099123456",
            prefix_icon=ft.Icons.PHONE,
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )
        
        direccion_field = ft.TextField(
            label="Dirección",
            hint_text="Av. 18 de Julio 1234",
            prefix_icon=ft.Icons.LOCATION_ON,
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )
        
        email_field = ft.TextField(
            label="Email",
            hint_text="cliente@ejemplo.com",
            prefix_icon=ft.Icons.EMAIL,
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )
        
        limite_field = ft.TextField(
            label="Límite de crédito",
            hint_text="0.00",
            value="0",
            prefix_icon=ft.Icons.ATTACH_MONEY,
            keyboard_type=ft.KeyboardType.NUMBER,
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )
        
        notas_field = ft.TextField(
            label="Notas",
            hint_text="Información adicional",
            multiline=True,
            min_lines=2,
            max_lines=4,
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )
        
        def guardar_cliente(e):
            # Validar campos requeridos
            if not nombre_field.value or nombre_field.value.strip() == "":
                self._mostrar_error("El nombre es obligatorio")
                return
            
            try:
                # Crear cliente
                nuevo_cliente = Cliente(
                    nombre=nombre_field.value.strip(),
                    telefono=telefono_field.value.strip() or None,
                    direccion=direccion_field.value.strip() or None,
                    email=email_field.value.strip() or None,
                    limite_credito=float(limite_field.value or 0),
                    notas=notas_field.value.strip() or None,
                )
                
                # Guardar en BD
                session = get_session_context()
                ClienteRepository.crear(session, nuevo_cliente)
                session.close()
                
                # Cerrar modal y recargar lista
                modal.open = False
                self.page.update()
                self._mostrar_exito(f"Cliente '{nuevo_cliente.nombre}' creado exitosamente")
                self._cargar_clientes(None)
                
            except Exception as error:
                self._mostrar_error(f"Error al crear cliente: {error}")
        
        # Crear modal
        modal = ft.AlertDialog(
            modal=True,
            bgcolor=AppColors.MODAL_BG,
            title=ft.Text("Nuevo Cliente", size=20, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
            content=ft.Container(
                content=ft.Column([
                    nombre_field,
                    telefono_field,
                    direccion_field,
                    email_field,
                    limite_field,
                    notas_field,
                ], tight=True, spacing=15),
                width=500,
            ),
            actions=[
                ft.TextButton("Cancelar", style=ft.ButtonStyle(color=AppColors.PRIMARY), on_click=lambda e: self._cerrar_modal(modal)),
                ft.ElevatedButton("Guardar", bgcolor=AppColors.PRIMARY, color=ft.Colors.WHITE, on_click=guardar_cliente),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(modal)
        modal.open = True
        self.page.update()

    # ============================================
    # MODAL: VER DETALLES
    # ============================================
    def _ver_cliente(self, cliente: Cliente):
        """Muestra los detalles completos de un cliente"""
        
        # Recargar datos actuales de la BD
        session = get_session_context()
        cliente_actual = ClienteRepository.obtener_por_id(session, cliente.id)
        session.close()
        
        if not cliente_actual:
            self._mostrar_error("Cliente no encontrado")
            return
        
        # Crear contenido del modal
        contenido = ft.Column([
            # Información básica
            self._crear_campo_detalle("Nombre", cliente_actual.nombre, ft.Icons.PERSON),
            self._crear_campo_detalle("Teléfono", cliente_actual.telefono or "No especificado", ft.Icons.PHONE),
            self._crear_campo_detalle("Dirección", cliente_actual.direccion or "No especificada", ft.Icons.LOCATION_ON),
            self._crear_campo_detalle("Email", cliente_actual.email or "No especificado", ft.Icons.EMAIL),
            
            ft.Divider(),
            
            # Información financiera
            ft.Text("Información Financiera", weight=ft.FontWeight.BOLD, size=16),
            self._crear_campo_detalle("Límite de crédito", f"${cliente_actual.limite_credito:.2f}", ft.Icons.CREDIT_CARD),
            self._crear_campo_detalle(
                "Deuda actual",
                f"${cliente_actual.deuda_total:.2f}",
                ft.Icons.ACCOUNT_BALANCE_WALLET,
                color=AppColors.DANGER if cliente_actual.tiene_deuda() else AppColors.SUCCESS
            ),
            
            ft.Divider(),
            
            # Notas
            ft.Text("Notas", weight=ft.FontWeight.BOLD, size=16),
            ft.Text(cliente_actual.notas or "Sin notas adicionales", color=AppColors.PRIMARY),
            
            ft.Divider(),
            
            # Metadata
            ft.Text("Información del sistema", size=12, color=AppColors.PRIMARY),
            ft.Text(f"Creado: {cliente_actual.fecha_creacion.strftime('%d/%m/%Y %H:%M')}", size=12, color=AppColors.PRIMARY),
        ], spacing=10, scroll=ft.ScrollMode.AUTO)
        
        modal = ft.AlertDialog(
            modal=True,
            bgcolor=AppColors.MODAL_BG,
            title=ft.Row([
                ft.Icon(ft.Icons.INFO, color=ft.Colors.BLUE_400),
                ft.Text("Detalles del Cliente", size=20, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
            ]),
            content=ft.Container(content=contenido, width=500, height=400),
            actions=[
                ft.TextButton("Cerrar", style=ft.ButtonStyle(color=AppColors.PRIMARY), on_click=lambda e: self._cerrar_modal(modal)),
                ft.ElevatedButton(
                    "Editar",
                    icon=ft.Icons.EDIT,
                    bgcolor=AppColors.PRIMARY,
                    color=ft.Colors.WHITE,
                    on_click=lambda e: [self._cerrar_modal(modal), self._editar_cliente(cliente_actual)]
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(modal)
        modal.open = True
        self.page.update()

    def _crear_campo_detalle(self, label: str, valor: str, icono, color=None):
        """Helper para crear un campo de detalle"""
        return ft.Row([
            ft.Icon(icono, size=20, color=color or AppColors.PRIMARY),
            ft.Column([
                ft.Text(label, size=12, color=AppColors.PRIMARY, weight=ft.FontWeight.BOLD),
                ft.Text(valor, size=14, color=color or AppColors.PRIMARY),
            ], spacing=2),
        ], spacing=10)
    
    # ============================================
    # MODAL: EDITAR CLIENTE
    # ============================================
    def _editar_cliente(self, cliente: Cliente):
        """Abre el modal para editar un cliente"""
        
        # Campos del formulario pre-llenados
        nombre_field = ft.TextField(
            label="Nombre *",
            value=cliente.nombre,
            autofocus=True,
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )

        telefono_field = ft.TextField(
            label="Teléfono",
            value=cliente.telefono or "",
            prefix_icon=ft.Icons.PHONE,
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )

        direccion_field = ft.TextField(
            label="Dirección",
            value=cliente.direccion or "",
            prefix_icon=ft.Icons.LOCATION_ON,
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )

        email_field = ft.TextField(
            label="Email",
            value=cliente.email or "",
            prefix_icon=ft.Icons.EMAIL,
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )

        limite_field = ft.TextField(
            label="Límite de crédito",
            value=str(cliente.limite_credito),
            prefix_icon=ft.Icons.ATTACH_MONEY,
            keyboard_type=ft.KeyboardType.NUMBER,
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )

        notas_field = ft.TextField(
            label="Notas",
            value=cliente.notas or "",
            multiline=True,
            min_lines=2,
            max_lines=4,
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )
        
        def actualizar_cliente(e):
            if not nombre_field.value or nombre_field.value.strip() == "":
                self._mostrar_error("El nombre es obligatorio")
                return
            
            try:
                # Actualizar datos del cliente
                cliente.nombre = nombre_field.value.strip()
                cliente.telefono = telefono_field.value.strip() or None
                cliente.direccion = direccion_field.value.strip() or None
                cliente.email = email_field.value.strip() or None
                cliente.limite_credito = float(limite_field.value or 0)
                cliente.notas = notas_field.value.strip() or None
                cliente.fecha_actualizacion = datetime.now()
                
                # Guardar en BD
                session = get_session_context()
                ClienteRepository.actualizar(session, cliente)
                session.close()
                
                # Cerrar modal y recargar lista
                modal.open = False
                self.page.update()
                self._mostrar_exito(f"Cliente '{cliente.nombre}' actualizado exitosamente")
                self._cargar_clientes(None)
                
            except Exception as error:
                self._mostrar_error(f"Error al actualizar cliente: {error}")
        
        modal = ft.AlertDialog(
            modal=True,
            bgcolor=AppColors.MODAL_BG,
            title=ft.Text("Editar Cliente", size=20, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
            content=ft.Container(
                content=ft.Column([
                    nombre_field,
                    telefono_field,
                    direccion_field,
                    email_field,
                    limite_field,
                    notas_field,
                ], tight=True, spacing=15),
                width=500,
            ),
            actions=[
                ft.TextButton("Cancelar", style=ft.ButtonStyle(color=AppColors.PRIMARY), on_click=lambda e: self._cerrar_modal(modal)),
                ft.ElevatedButton("Actualizar", bgcolor=AppColors.PRIMARY, color=ft.Colors.WHITE, on_click=actualizar_cliente),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(modal)
        modal.open = True
        self.page.update()
    
    # ============================================
    # MODAL: CONFIRMAR ELIMINACIÓN
    # ============================================
    def _confirmar_eliminacion(self, cliente: Cliente):
        """Muestra un diálogo de confirmación antes de eliminar"""
        
        def eliminar(e):
            try:
                # Desactivar cliente (eliminación lógica)
                session = get_session_context()
                cliente.activo = False
                cliente.fecha_actualizacion = datetime.now()
                ClienteRepository.actualizar(session, cliente)
                session.close()
                
                # Cerrar modal y recargar lista
                modal.open = False
                self.page.update()
                self._mostrar_exito(f"Cliente '{cliente.nombre}' eliminado exitosamente")
                self._cargar_clientes(None)
                
            except Exception as error:
                self._mostrar_error(f"Error al eliminar cliente: {error}")
        
        # Advertencia si tiene deuda
        advertencia = None
        if cliente.tiene_deuda():
            advertencia = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.WARNING, color=ft.Colors.ORANGE_400),
                    ft.Text(
                        f"⚠️ Este cliente tiene una deuda de ${cliente.deuda_total:.2f}",
                        color=ft.Colors.ORANGE_700,
                        weight=ft.FontWeight.BOLD,
                    ),
                ]),
                bgcolor=ft.Colors.ORANGE_50,
                padding=10,
                border_radius=5,
            )
        
        modal = ft.AlertDialog(
            modal=True,
            bgcolor=AppColors.MODAL_BG,
            title=ft.Row([
                ft.Icon(ft.Icons.WARNING, color=AppColors.DANGER, size=30),
                ft.Text("Confirmar Eliminación", size=20, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
            ]),
            content=ft.Column([
                ft.Text(
                    f"¿Estás seguro de que deseas eliminar al cliente '{cliente.nombre}'?",
                    size=16,
                    color=AppColors.PRIMARY,
                ),
                ft.Text(
                    "Esta acción desactivará el cliente pero no eliminará su historial.",
                    size=12,
                    color=AppColors.PRIMARY,
                    italic=True,
                ),
                advertencia if advertencia else ft.Container(),
            ], tight=True, spacing=10),
            actions=[
                ft.TextButton("Cancelar", style=ft.ButtonStyle(color=AppColors.PRIMARY), on_click=lambda e: self._cerrar_modal(modal)),
                ft.ElevatedButton(
                    "Eliminar",
                    bgcolor=AppColors.DANGER,
                    color=ft.Colors.WHITE,
                    on_click=eliminar,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(modal)
        modal.open = True
        self.page.update()

    # ============================================
    # MODAL: VER HISTORIAL
    # ============================================
    def _ver_historial_cliente(self, cliente: Cliente):
        """Muestra el historial de compras y pagos del cliente"""

        # Cargar todas las ventas del cliente
        session = get_session_context()
        ventas = VentaRepository.listar_por_cliente(session, cliente.id)
        session.close()

        # Crear lista de ventas
        ventas_list = ft.Column(
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )

        if not ventas:
            ventas_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        "Este cliente no tiene ventas registradas",
                        size=14,
                        color=AppColors.PRIMARY,
                        italic=True,
                    ),
                    padding=20,
                    alignment=ft.alignment.center,
                )
            )
        else:
            for venta in ventas:
                ventas_list.controls.append(
                    self._crear_card_venta(venta, cliente)
                )

        modal = ft.AlertDialog(
            modal=True,
            bgcolor=AppColors.MODAL_BG,
            title=ft.Row([
                ft.Icon(ft.Icons.HISTORY, color=ft.Colors.PURPLE_400, size=30),
                ft.Text(f"Historial de {cliente.nombre}", size=20, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
            ]),
            content=ft.Container(
                content=ventas_list,
                width=700,
                height=500,
            ),
            actions=[
                ft.TextButton("Cerrar", style=ft.ButtonStyle(color=AppColors.PRIMARY), on_click=lambda e: self._cerrar_modal(modal)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(modal)
        modal.open = True
        self.page.update()

    def _crear_card_venta(self, venta, cliente: Cliente) -> ft.Card:
        """Crea una tarjeta para mostrar una venta en el historial"""

        # Determinar estado y color
        if venta.es_fiado:
            if venta.pagado_completamente:
                estado_texto = "PAGADO"
                estado_color = ft.Colors.GREEN_600
                estado_icon = ft.Icons.CHECK_CIRCLE
            else:
                estado_texto = f"DEBE ${venta.resto:.2f}"
                estado_color = ft.Colors.RED_600
                estado_icon = ft.Icons.PENDING
        else:
            estado_texto = "CONTADO"
            estado_color = ft.Colors.BLUE_600
            estado_icon = ft.Icons.PAYMENT

        # Lista de productos
        productos_texto = []
        for item in venta.productos:
            nombre = item.get("nombre", "Sin nombre")
            cantidad = item.get("cantidad", 0)
            precio = item.get("precio_unitario", 0)
            subtotal = item.get("subtotal", 0)
            productos_texto.append(
                f"  • {nombre} x{cantidad} @ ${precio:.2f} = ${subtotal:.2f}"
            )

        # Información de pagos (si es fiado)
        info_pagos = []
        if venta.es_fiado:
            # Obtener abonos
            session = get_session_context()
            abonos = AbonoRepository.listar_por_venta(session, venta.id)
            session.close()

            info_pagos.append(
                ft.Text(f"Total: ${venta.total:.2f}", size=12, color=AppColors.PRIMARY)
            )
            info_pagos.append(
                ft.Text(f"Abonado: ${venta.abonado:.2f}", size=12, color=ft.Colors.GREEN_600)
            )
            if not venta.pagado_completamente:
                info_pagos.append(
                    ft.Text(f"Resto: ${venta.resto:.2f}", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_600)
                )

            # Mostrar lista de abonos si existen
            if abonos:
                info_pagos.append(
                    ft.Text(f"Abonos ({len(abonos)}):", size=11, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY)
                )
                for abono in abonos:
                    usuario_abono = f" por {abono.usuario_nombre}" if abono.usuario_nombre else ""
                    info_pagos.append(
                        ft.Text(
                            f"  • ${abono.monto:.2f} - {abono.fecha.strftime('%d/%m/%y')}{usuario_abono}",
                            size=10,
                            color=AppColors.PRIMARY,
                        )
                    )

        # Botones de acción
        botones_accion = [
            ft.IconButton(
                icon=ft.Icons.EDIT,
                icon_color=ft.Colors.ORANGE_400,
                tooltip="Editar venta",
                on_click=lambda e, v=venta, c=cliente: self._editar_venta(v, c),
            ),
            ft.IconButton(
                icon=ft.Icons.DELETE,
                icon_color=AppColors.DANGER,
                tooltip="Eliminar venta",
                on_click=lambda e, v=venta, c=cliente: self._confirmar_eliminar_venta(v, c),
            ),
        ]

        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    # Header con fecha, usuario y estado
                    ft.Row([
                        ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.CALENDAR_TODAY, size=16, color=ft.Colors.WHITE70),
                                ft.Text(
                                    venta.fecha.strftime("%d/%m/%Y %H:%M"),
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                ),
                            ], spacing=5),
                            ft.Row([
                                ft.Icon(ft.Icons.PERSON, size=14, color=ft.Colors.WHITE54),
                                ft.Text(
                                    f"Vendedor: {venta.usuario_nombre or 'No registrado'}",
                                    size=11,
                                    color=ft.Colors.WHITE54,
                                ),
                            ], spacing=5),
                        ], spacing=2),
                        ft.Row([
                            ft.Icon(estado_icon, size=18, color=estado_color),
                            ft.Text(
                                estado_texto,
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=estado_color,
                            ),
                        ], spacing=5),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                    ft.Divider(height=1, color=ft.Colors.WHITE24),

                    # Productos
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Productos:", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE70),
                            ft.Text(
                                "\n".join(productos_texto),
                                size=11,
                                color=ft.Colors.WHITE70,
                            ),
                        ], spacing=5),
                        padding=ft.padding.only(left=10, top=5, bottom=5),
                    ),

                    # Información de pagos (si es fiado)
                    ft.Container(
                        content=ft.Column(info_pagos, spacing=3),
                        padding=ft.padding.only(left=10, bottom=5),
                    ) if info_pagos else ft.Container(),

                    # Total y botones
                    ft.Row([
                        ft.Text(
                            f"Total: ${venta.total:.2f}",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                        ),
                        ft.Row(botones_accion, spacing=0),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                ], spacing=8),
                padding=15,
                bgcolor=AppColors.CARD_DARK,
                border_radius=10,
            ),
        )

    # ============================================
    # MODAL: GESTIONAR ABONOS DE UNA VENTA
    # ============================================
    def _editar_venta(self, venta, cliente: Cliente):
        """Muestra los abonos de una venta y permite agregar o eliminar abonos"""

        if not venta.es_fiado:
            self._mostrar_info("Solo las ventas fiadas tienen abonos")
            return

        # Cargar abonos de la venta
        session = get_session_context()
        abonos = AbonoRepository.listar_por_venta(session, venta.id)
        session.close()

        # Lista de abonos
        abonos_list = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO)

        def actualizar_lista_abonos():
            """Recarga la lista de abonos"""
            session = get_session_context()
            abonos_actuales = AbonoRepository.listar_por_venta(session, venta.id)
            venta_actualizada = VentaRepository.obtener_por_id(session, venta.id)
            session.close()

            abonos_list.controls.clear()

            if not abonos_actuales:
                abonos_list.controls.append(
                    ft.Text("No hay abonos registrados", size=12, color=AppColors.PRIMARY, italic=True)
                )
            else:
                for abono in abonos_actuales:
                    abonos_list.controls.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.Row([
                                    ft.Column([
                                        ft.Text(
                                            f"${abono.monto:.2f}",
                                            size=14,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.GREEN_600,
                                        ),
                                        ft.Text(
                                            abono.fecha.strftime("%d/%m/%Y %H:%M"),
                                            size=11,
                                            color=AppColors.PRIMARY,
                                        ),
                                    ], spacing=2),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE,
                                        icon_color=AppColors.DANGER,
                                        icon_size=18,
                                        tooltip="Eliminar abono",
                                        on_click=lambda e, a=abono: eliminar_abono(a),
                                    ),
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                padding=10,
                            ),
                        )
                    )

            # Actualizar información de la venta
            info_total.value = f"Total: ${venta_actualizada.total:.2f}"
            info_abonado.value = f"Abonado: ${venta_actualizada.abonado:.2f}"
            info_resto.value = f"Resto: ${venta_actualizada.resto:.2f}"
            info_resto.color = ft.Colors.GREEN_600 if venta_actualizada.resto == 0 else ft.Colors.RED_600

            self.page.update()

        def eliminar_abono(abono):
            """Elimina un abono"""
            def confirmar_eliminar(e):
                try:
                    session = get_session_context()
                    AbonoRepository.eliminar(session, abono.id)
                    session.close()

                    confirm_modal.open = False
                    self.page.update()

                    actualizar_lista_abonos()
                    self._mostrar_exito("Abono eliminado exitosamente")

                except Exception as error:
                    self._mostrar_error(f"Error al eliminar abono: {error}")

            confirm_modal = ft.AlertDialog(
                modal=True,
                bgcolor=AppColors.MODAL_BG,
                title=ft.Text("Confirmar eliminación", color=AppColors.PRIMARY),
                content=ft.Text(f"¿Eliminar abono de ${abono.monto:.2f}?"),
                actions=[
                    ft.TextButton("Cancelar", style=ft.ButtonStyle(color=AppColors.PRIMARY), on_click=lambda e: self._cerrar_modal(confirm_modal)),
                    ft.ElevatedButton(
                        "Eliminar",
                        bgcolor=AppColors.DANGER,
                        color=ft.Colors.WHITE,
                        on_click=confirmar_eliminar,
                    ),
                ],
            )
            self.page.overlay.append(confirm_modal)
            confirm_modal.open = True
            self.page.update()

        def agregar_abono(e):
            """Muestra el diálogo para agregar un nuevo abono"""
            monto_field = ft.TextField(
                label="Monto del abono",
                prefix_text="$",
                keyboard_type=ft.KeyboardType.NUMBER,
                autofocus=True,
                color=AppColors.PRIMARY,
                border_color=AppColors.INPUT_BORDER,
                focused_border_color=AppColors.INPUT_FOCUS,
            )
            notas_field = ft.TextField(
                label="Notas (opcional)",
                multiline=True,
                max_lines=2,
                color=AppColors.PRIMARY,
                border_color=AppColors.INPUT_BORDER,
                focused_border_color=AppColors.INPUT_FOCUS,
            )
            error_msg = ft.Text("", color=AppColors.DANGER, size=12, visible=False)

            def guardar_abono(e):
                try:
                    monto = float(monto_field.value or 0)
                    notas = notas_field.value.strip() or None

                    # Obtener usuario actual del estado
                    usuario_actual = self.state.get("usuario_actual")

                    session = get_session_context()
                    AbonoRepository.crear(
                        session,
                        venta.id,
                        monto,
                        notas,
                        usuario_id=usuario_actual.id if usuario_actual else None,
                        usuario_nombre=usuario_actual.nombre if usuario_actual else None
                    )
                    session.close()

                    abono_modal.open = False
                    self.page.update()

                    actualizar_lista_abonos()
                    self._mostrar_exito("Abono registrado exitosamente")

                except ValueError as ve:
                    error_msg.value = str(ve)
                    error_msg.visible = True
                    self.page.update()
                except Exception as error:
                    self._mostrar_error(f"Error al registrar abono: {error}")

            abono_modal = ft.AlertDialog(
                modal=True,
                bgcolor=AppColors.MODAL_BG,
                title=ft.Text("Agregar Abono", color=AppColors.PRIMARY),
                content=ft.Column([
                    monto_field,
                    notas_field,
                    error_msg,
                ], tight=True, spacing=10),
                actions=[
                    ft.TextButton("Cancelar", style=ft.ButtonStyle(color=AppColors.PRIMARY), on_click=lambda e: self._cerrar_modal(abono_modal)),
                    ft.ElevatedButton(
                        "Guardar",
                        bgcolor=ft.Colors.GREEN_600,
                        color=ft.Colors.WHITE,
                        on_click=guardar_abono,
                    ),
                ],
            )
            self.page.overlay.append(abono_modal)
            abono_modal.open = True
            self.page.update()

        # Información de la venta
        info_total = ft.Text(f"Total: ${venta.total:.2f}", size=14, color=AppColors.PRIMARY)
        info_abonado = ft.Text(f"Abonado: ${venta.abonado:.2f}", size=14, color=ft.Colors.GREEN_700)
        info_resto = ft.Text(
            f"Resto: ${venta.resto:.2f}",
            size=14,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.GREEN_600 if venta.resto == 0 else ft.Colors.RED_600,
        )

        # Inicializar lista de abonos
        actualizar_lista_abonos()

        modal = ft.AlertDialog(
            modal=True,
            bgcolor=AppColors.MODAL_BG,
            title=ft.Row([
                ft.Icon(ft.Icons.PAYMENTS, color=ft.Colors.ORANGE_400, size=30),
                ft.Text("Gestionar Abonos", size=20, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
            ]),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        f"Venta del {venta.fecha.strftime('%d/%m/%Y %H:%M')}",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.PRIMARY,
                    ),
                    ft.Container(
                        content=ft.Column([info_total, info_abonado, info_resto], spacing=3),
                        bgcolor=ft.Colors.GREY_100,
                        padding=10,
                        border_radius=8,
                        margin=ft.margin.only(top=10, bottom=10),
                    ),
                    ft.Row([
                        ft.Text("Abonos registrados:", size=14, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
                        ft.IconButton(
                            icon=ft.Icons.ADD_CIRCLE,
                            icon_color=ft.Colors.GREEN_600,
                            tooltip="Agregar abono",
                            on_click=agregar_abono,
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(
                        content=abonos_list,
                        height=200,
                    ),
                ], tight=True, spacing=10),
                width=500,
            ),
            actions=[
                ft.TextButton("Cerrar", style=ft.ButtonStyle(color=AppColors.PRIMARY), on_click=lambda e: [self._cerrar_modal(modal), self._cargar_clientes(None)]),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(modal)
        modal.open = True
        self.page.update()

    # ============================================
    # MODAL: CONFIRMAR ELIMINAR VENTA
    # ============================================
    def _confirmar_eliminar_venta(self, venta, cliente: Cliente):
        """Confirma la eliminación de una venta"""

        def eliminar(e):
            try:
                session = get_session_context()

                # Eliminar venta (esto ya revierte stock y deuda automáticamente)
                exito = VentaRepository.eliminar(session, venta.id)

                session.close()

                if exito:
                    modal.open = False
                    self.page.update()

                    self._mostrar_exito("Venta eliminada exitosamente")

                    # Recargar la lista de clientes
                    self._cargar_clientes(None)
                else:
                    self._mostrar_error("No se pudo eliminar la venta")

            except Exception as error:
                self._mostrar_error(f"Error al eliminar venta: {error}")

        # Advertencia
        advertencia_texto = "Esta acción eliminará la venta y revertirá los cambios de stock"
        if venta.es_fiado and venta.abonado > 0:
            advertencia_texto += f" y la deuda del cliente (se restarán ${venta.resto:.2f} de la deuda)."
        else:
            advertencia_texto += "."

        modal = ft.AlertDialog(
            modal=True,
            bgcolor=AppColors.MODAL_BG,
            title=ft.Row([
                ft.Icon(ft.Icons.WARNING, color=AppColors.DANGER, size=30),
                ft.Text("Confirmar Eliminación", size=20, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
            ]),
            content=ft.Column([
                ft.Text(
                    f"¿Estás seguro de que deseas eliminar esta venta?",
                    size=16,
                    color=AppColors.PRIMARY,
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            f"Fecha: {venta.fecha.strftime('%d/%m/%Y %H:%M')}",
                            size=14,
                            color=AppColors.PRIMARY,
                        ),
                        ft.Text(
                            f"Total: ${venta.total:.2f}",
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=AppColors.PRIMARY,
                        ),
                        ft.Text(
                            advertencia_texto,
                            size=12,
                            color=ft.Colors.ORANGE_700,
                            italic=True,
                        ),
                    ], spacing=5),
                    bgcolor=ft.Colors.ORANGE_50,
                    padding=15,
                    border_radius=8,
                    margin=ft.margin.only(top=10, bottom=10),
                ),
            ], tight=True, spacing=10),
            actions=[
                ft.TextButton("Cancelar", style=ft.ButtonStyle(color=AppColors.PRIMARY), on_click=lambda e: self._cerrar_modal(modal)),
                ft.ElevatedButton(
                    "Eliminar",
                    bgcolor=AppColors.DANGER,
                    color=ft.Colors.WHITE,
                    icon=ft.Icons.DELETE,
                    on_click=eliminar,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(modal)
        modal.open = True
        self.page.update()

    # ============================================
    # SINCRONIZACIÓN DE DEUDAS
    # ============================================
    def _sincronizar_todas_deudas(self, e):
        """Sincroniza las deudas de todos los clientes con la realidad desde las ventas"""

        def confirmar_sincronizacion(e):
            try:
                confirm_modal.open = False
                self.loading.visible = True
                self.page.update()

                session = get_session_context()
                stats = ClienteRepository.sincronizar_todas_las_deudas(session)
                session.close()

                # Mostrar resultados
                self._mostrar_resultados_sincronizacion(stats)

                # Recargar lista
                self._cargar_clientes(None)

            except Exception as error:
                self._mostrar_error(f"Error al sincronizar deudas: {error}")
            finally:
                self.loading.visible = False
                self.page.update()

        confirm_modal = ft.AlertDialog(
            modal=True,
            bgcolor=AppColors.MODAL_BG,
            title=ft.Row([
                ft.Icon(ft.Icons.SYNC, color=ft.Colors.ORANGE_600, size=30),
                ft.Text("Sincronizar Deudas", size=20, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
            ]),
            content=ft.Column([
                ft.Text(
                    "Esta operación sincronizará las deudas de todos los clientes",
                    size=16,
                    color=AppColors.PRIMARY,
                ),
                ft.Text(
                    "con el valor real calculado desde las ventas pendientes.",
                    size=16,
                    color=AppColors.PRIMARY,
                ),
                ft.Container(
                    content=ft.Text(
                        "Esto corregirá cualquier inconsistencia en los datos.",
                        size=14,
                        color=AppColors.PRIMARY,
                        italic=True,
                    ),
                    bgcolor=ft.Colors.ORANGE_50,
                    padding=10,
                    border_radius=8,
                    margin=ft.margin.only(top=10, bottom=10),
                ),
            ], tight=True, spacing=10),
            actions=[
                ft.TextButton("Cancelar", style=ft.ButtonStyle(color=AppColors.PRIMARY), on_click=lambda e: self._cerrar_modal(confirm_modal)),
                ft.ElevatedButton(
                    "Sincronizar",
                    bgcolor=ft.Colors.ORANGE_600,
                    color=ft.Colors.WHITE,
                    icon=ft.Icons.SYNC,
                    on_click=confirmar_sincronizacion,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(confirm_modal)
        confirm_modal.open = True
        self.page.update()

    def _mostrar_resultados_sincronizacion(self, stats: dict):
        """Muestra los resultados de la sincronización"""

        contenido = []

        contenido.append(ft.Text(
            f"Total de clientes: {stats['total_clientes']}",
            size=16,
            color=AppColors.PRIMARY,
        ))

        contenido.append(ft.Text(
            f"Clientes corregidos: {stats['clientes_corregidos']}",
            size=16,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.ORANGE_600 if stats['clientes_corregidos'] > 0 else ft.Colors.GREEN_600,
        ))

        if stats['diferencias']:
            contenido.append(ft.Divider())
            contenido.append(ft.Text("Detalles de las correcciones:", size=14, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY))

            for diff in stats['diferencias']:
                diferencia_texto = f"+${abs(diff['diferencia']):.2f}" if diff['diferencia'] > 0 else f"-${abs(diff['diferencia']):.2f}"
                color_diferencia = ft.Colors.RED_600 if diff['diferencia'] > 0 else ft.Colors.GREEN_600

                contenido.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(f"{diff['nombre']}", size=13, weight=ft.FontWeight.BOLD),
                            ft.Text(f"BD: ${diff['deuda_bd']:.2f} → Real: ${diff['deuda_real']:.2f}", size=12),
                            ft.Text(f"Diferencia: {diferencia_texto}", size=12, color=color_diferencia),
                        ], spacing=3),
                        bgcolor=ft.Colors.GREY_100,
                        padding=10,
                        border_radius=5,
                        margin=ft.margin.only(bottom=5),
                    )
                )

        modal = ft.AlertDialog(
            modal=True,
            bgcolor=AppColors.MODAL_BG,
            title=ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_600, size=30),
                ft.Text("Sincronización Completada", size=20, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
            ]),
            content=ft.Container(
                content=ft.Column(contenido, spacing=10, scroll=ft.ScrollMode.AUTO),
                width=500,
                height=400 if stats['diferencias'] else 150,
            ),
            actions=[
                ft.TextButton("Cerrar", style=ft.ButtonStyle(color=AppColors.PRIMARY), on_click=lambda e: self._cerrar_modal(modal)),
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
    
    def _mostrar_info(self, mensaje: str):
        """Muestra un mensaje informativo"""
        snack = ft.SnackBar(
            content=ft.Text(mensaje),
            bgcolor=ft.Colors.BLUE_400,
        )
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()