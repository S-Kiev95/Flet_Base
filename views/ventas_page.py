"""Vista de gestión de ventas"""

import flet as ft
from typing import List
from datetime import datetime
from models.venta import Venta
from database.connection import get_session_context
from database.db_service import VentaRepository
from config.settings import AppColors
from utils.pdf_generator import PDFGenerator


class VentasPage:
    """Página de gestión de ventas"""
    
    def __init__(self, state, api, page, router):
        self.state = state
        self.api = api
        self.page = page
        self.router = router
        self.container = None
        
        # Componentes
        self.search_field = ft.TextField(
            label="Buscar venta",
            prefix_icon=ft.Icons.SEARCH,
            color=AppColors.PRIMARY,
            bgcolor=AppColors.INPUT_BG,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
            on_change=self._on_search_change,
            expand=True,
        )
        
        self.ventas_list = ft.Column(
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )
        
        self.loading = ft.ProgressRing(visible=False)
        
        # Lista completa de ventas (para filtrar)
        self.todas_ventas: List[Venta] = []
    
    def build(self):
        """Construye la interfaz de la página"""
        
        self.container = ft.Container(
            content=ft.Column([
                # Header
                ft.Row([
                    ft.Text(
                        "Gestión de Ventas",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.PRIMARY
                    ),
                    ft.Row([
                        ft.ElevatedButton(
                            "Ver Fiados",
                            icon=ft.Icons.ATTACH_MONEY,
                            bgcolor=AppColors.WARNING,
                            color=ft.Colors.WHITE,
                            on_click=self._ver_fiados,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.REFRESH,
                            tooltip="Recargar lista",
                            on_click=self._cargar_ventas,
                        ),
                    ]),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                ft.Divider(),

                # Barra de búsqueda
                ft.Row([
                    self.search_field,
                    ft.ElevatedButton(
                        "Nueva Venta",
                        icon=ft.Icons.ADD_SHOPPING_CART,
                        bgcolor=AppColors.PRIMARY,
                        color=ft.Colors.WHITE,
                        on_click=self._nueva_venta,
                    ),
                ]),
                
                # Indicador de carga
                self.loading,
                
                # Lista de ventas
                ft.Container(
                    content=self.ventas_list,
                    expand=True,
                ),
                
            ]),
            padding=20,
            expand=True,
        )
        
        # Cargar ventas al iniciar
        self._cargar_ventas(None)
        
        return self.container
    
    def _cargar_ventas(self, e):
        """Carga la lista de ventas desde la base de datos"""
        self.loading.visible = True
        self.page.update()
        
        try:
            session = get_session_context()
            self.todas_ventas = VentaRepository.listar_todas(session, limit=50)
            session.close()
            
            self._actualizar_lista(self.todas_ventas)
            
        except Exception as error:
            self._mostrar_error(f"Error al cargar ventas: {error}")
        finally:
            self.loading.visible = False
            self.page.update()
    
    def _on_search_change(self, e):
        """Filtra la lista cuando cambia el texto de búsqueda"""
        texto_busqueda = self.search_field.value.lower().strip()
        
        if not texto_busqueda:
            self._actualizar_lista(self.todas_ventas)
        else:
            ventas_filtradas = [
                v for v in self.todas_ventas
                if (v.cliente_nombre and texto_busqueda in v.cliente_nombre.lower()) or
                   str(v.id) == texto_busqueda
            ]
            self._actualizar_lista(ventas_filtradas)
    
    def _actualizar_lista(self, ventas: List[Venta]):
        """Actualiza la lista visual de ventas"""
        self.ventas_list.controls.clear()
        
        if not ventas:
            self.ventas_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No se encontraron ventas",
                        size=16,
                        color=AppColors.PRIMARY,
                        italic=True,
                    ),
                    padding=20,
                    alignment=ft.alignment.center,
                )
            )
        else:
            for venta in ventas:
                self.ventas_list.controls.append(
                    self._crear_card_venta(venta)
                )
        
        self.page.update()
    
    def _crear_card_venta(self, venta: Venta) -> ft.Card:
        """Crea una tarjeta para mostrar una venta"""
        
        # Estado de la venta
        if venta.pagado_completamente:
            estado_texto = "PAGADO"
            estado_color = AppColors.SUCCESS
            estado_icono = ft.Icons.CHECK_CIRCLE
        elif venta.es_fiado:
            estado_texto = f"DEBE ${venta.resto:.2f}"
            estado_color = AppColors.DANGER
            estado_icono = ft.Icons.PENDING
        else:
            estado_texto = "CONTADO"
            estado_color = AppColors.PRIMARY
            estado_icono = ft.Icons.PAYMENT
        
        return ft.Card(
            content=ft.Container(
                content=ft.Row([
                    # Información principal
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.RECEIPT, size=20, color=ft.Colors.WHITE),
                                ft.Text(
                                    f"Venta #{venta.id}",
                                    size=18,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                ),
                            ]),

                            ft.Row([
                                ft.Icon(ft.Icons.CALENDAR_TODAY, size=16, color=ft.Colors.WHITE70),
                                ft.Text(
                                    venta.fecha.strftime("%d/%m/%Y %H:%M"),
                                    size=14,
                                    color=ft.Colors.WHITE70,
                                ),
                            ], spacing=5),

                            ft.Row([
                                ft.Icon(ft.Icons.PERSON, size=16, color=ft.Colors.WHITE70),
                                ft.Text(
                                    venta.cliente_nombre or "Cliente anónimo",
                                    size=14,
                                    color=ft.Colors.WHITE70,
                                ),
                            ], spacing=5),

                        ], spacing=5),
                        expand=True,
                    ),

                    # Totales
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Total", size=12, color=ft.Colors.WHITE70, weight=ft.FontWeight.BOLD),
                            ft.Text(f"${venta.total:.2f}", size=18, weight=ft.FontWeight.BOLD, color=AppColors.SUCCESS),
                            ft.Row([
                                ft.Icon(estado_icono, size=16, color=estado_color),
                                ft.Text(estado_texto, size=12, color=estado_color, weight=ft.FontWeight.BOLD),
                            ]),
                        ], spacing=3),
                        width=130,
                    ),

                    # Botones de acción
                    ft.Container(
                        content=ft.Row([
                            ft.IconButton(
                                icon=ft.Icons.VISIBILITY,
                                icon_color=ft.Colors.BLUE_200,
                                tooltip="Ver detalles",
                                on_click=lambda e, v=venta: self._ver_venta(v),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.PAYMENT,
                                icon_color=AppColors.SUCCESS,
                                tooltip="Registrar abono",
                                on_click=lambda e, v=venta: self._registrar_abono(v),
                                disabled=venta.pagado_completamente,
                            ) if venta.es_fiado else ft.Container(width=48),
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                icon_color=AppColors.DANGER,
                                tooltip="Eliminar",
                                on_click=lambda e, v=venta: self._confirmar_eliminacion(v),
                            ),
                        ], spacing=0),
                        width=140,
                    ),

                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=15,
                bgcolor=AppColors.CARD_DARK,
                border_radius=10,
            ),
        )

    # ============================================
    # NAVEGACIÓN
    # ============================================
    def _nueva_venta(self, e):
        """Navega a la página de nueva venta"""
        self.router.navigate("nueva_venta")
    
    # ============================================
    # MODAL: VER DETALLES
    # ============================================
    def _ver_venta(self, venta: Venta):
        """Muestra los detalles completos de una venta"""
        
        session = get_session_context()
        venta_actual = VentaRepository.obtener_por_id(session, venta.id)
        session.close()
        
        if not venta_actual:
            self._mostrar_error("Venta no encontrada")
            return
        
        # Lista de productos
        productos_detalle = ft.Column(spacing=5)
        for item in venta_actual.productos:
            tipo = "🏪 BD" if item.get("producto_id") else "✏️ Manual"
            productos_detalle.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(f"{tipo} {item['nombre']}", weight=ft.FontWeight.BOLD, size=14),
                        ]),
                        ft.Text(
                            f"${item['precio_unitario']:.2f} x {item['cantidad']} = ${item['subtotal']:.2f}",
                            size=12,
                            color=AppColors.PRIMARY
                        ),
                    ], spacing=2),
                    bgcolor=ft.Colors.GREY_100,
                    padding=10,
                    border_radius=5,
                )
            )
        
        contenido = ft.Column([
            self._crear_campo_detalle("Venta", f"#{venta_actual.id}", ft.Icons.RECEIPT),
            self._crear_campo_detalle("Fecha", venta_actual.fecha.strftime("%d/%m/%Y %H:%M"), ft.Icons.CALENDAR_TODAY),
            self._crear_campo_detalle("Cliente", venta_actual.cliente_nombre or "Anónimo", ft.Icons.PERSON),
            self._crear_campo_detalle("Vendedor", venta_actual.usuario_nombre or "No registrado", ft.Icons.BADGE),

            ft.Divider(),
            
            ft.Text("Productos", weight=ft.FontWeight.BOLD, size=16),
            productos_detalle,
            
            ft.Divider(),
            
            ft.Text("Totales", weight=ft.FontWeight.BOLD, size=16),
            self._crear_campo_detalle("Total", f"${venta_actual.total:.2f}", ft.Icons.ATTACH_MONEY, color=ft.Colors.GREEN_600),
            
            self._crear_campo_detalle("Abonado", f"${venta_actual.abonado:.2f}", ft.Icons.PAYMENT, color=ft.Colors.BLUE_600) if venta_actual.es_fiado else ft.Container(),
            self._crear_campo_detalle("Resto", f"${venta_actual.resto:.2f}", ft.Icons.PENDING, color=ft.Colors.ORANGE_600) if venta_actual.es_fiado else ft.Container(),
            
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=AppColors.SUCCESS),
                    ft.Text("PAGADO COMPLETAMENTE", color=ft.Colors.GREEN_700, weight=ft.FontWeight.BOLD),
                ]),
                bgcolor=ft.Colors.GREEN_50,
                padding=10,
                border_radius=5,
            ) if venta_actual.pagado_completamente else ft.Container(),
            
        ], spacing=10, scroll=ft.ScrollMode.AUTO)

        # Crear el botón de imprimir antes para poder referenciarlo
        btn_imprimir = ft.ElevatedButton(
            "Imprimir Comprobante",
            icon=ft.Icons.PRINT,
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.GREEN_600,
        )

        # Variable para guardar referencia al modal
        modal_ref = [None]

        def imprimir_comprobante(e):
            es_web = getattr(self.page, 'web', False)

            # Cerrar el modal de detalles primero
            if modal_ref[0]:
                modal_ref[0].open = False
                self.page.update()

            try:
                # Usar método unificado (detecta web/desktop automáticamente)
                PDFGenerator.imprimir_o_mostrar(self.page, venta=venta_actual, tipo='venta')

                # Solo mostrar snackbar en desktop (en web el modal del PDF ya informa)
                if not es_web:
                    self._mostrar_exito("Comprobante enviado a impresora")

            except Exception as error:
                self._mostrar_error(f"Error al generar comprobante: {error}")

        # Asignar el evento después de crear la función
        btn_imprimir.on_click = imprimir_comprobante

        modal = ft.AlertDialog(
            modal=True,
            bgcolor=AppColors.MODAL_BG,
            title=ft.Row([
                ft.Icon(ft.Icons.INFO, color=ft.Colors.BLUE_400),
                ft.Text("Detalles de la Venta", size=20, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
            ]),
            content=ft.Container(content=contenido, width=500, height=500),
            actions=[
                ft.TextButton("Cerrar", style=ft.ButtonStyle(color=AppColors.PRIMARY), on_click=lambda e: self._cerrar_modal(modal)),
                btn_imprimir,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        # Guardar referencia para poder cerrar desde imprimir_comprobante
        modal_ref[0] = modal

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
    # MODAL: REGISTRAR ABONO
    # ============================================
    def _registrar_abono(self, venta: Venta):
        """Registra un abono a una venta fiada"""
        
        session = get_session_context()
        venta_actual = VentaRepository.obtener_por_id(session, venta.id)
        session.close()
        
        if not venta_actual or not venta_actual.es_fiado:
            self._mostrar_error("Esta venta no es fiada")
            return
        
        if venta_actual.pagado_completamente:
            self._mostrar_error("Esta venta ya está pagada completamente")
            return
        
        monto_field = ft.TextField(
            label=f"Monto a abonar (Resto: ${venta_actual.resto:.2f})",
            hint_text="0.00",
            value=str(venta_actual.resto),
            prefix_icon=ft.Icons.ATTACH_MONEY,
            keyboard_type=ft.KeyboardType.NUMBER,
            autofocus=True,
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )

        # Crear el botón antes para poder referenciarlo
        btn_registrar = ft.ElevatedButton(
            "Registrar Abono",
            icon=ft.Icons.SAVE,
            bgcolor=AppColors.PRIMARY,
            color=ft.Colors.WHITE,
        )
        
        def guardar_abono(e):
            # Deshabilitar el botón inmediatamente
            btn_registrar.disabled = True
            btn_registrar.text = "Registrando..."
            self.page.update()
            
            try:
                monto = float(monto_field.value or 0)
                
                if monto <= 0:
                    self._mostrar_error("El monto debe ser mayor a 0")
                    btn_registrar.disabled = False
                    btn_registrar.text = "Registrar Abono"
                    self.page.update()
                    return
                
                if monto > venta_actual.resto:
                    self._mostrar_error(f"El monto no puede ser mayor al resto (${venta_actual.resto:.2f})")
                    btn_registrar.disabled = False
                    btn_registrar.text = "Registrar Abono"
                    self.page.update()
                    return
                
                session = get_session_context()
                VentaRepository.registrar_abono(session, venta_actual.id, monto)
                session.close()
                
                modal.open = False
                self.page.update()
                
                self._mostrar_exito(f"Abono de ${monto:.2f} registrado exitosamente")
                self._cargar_ventas(None)
                
            except ValueError:
                self._mostrar_error("Monto inválido")
                btn_registrar.disabled = False
                btn_registrar.text = "Registrar Abono"
                self.page.update()
            except Exception as error:
                self._mostrar_error(f"Error al registrar abono: {error}")
                btn_registrar.disabled = False
                btn_registrar.text = "Registrar Abono"
                self.page.update()
        
        # Asignar el evento después de crear la función
        btn_registrar.on_click = guardar_abono
        
        modal = ft.AlertDialog(
            modal=True,
            bgcolor=AppColors.MODAL_BG,
            title=ft.Row([
                ft.Icon(ft.Icons.PAYMENT, color=AppColors.SUCCESS),
                ft.Text("Registrar Abono", size=20, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
            ]),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(f"Venta #{venta_actual.id}", size=16, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
                    ft.Text(f"Cliente: {venta_actual.cliente_nombre}", size=14, color=AppColors.PRIMARY),
                    ft.Divider(),
                    ft.Text(f"Total: ${venta_actual.total:.2f}", size=14, color=AppColors.PRIMARY),
                    ft.Text(f"Abonado: ${venta_actual.abonado:.2f}", size=14, color=AppColors.SUCCESS),
                    ft.Text(f"Resto: ${venta_actual.resto:.2f}", size=14, color=AppColors.DANGER, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    monto_field,
                ], tight=True, spacing=10),
                width=400,
            ),
            actions=[
                ft.TextButton("Cancelar", style=ft.ButtonStyle(color=AppColors.PRIMARY), on_click=lambda e: self._cerrar_modal(modal)),
                btn_registrar,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(modal)
        modal.open = True
        self.page.update()
    
    # ============================================
    # MODAL: VER FIADOS
    # ============================================
    def _ver_fiados(self, e):
        """Muestra solo las ventas fiadas pendientes"""
        
        session = get_session_context()
        ventas_fiadas = VentaRepository.listar_pendientes(session)
        session.close()
        
        fiados_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        
        if not ventas_fiadas:
            fiados_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        "¡No hay ventas fiadas pendientes! 🎉",
                        size=16,
                        color=ft.Colors.GREEN_500,
                        weight=ft.FontWeight.BOLD,
                    ),
                    padding=20,
                    alignment=ft.alignment.center,
                )
            )
        else:
            total_deuda = sum(v.resto for v in ventas_fiadas)
            
            fiados_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text("Resumen de Fiados", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Total de ventas fiadas: {len(ventas_fiadas)}", size=14),
                        ft.Text(f"Deuda total: ${total_deuda:.2f}", size=16, color=ft.Colors.ORANGE_600, weight=ft.FontWeight.BOLD),
                    ], spacing=5),
                    bgcolor=ft.Colors.ORANGE_50,
                    padding=15,
                    border_radius=5,
                )
            )
            
            fiados_list.controls.append(ft.Divider())
            
            # Agrupar por cliente
            ventas_por_cliente = {}
            for venta in ventas_fiadas:
                cliente = venta.cliente_nombre or "Sin cliente"
                if cliente not in ventas_por_cliente:
                    ventas_por_cliente[cliente] = []
                ventas_por_cliente[cliente].append(venta)
            
            for cliente, ventas in ventas_por_cliente.items():
                deuda_cliente = sum(v.resto for v in ventas)
                
                fiados_list.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.PERSON, size=20, color=ft.Colors.BLUE_400),
                                ft.Text(cliente, size=16, weight=ft.FontWeight.BOLD, expand=True),
                                ft.Text(f"Debe: ${deuda_cliente:.2f}", size=14, color=AppColors.DANGER, weight=ft.FontWeight.BOLD),
                            ]),
                            ft.Divider(height=5),
                            *[
                                ft.Container(
                                    content=ft.Row([
                                        ft.Column([
                                            ft.Text(f"Venta #{v.id} - {v.fecha.strftime('%d/%m/%Y')}", size=13),
                                            ft.Text(f"Total: ${v.total:.2f} | Abonado: ${v.abonado:.2f}", size=11, color=AppColors.PRIMARY),
                                        ], expand=True),
                                        ft.Row([
                                            ft.Text(f"${v.resto:.2f}", size=14, color=ft.Colors.ORANGE_600, weight=ft.FontWeight.BOLD),
                                            ft.IconButton(
                                                icon=ft.Icons.PAYMENT,
                                                icon_size=18,
                                                icon_color=AppColors.SUCCESS,
                                                on_click=lambda e, venta=v: [self._cerrar_modal(modal), self._registrar_abono(venta)],
                                            ),
                                        ]),
                                    ]),
                                    bgcolor=ft.Colors.GREY_50,
                                    padding=8,
                                    border_radius=5,
                                )
                                for v in ventas
                            ],
                        ], spacing=5),
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        border_radius=5,
                        padding=10,
                    )
                )
        
        modal = ft.AlertDialog(
            modal=True,
            bgcolor=AppColors.MODAL_BG,
            title=ft.Row([
                ft.Icon(ft.Icons.ATTACH_MONEY, color=ft.Colors.ORANGE_400),
                ft.Text("Ventas Fiadas Pendientes", size=20, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
            ]),
            content=ft.Container(
                content=fiados_list,
                width=600,
                height=500,
            ),
            actions=[
                ft.TextButton("Cerrar", style=ft.ButtonStyle(color=AppColors.PRIMARY), on_click=lambda e: self._cerrar_modal(modal)),
            ],
        )
        
        self.page.overlay.append(modal)
        modal.open = True
        self.page.update()
    
    # ============================================
    # MODAL: CONFIRMAR ELIMINACIÓN
    # ============================================
    def _confirmar_eliminacion(self, venta: Venta):
        """Muestra un diálogo de confirmación antes de eliminar"""
        
        def eliminar(e):
            try:
                self._mostrar_info("Función de eliminación de ventas por implementar")
                modal.open = False
                self.page.update()
                
            except Exception as error:
                self._mostrar_error(f"Error al eliminar venta: {error}")
        
        advertencia = None
        if venta.es_fiado and not venta.pagado_completamente:
            advertencia = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.WARNING, color=ft.Colors.ORANGE_400),
                    ft.Text(
                        f"⚠️ Esta venta tiene un saldo pendiente de ${venta.resto:.2f}",
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
                    f"¿Estás seguro de que deseas eliminar la venta #{venta.id}?",
                    size=16,
                    color=AppColors.PRIMARY,
                ),
                ft.Text(
                    "Esta acción no se puede deshacer.",
                    size=12,
                    color=AppColors.DANGER,
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
    # HELPERS
    # ============================================
    def _cerrar_modal(self, modal):
        """Cierra un modal"""
        modal.open = False
        self.page.update()
    
    def _mostrar_error(self, mensaje: str):
        """Muestra un mensaje de error"""
        snack = ft.SnackBar(content=ft.Text(mensaje), bgcolor=AppColors.DANGER)
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()
    
    def _mostrar_exito(self, mensaje: str):
        """Muestra un mensaje de éxito"""
        snack = ft.SnackBar(content=ft.Text(mensaje), bgcolor=AppColors.SUCCESS)
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()
    
    def _mostrar_info(self, mensaje: str):
        """Muestra un mensaje informativo"""
        snack = ft.SnackBar(content=ft.Text(mensaje), bgcolor=ft.Colors.BLUE_400)
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()