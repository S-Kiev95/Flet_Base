"""Página para crear una nueva venta"""

import flet as ft
from typing import List, Dict, Any
from models.venta import Venta
from models.cliente import Cliente
from models.producto import Producto
from database.connection import get_session_context
from database.db_service import VentaRepository, ClienteRepository, ProductoRepository, AbonoRepository
from config.settings import AppColors

from utils.pdf_generator import PDFGenerator

class NuevaVentaPage:
    """Página dedicada para crear una nueva venta"""
    
    def __init__(self, state, api, page, router):
        self.state = state
        self.api = api
        self.page = page
        self.router = router
        self.container = None
        
        # Estado de la venta
        self.items_venta: List[Dict[str, Any]] = []
        self.total_venta = 0.0
        
        # Componentes principales
        self.items_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        self.total_text = ft.Text("Total: $0.00", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_600)
        
        # Cargar datos necesarios
        session = get_session_context()
        self.clientes_disponibles = ClienteRepository.listar_activos(session)
        self.productos_disponibles = ProductoRepository.listar_activos(session)
        session.close()
        
        # Componentes de formulario con búsqueda de cliente
        self.cliente_search = ft.TextField(
            label="Buscar cliente",
            hint_text="Escribe para buscar...",
            prefix_icon=ft.Icons.SEARCH,
            on_change=self._on_cliente_search,
            width=300,
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )

        self.cliente_dropdown = ft.Dropdown(
            label="Cliente (opcional)",
            hint_text="Seleccionar cliente",
            options=[ft.dropdown.Option(key=str(c.id), text=c.nombre) for c in self.clientes_disponibles],
            width=300,
            visible=False,
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
            bgcolor=ft.Colors.WHITE,
            fill_color=ft.Colors.WHITE,
        )

        self.es_fiado_checkbox = ft.Checkbox(
            label="Es fiado",
            value=False,
            on_change=self._on_fiado_change,
            check_color=ft.Colors.WHITE,
            fill_color=AppColors.PRIMARY,
            label_style=ft.TextStyle(color=AppColors.PRIMARY),
        )

        self.abonado_field = ft.TextField(
            label="Abono inicial",
            hint_text="0.00",
            value="0",
            prefix_icon=ft.Icons.ATTACH_MONEY,
            keyboard_type=ft.KeyboardType.NUMBER,
            visible=False,
            width=200,
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )
    
    def build(self):
        """Construye la interfaz de la página"""
        
        self.container = ft.Container(
            content=ft.Column([
                # Header
                ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        tooltip="Volver",
                        on_click=self._cancelar,
                        icon_color=AppColors.PRIMARY,
                    ),
                    ft.Text(
                        "Nueva Venta",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        expand=True,
                        color=AppColors.PRIMARY,
                    ),
                    self.total_text,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Divider(),
                
                # Sección de cliente y tipo de venta
                ft.Container(
                    content=ft.Column([
                        ft.Text("Información de la Venta", size=18, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
                        self.cliente_search,
                        self.cliente_dropdown,
                        ft.Row([
                            self.es_fiado_checkbox,
                            self.abonado_field,
                        ], spacing=20),
                    ], spacing=10),
                    bgcolor=AppColors.CARD_BG,
                    padding=15,
                    border_radius=10,
                ),
                
                ft.Divider(),
                
                # Botones para agregar productos
                ft.Row([
                    ft.Text("Productos", size=18, weight=ft.FontWeight.BOLD, expand=True, color=AppColors.PRIMARY),
                    ft.ElevatedButton(
                        "Agregar desde lista",
                        icon=ft.Icons.LIST,
                        on_click=self._mostrar_lista_productos,
                        bgcolor=AppColors.PRIMARY,
                        color=ft.Colors.WHITE,
                    ),
                    ft.ElevatedButton(
                        "Agregar manual",
                        icon=ft.Icons.EDIT,
                        on_click=self._mostrar_form_manual,
                        bgcolor=AppColors.PRIMARY,
                        color=ft.Colors.WHITE,
                    ),
                ], spacing=10),
                
                # Lista de items agregados
                ft.Container(
                    content=self.items_list,
                    border=ft.border.all(2, ft.Colors.GREY_300),
                    border_radius=10,
                    padding=15,
                    expand=True,
                ),
                
                # Botones de acción
                ft.Row([
                    ft.TextButton(
                        "Cancelar",
                        icon=ft.Icons.CANCEL,
                        on_click=self._cancelar,
                        style=ft.ButtonStyle(color=AppColors.PRIMARY),
                    ),
                    ft.ElevatedButton(
                        "Guardar Venta",
                        icon=ft.Icons.SAVE,
                        on_click=self._guardar_venta,
                        bgcolor=AppColors.SUCCESS,
                        color=ft.Colors.WHITE,
                    ),
                ], alignment=ft.MainAxisAlignment.END, spacing=10),
                
            ]),
            padding=20,
            expand=True,
        )
        
        # Inicializar la lista vacía visualmente
        self._actualizar_lista_items()
        
        return self.container
    
    def _on_fiado_change(self, e):
        """Muestra/oculta el campo de abono según si es fiado"""
        self.abonado_field.visible = self.es_fiado_checkbox.value
        if not self.es_fiado_checkbox.value:
            self.abonado_field.value = "0"
        self.page.update()
    
    def _on_cliente_search(self, e):
        """Filtra y muestra clientes según búsqueda"""
        texto = self.cliente_search.value.lower().strip()
        
        if not texto:
            # Ocultar dropdown si no hay texto
            self.cliente_dropdown.visible = False
            self.cliente_dropdown.value = None
        else:
            # Filtrar clientes
            clientes_filtrados = [
                c for c in self.clientes_disponibles
                if texto in c.nombre.lower()
            ]
            
            # Actualizar opciones del dropdown
            self.cliente_dropdown.options = [
                ft.dropdown.Option(key=str(c.id), text=c.nombre) 
                for c in clientes_filtrados
            ]
            
            # Mostrar dropdown
            self.cliente_dropdown.visible = True
            
            # Si hay exactamente un resultado, seleccionarlo automáticamente
            if len(clientes_filtrados) == 1:
                self.cliente_dropdown.value = str(clientes_filtrados[0].id)
        
        self.page.update()
    
    def _actualizar_lista_items(self):
        """Actualiza la visualización de items"""
        self.items_list.controls.clear()
        
        if not self.items_venta:
            self.items_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.SHOPPING_CART_OUTLINED, size=64, color=ft.Colors.GREY_400),
                        ft.Text(
                            "No hay productos agregados",
                            size=16,
                            color=AppColors.PRIMARY,
                            italic=True,
                        ),
                        ft.Text(
                            "Usa los botones de arriba para agregar productos",
                            size=12,
                            color=ft.Colors.GREY_400,
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                    alignment=ft.alignment.center,
                    padding=40,
                )
            )
        else:
            for idx, item in enumerate(self.items_venta):
                tipo_icono = ft.Icons.INVENTORY if item.get("producto_id") else ft.Icons.EDIT
                tipo_texto = "BD" if item.get("producto_id") else "Manual"
                
                self.items_list.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Row([
                                ft.Icon(tipo_icono, size=32, color=ft.Colors.WHITE),
                                ft.Column([
                                    ft.Row([
                                        ft.Text(item["nombre"], size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                        ft.Container(
                                            content=ft.Text(tipo_texto, size=10, color=AppColors.PRIMARY),
                                            bgcolor=ft.Colors.WHITE,
                                            padding=ft.padding.symmetric(horizontal=8, vertical=2),
                                            border_radius=5,
                                        ),
                                    ], spacing=10),
                                    ft.Text(
                                        f"${item['precio_unitario']:.2f} × {item['cantidad']} = ${item['subtotal']:.2f}",
                                        size=14,
                                        color=ft.Colors.WHITE70,
                                    ),
                                ], spacing=5, expand=True),
                                ft.Row([
                                    ft.IconButton(
                                        icon=ft.Icons.EDIT,
                                        icon_color=ft.Colors.WHITE,
                                        icon_size=24,
                                        tooltip="Editar",
                                        on_click=lambda e, i=idx: self._editar_item(i),
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE,
                                        icon_color=ft.Colors.RED_300,
                                        icon_size=24,
                                        tooltip="Eliminar",
                                        on_click=lambda e, i=idx: self._eliminar_item(i),
                                    ),
                                ]),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            padding=15,
                            bgcolor=AppColors.PRIMARY,
                            border_radius=10,
                        ),
                    )
                )
        
        self._actualizar_total()
        if self.container:  # Solo actualizar si ya está construido
            self.page.update()
    
    def _actualizar_total(self):
        """Recalcula y actualiza el total"""
        self.total_venta = sum(item["subtotal"] for item in self.items_venta)
        self.total_text.value = f"Total: ${self.total_venta:.2f}"
        # No llamar update() aquí porque puede no estar en la página aún
    
    def _eliminar_item(self, index: int):
        """Elimina un item de la lista"""
        self.items_venta.pop(index)
        self._actualizar_lista_items()

    def _editar_item(self, index: int):
        """Permite editar un producto agregado a la venta"""
        item = self.items_venta[index]

        # Campos editables según el tipo de producto
        nombre_field = ft.TextField(
            label="Nombre del producto",
            value=item["nombre"],
            prefix_icon=ft.Icons.EDIT,
            read_only=bool(item.get("producto_id")),  # si viene de BD, no editable
        )

        precio_field = ft.TextField(
            label="Precio unitario",
            value=str(item["precio_unitario"]),
            prefix_icon=ft.Icons.ATTACH_MONEY,
            keyboard_type=ft.KeyboardType.NUMBER,
            read_only=bool(item.get("producto_id")),  # precio fijo si es BD
        )

        cantidad_field = ft.TextField(
            label="Cantidad",
            value=str(item["cantidad"]),
            prefix_icon=ft.Icons.NUMBERS,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        subtotal_text = ft.Text(
            f"Subtotal: ${item['subtotal']:.2f}",
            size=16,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.GREEN_600,
        )

        def calcular_subtotal(e):
            try:
                precio = float(precio_field.value or 0)
                cantidad = float(cantidad_field.value or 0)
                subtotal = precio * cantidad
                subtotal_text.value = f"Subtotal: ${subtotal:.2f}"
                subtotal_text.update()
            except:
                pass

        cantidad_field.on_change = calcular_subtotal
        if not item.get("producto_id"):
            precio_field.on_change = calcular_subtotal

        def guardar_cambios(e):
            try:
                nuevo_nombre = nombre_field.value.strip()
                nuevo_precio = float(precio_field.value or 0)
                nueva_cantidad = float(cantidad_field.value or 0)

                if nueva_cantidad <= 0:
                    self._mostrar_error("La cantidad debe ser mayor a 0")
                    return
                if nuevo_precio <= 0:
                    self._mostrar_error("El precio debe ser mayor a 0")
                    return

                # Actualizar el item
                item["nombre"] = nuevo_nombre
                item["precio_unitario"] = nuevo_precio
                item["cantidad"] = nueva_cantidad
                item["subtotal"] = nuevo_precio * nueva_cantidad

                modal.open = False
                self.page.update()
                self._actualizar_lista_items()

            except ValueError:
                self._mostrar_error("Valores inválidos")

        modal = ft.AlertDialog(
            modal=True,
            bgcolor=AppColors.MODAL_BG,
            title=ft.Text("Editar producto", size=18, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
            content=ft.Container(
                content=ft.Column([
                    nombre_field,
                    precio_field,
                    cantidad_field,
                    ft.Divider(),
                    subtotal_text,
                ], spacing=10),
                width=400,
                height=200,
            ),
            actions=[
                ft.TextButton("Cancelar", style=ft.ButtonStyle(color=AppColors.PRIMARY), on_click=lambda e: self._cerrar_modal(modal)),
                ft.ElevatedButton("Guardar", icon=ft.Icons.SAVE, on_click=guardar_cambios),
            ],
        )

        self.page.overlay.append(modal)
        modal.open = True
        self.page.update()

    
    # ============================================
    # AGREGAR DESDE LISTA
    # ============================================
    def _mostrar_lista_productos(self, e):
        """Muestra la lista de productos disponibles"""
        
        # Buscador
        search_field = ft.TextField(
            label="Buscar producto",
            prefix_icon=ft.Icons.SEARCH,
            expand=True,
            dense=True,
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )
        
        productos_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        
        def renderizar_productos(productos):
            productos_list.controls.clear()
            
            if not productos:
                productos_list.controls.append(
                    ft.Text("No se encontraron productos", color=AppColors.PRIMARY, italic=True)
                )
            else:
                for prod in productos:
                    stock_color = AppColors.DANGER if prod.esta_bajo_stock() else AppColors.SUCCESS

                    productos_list.controls.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.Row([
                                    ft.Column([
                                        ft.Text(prod.nombre, size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                        ft.Row([
                                            ft.Icon(ft.Icons.INVENTORY_2, size=16, color=stock_color),
                                            ft.Text(
                                                f"Stock: {prod.cantidad_stock} {prod.unidad_medida}",
                                                size=13,
                                                color=stock_color,
                                            ),
                                        ], spacing=5),
                                        ft.Text(
                                            f"Precio: ${prod.precio_venta:.2f}",
                                            size=14,
                                            color=AppColors.SUCCESS,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                    ], spacing=5, expand=True),
                                    ft.IconButton(
                                        icon=ft.Icons.ADD_SHOPPING_CART,
                                        icon_color=ft.Colors.WHITE,
                                        icon_size=28,
                                        on_click=lambda e, p=prod: self._agregar_producto_bd(p, modal),
                                    ),
                                ]),
                                padding=15,
                                bgcolor=AppColors.CARD_DARK,
                                border_radius=10,
                            ),
                            elevation=0,
                        )
                    )
            
            # Usar page.update() en lugar de productos_list.update()
            self.page.update()
        
        def filtrar(e):
            texto = search_field.value.lower().strip()
            
            if not texto:
                productos_filtrados = self.productos_disponibles
            else:
                productos_filtrados = [
                    p for p in self.productos_disponibles
                    if texto in p.nombre.lower() or (p.codigo_barras and texto in p.codigo_barras)
                ]
            
            renderizar_productos(productos_filtrados)
        
        search_field.on_change = filtrar
        
        renderizar_productos(self.productos_disponibles)
        
        modal = ft.AlertDialog(
            modal=True,
            bgcolor=AppColors.MODAL_BG,
            title=ft.Text(
                "Seleccionar Producto",
                size=20,
                weight=ft.FontWeight.BOLD,
                color=AppColors.PRIMARY,
            ),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Container(
                            search_field,
                            padding=ft.padding.symmetric(horizontal=10, vertical=0),
                            margin=0,
                        ),
                        ft.Container(
                            content=ft.ListView(
                                controls=productos_list.controls,
                                expand=True,
                                spacing=5,
                                padding=ft.padding.symmetric(horizontal=10, vertical=5),
                            ),
                            expand=True,
                            padding=0,
                            margin=10,
                        ),
                    ],
                    spacing=0,
                    tight=True,
                ),
                width=800,
                height=400,
                padding=0,
            ),
            actions=[
                ft.TextButton("Cerrar", style=ft.ButtonStyle(color=AppColors.PRIMARY), on_click=lambda e: self._cerrar_modal(modal)),
            ],
        )
        
        self.page.overlay.append(modal)
        modal.open = True
        self.page.update()
    
    def _agregar_producto_bd(self, producto: Producto, modal_lista):
        """Agrega un producto de BD después de pedir cantidad"""
        
        cantidad_field = ft.TextField(
            label="Cantidad",
            value="1",
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_icon=ft.Icons.NUMBERS,
            autofocus=True,
        )
        
        subtotal_text = ft.Text(
            f"Subtotal: ${producto.precio_venta:.2f}",
            size=16,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.GREEN_600,
        )
        
        def calcular_subtotal(e):
            try:
                cant = float(cantidad_field.value or 0)
                subtotal = producto.precio_venta * cant
                subtotal_text.value = f"Subtotal: ${subtotal:.2f}"
                subtotal_text.update()
            except:
                pass
        
        cantidad_field.on_change = calcular_subtotal
        
        def confirmar(e):
            try:
                cantidad = float(cantidad_field.value or 0)
                
                if cantidad <= 0:
                    self._mostrar_error("La cantidad debe ser mayor a 0")
                    return
                
                if cantidad > producto.cantidad_stock:
                    self._mostrar_error(f"Stock insuficiente. Disponible: {producto.cantidad_stock}")
                    return
                
                subtotal = producto.precio_venta * cantidad
                
                self.items_venta.append({
                    "producto_id": producto.id,
                    "nombre": producto.nombre,
                    "precio_unitario": producto.precio_venta,
                    "cantidad": cantidad,
                    "subtotal": subtotal,
                    "descontar_stock": True
                })
                
                modal_cantidad.open = False
                if modal_lista:
                    modal_lista.open = False
                self.page.update()
                
                self._actualizar_lista_items()
                
            except ValueError:
                self._mostrar_error("Cantidad inválida")
        
        modal_cantidad = ft.AlertDialog(
            modal=True,
            bgcolor=AppColors.MODAL_BG,
            title=ft.Text(f"Cantidad de: {producto.nombre}", size=18, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
            content=ft.Container(
                content=ft.Column([
                    cantidad_field,
                    ft.Text(
                        f"Stock disponible: {producto.cantidad_stock} {producto.unidad_medida}",
                        size=12,
                        color=AppColors.PRIMARY,
                    ),
                    ft.Text(
                        f"Precio unitario: ${producto.precio_venta:.2f}",
                        size=14,
                        color=ft.Colors.BLUE_600,
                    ),
                    ft.Divider(),
                    subtotal_text,
                ], spacing=10),
                width=350,
                height=200,
            ),
            actions=[
                ft.TextButton("Cancelar", style=ft.ButtonStyle(color=AppColors.PRIMARY), on_click=lambda e: self._cerrar_modal(modal_cantidad)),
                ft.ElevatedButton("Agregar", icon=ft.Icons.ADD, on_click=confirmar),
            ],
        )
        
        self.page.overlay.append(modal_cantidad)
        modal_cantidad.open = True
        self.page.update()
    
    # ============================================
    # AGREGAR MANUAL
    # ============================================
    def _mostrar_form_manual(self, e):
        """Muestra formulario para ingresar producto manual"""
        
        nombre_field = ft.TextField(
            label="Nombre del producto *",
            prefix_icon=ft.Icons.EDIT,
            autofocus=True,
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )

        precio_field = ft.TextField(
            label="Precio *",
            value="0",
            prefix_icon=ft.Icons.ATTACH_MONEY,
            keyboard_type=ft.KeyboardType.NUMBER,
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )

        cantidad_field = ft.TextField(
            label="Cantidad *",
            value="1",
            prefix_icon=ft.Icons.NUMBERS,
            keyboard_type=ft.KeyboardType.NUMBER,
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )
        
        subtotal_text = ft.Text(
            "Subtotal: $0.00",
            size=18,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.GREEN_600,
        )
        
        def calcular_subtotal(e):
            try:
                precio = float(precio_field.value or 0)
                cantidad = float(cantidad_field.value or 0)
                subtotal = precio * cantidad
                subtotal_text.value = f"Subtotal: ${subtotal:.2f}"
                subtotal_text.update()
            except:
                pass
        
        precio_field.on_change = calcular_subtotal
        cantidad_field.on_change = calcular_subtotal
        
        def guardar_manual(e):
            if not nombre_field.value or nombre_field.value.strip() == "":
                self._mostrar_error("El nombre es obligatorio")
                return
            
            try:
                precio = float(precio_field.value or 0)
                cantidad = float(cantidad_field.value or 0)
                
                if precio <= 0:
                    self._mostrar_error("El precio debe ser mayor a 0")
                    return
                
                if cantidad <= 0:
                    self._mostrar_error("La cantidad debe ser mayor a 0")
                    return
                
                subtotal = precio * cantidad
                
                self.items_venta.append({
                    "producto_id": None,
                    "nombre": nombre_field.value.strip(),
                    "precio_unitario": precio,
                    "cantidad": cantidad,
                    "subtotal": subtotal,
                    "descontar_stock": False
                })
                
                modal.open = False
                self.page.update()
                
                self._actualizar_lista_items()
                
            except ValueError:
                self._mostrar_error("Valores numéricos inválidos")
        
        modal = ft.AlertDialog(
            modal=True,
            bgcolor=AppColors.MODAL_BG,
            title=ft.Text("Producto Manual", size=20, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
            content=ft.Container(
                content=ft.Column([
                    nombre_field,
                    precio_field,
                    cantidad_field,
                    ft.Divider(),
                    subtotal_text,
                ], spacing=15),
                width=400,
                height=250,
            ),
            actions=[
                ft.TextButton("Cancelar", style=ft.ButtonStyle(color=AppColors.PRIMARY), on_click=lambda e: self._cerrar_modal(modal)),
                ft.ElevatedButton("Agregar", icon=ft.Icons.ADD, bgcolor=AppColors.PRIMARY, color=ft.Colors.WHITE, on_click=guardar_manual),
            ],
        )
        
        self.page.overlay.append(modal)
        modal.open = True
        self.page.update()
    
    # ============================================
    # ACCIONES PRINCIPALES
    # ============================================
    def _guardar_venta(self, e):
        """Guarda la venta en la base de datos"""
        
        if not self.items_venta:
            self._mostrar_error("Debes agregar al menos un producto")
            return
        
        try:
            cliente_id = None
            cliente_nombre = None
            
            # Buscar cliente seleccionado en el dropdown
            if self.cliente_dropdown.value:
                cliente_id = int(self.cliente_dropdown.value)
                cliente_seleccionado = next(
                    (c for c in self.clientes_disponibles if c.id == cliente_id),
                    None
                )
                if cliente_seleccionado:
                    cliente_nombre = cliente_seleccionado.nombre
            
            es_fiado = self.es_fiado_checkbox.value
            abono = float(self.abonado_field.value or 0)
            
            if es_fiado and not cliente_id:
                self._mostrar_error("Debes seleccionar un cliente para ventas fiadas")
                return
            
            if abono < 0:
                self._mostrar_error("El abono no puede ser negativo")
                return
            
            # Obtener usuario actual del estado
            usuario_actual = self.state.get("usuario_actual")

            nueva_venta = Venta(
                cliente_id=cliente_id,
                cliente_nombre=cliente_nombre,
                productos=self.items_venta,
                es_fiado=es_fiado,
                abonado=0,  # Inicialmente 0, se registrará como abono si corresponde
                usuario_id=usuario_actual.id if usuario_actual else None,
                usuario_nombre=usuario_actual.nombre if usuario_actual else None
            )

            nueva_venta.calcular_totales()

            session = get_session_context()
            venta_creada = VentaRepository.crear(session, nueva_venta)

            # Si hay un abono inicial, registrarlo en la tabla de abonos
            if es_fiado and abono > 0:
                AbonoRepository.crear(
                    session,
                    venta_creada.id,
                    abono,
                    "Abono inicial al momento de la venta",
                    usuario_id=usuario_actual.id if usuario_actual else None,
                    usuario_nombre=usuario_actual.nombre if usuario_actual else None
                )

            session.close()
            
            # ✨ Mostrar diálogo de confirmación para imprimir
            self._mostrar_dialogo_imprimir(nueva_venta)
            
        except Exception as error:
            self._mostrar_error(f"Error al crear venta: {error}")

    def _mostrar_dialogo_imprimir(self, venta):
        """Muestra un diálogo preguntando si desea imprimir el comprobante"""

        # Referencias a los botones para poder deshabilitarlos
        btn_imprimir = None
        btn_solo_guardar = None
        btn_no_imprimir = None
        progress_ring = ft.ProgressRing(visible=False, width=20, height=20)

        def imprimir_directo(e):
            try:
                es_web = getattr(self.page, 'web', False)

                # Cerrar el modal de confirmación primero
                modal.open = False
                self.page.update()

                # Usar método unificado (detecta web/desktop automáticamente)
                PDFGenerator.imprimir_o_mostrar(self.page, venta=venta, tipo='venta')

                # Solo mostrar snackbar en desktop (en web el modal del PDF ya informa)
                if not es_web:
                    self._mostrar_exito(f"Venta #{venta.id} registrada. Enviado a impresora.")
                    self.router.navigate("ventas")

            except Exception as error:
                self._mostrar_error(f"Error al generar comprobante: {error}")

        def solo_guardar(e):
            # En web no tiene sentido "solo guardar", redirigir sin comprobante
            self._mostrar_exito(f"Venta #{venta.id} registrada exitosamente")
            modal.open = False
            self.page.update()
            self.router.navigate("ventas")
        
        def no_imprimir(e):
            self._mostrar_exito(f"Venta #{venta.id} registrada exitosamente")
            modal.open = False
            self.page.update()
            self.router.navigate("ventas")
        
        # Crear botones con referencias
        btn_solo_guardar = ft.TextButton(
            "Solo guardar",
            icon=ft.Icons.SAVE,
            style=ft.ButtonStyle(color=AppColors.PRIMARY),
            on_click=solo_guardar,
        )

        btn_no_imprimir = ft.TextButton(
            "No, gracias",
            icon=ft.Icons.CANCEL,
            style=ft.ButtonStyle(color=AppColors.PRIMARY),
            on_click=no_imprimir,
        )

        btn_imprimir = ft.ElevatedButton(
            "Imprimir",
            icon=ft.Icons.PRINT,
            bgcolor=AppColors.PRIMARY,
            color=ft.Colors.WHITE,
            on_click=imprimir_directo,
        )

        modal = ft.AlertDialog(
            modal=True,
            bgcolor=AppColors.MODAL_BG,
            title=ft.Row([
                ft.Icon(ft.Icons.PRINT, size=32, color=ft.Colors.GREEN_600),
                ft.Text("Venta registrada", size=20, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
                progress_ring,
            ], spacing=10),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        f"La venta #{venta.id} se ha guardado correctamente.",
                        size=14,
                        color=AppColors.PRIMARY,
                    ),
                    ft.Divider(),
                    ft.Text(
                        "¿Qué desea hacer?",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.PRIMARY,
                    ),
                ], spacing=10, tight=True),
                width=400,
            ),
            actions=[
                btn_solo_guardar,
                btn_no_imprimir,
                btn_imprimir,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(modal)
        modal.open = True
        self.page.update()
    
    def _cancelar(self, e):
        """Cancela la operación y vuelve a la lista de ventas"""
        self.router.navigate("ventas")
    
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