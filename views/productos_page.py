"""Vista de gestión de productos"""

import flet as ft
from typing import List
from datetime import datetime
from models.producto import Producto
from database.connection import get_session_context
from database.db_service import ProductoRepository
from config.settings import AppColors


class ProductosPage:
    """Página de gestión de productos"""
    
    def __init__(self, state, api, page):
        self.state = state
        self.api = api
        self.page = page
        self.container = None
        
        # Componentes
        self.search_field = ft.TextField(
            label="Buscar producto por nombre",
            prefix_icon=ft.Icons.SEARCH,
            color=AppColors.PRIMARY,
            bgcolor=AppColors.INPUT_BG,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
            on_change=self._on_search_change,
            expand=True,
        )
        
        self.productos_list = ft.Column(
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )
        
        self.loading = ft.ProgressRing(visible=False)
        
        # Lista completa de productos (para filtrar)
        self.todos_productos: List[Producto] = []
    
    def build(self):
        """Construye la interfaz de la página"""
        
        self.container = ft.Container(
            content=ft.Column([
                # Header
                ft.Row([
                    ft.Text(
                        "Gestión de Productos",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.PRIMARY
                    ),
                    ft.IconButton(
                        icon=ft.Icons.REFRESH,
                        tooltip="Recargar lista",
                        on_click=self._cargar_productos,
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Divider(),
                
                # Barra de búsqueda
                ft.Row([
                    self.search_field,
                    ft.ElevatedButton(
                        "Nuevo Producto",
                        icon=ft.Icons.ADD,
                        bgcolor=AppColors.PRIMARY,
                        color=ft.Colors.WHITE,
                        on_click=self._nuevo_producto,
                    ),
                ]),
                
                # Indicador de carga
                self.loading,
                
                # Lista de productos
                ft.Container(
                    content=self.productos_list,
                    expand=True,
                ),
                
            ]),
            padding=20,
            expand=True,
        )
        
        # Cargar productos al iniciar
        self._cargar_productos(None)
        
        return self.container
    
    def _cargar_productos(self, e):
        """Carga la lista de productos desde la base de datos"""
        self.loading.visible = True
        self.page.update()
        
        try:
            session = get_session_context()
            self.todos_productos = ProductoRepository.listar_activos(session)
            session.close()
            
            self._actualizar_lista(self.todos_productos)
            
        except Exception as error:
            self._mostrar_error(f"Error al cargar productos: {error}")
        finally:
            self.loading.visible = False
            self.page.update()
    
    def _on_search_change(self, e):
        """Filtra la lista cuando cambia el texto de búsqueda"""
        texto_busqueda = self.search_field.value.lower().strip()
        
        if not texto_busqueda:
            self._actualizar_lista(self.todos_productos)
        else:
            productos_filtrados = [
                p for p in self.todos_productos
                if texto_busqueda in p.nombre.lower()
            ]
            self._actualizar_lista(productos_filtrados)
    
    def _actualizar_lista(self, productos: List[Producto]):
        """Actualiza la lista visual de productos"""
        self.productos_list.controls.clear()
        
        if not productos:
            self.productos_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No se encontraron productos",
                        size=16,
                        color=AppColors.PRIMARY,
                        italic=True,
                    ),
                    padding=20,
                    alignment=ft.alignment.center,
                )
            )
        else:
            for producto in productos:
                self.productos_list.controls.append(
                    self._crear_card_producto(producto)
                )
        
        self.page.update()
    
    def _crear_card_producto(self, producto: Producto) -> ft.Card:
        """Crea una tarjeta para mostrar un producto"""
        
        # Indicadores visuales
        stock_bajo = producto.esta_bajo_stock()
        stock_color = AppColors.DANGER if stock_bajo else AppColors.SUCCESS
        margen = producto.calcular_margen()
        
        return ft.Card(
            content=ft.Container(
                content=ft.Row([
                    # Información principal
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.INVENTORY, size=20, color=ft.Colors.WHITE),
                                ft.Text(
                                    producto.nombre,
                                    size=18,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                ),
                            ]),

                            # Categoría y código
                            ft.Row([
                                ft.Icon(ft.Icons.CATEGORY, size=16, color=ft.Colors.WHITE70),
                                ft.Text(
                                    producto.categoria or "Sin categoría",
                                    size=14,
                                    color=ft.Colors.WHITE70,
                                ),
                            ], spacing=5) if producto.categoria else ft.Container(),

                            ft.Row([
                                ft.Icon(ft.Icons.QR_CODE, size=16, color=ft.Colors.WHITE70),
                                ft.Text(
                                    producto.codigo_barras or "Sin código",
                                    size=14,
                                    color=ft.Colors.WHITE70,
                                ),
                            ], spacing=5) if producto.codigo_barras else ft.Container(),

                        ], spacing=5),
                        expand=True,
                    ),

                    # Precios
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Precios", size=12, color=ft.Colors.WHITE70, weight=ft.FontWeight.BOLD),
                            ft.Row([
                                ft.Text("Costo:", size=12, color=ft.Colors.WHITE70),
                                ft.Text(f"${producto.precio_proveedor:.2f}", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            ]),
                            ft.Row([
                                ft.Text("Venta:", size=12, color=ft.Colors.WHITE70),
                                ft.Text(f"${producto.precio_venta:.2f}", size=14, weight=ft.FontWeight.BOLD, color=AppColors.SUCCESS),
                            ]),
                            ft.Text(f"Margen: {margen:.1f}%", size=12, color=ft.Colors.YELLOW_300),
                        ], spacing=3),
                        width=120,
                    ),

                    # Stock
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Stock", size=12, color=ft.Colors.WHITE70, weight=ft.FontWeight.BOLD),
                            ft.Row([
                                ft.Icon(
                                    ft.Icons.INVENTORY_2 if not stock_bajo else ft.Icons.WARNING,
                                    color=stock_color,
                                    size=16
                                ),
                                ft.Text(
                                    f"{producto.cantidad_stock} {producto.unidad_medida}",
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                    color=stock_color,
                                ),
                            ]),
                            ft.Text(
                                f"Mín: {producto.stock_minimo}",
                                size=12,
                                color=ft.Colors.WHITE70,
                            ),
                        ], spacing=3),
                        width=100,
                    ),

                    # Botones de acción
                    ft.Container(
                        content=ft.Row([
                            ft.IconButton(
                                icon=ft.Icons.VISIBILITY,
                                icon_color=ft.Colors.BLUE_200,
                                tooltip="Ver detalles",
                                on_click=lambda e, p=producto: self._ver_producto(p),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.EDIT,
                                icon_color=ft.Colors.ORANGE_300,
                                tooltip="Editar",
                                on_click=lambda e, p=producto: self._editar_producto(p),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                icon_color=AppColors.DANGER,
                                tooltip="Eliminar",
                                on_click=lambda e, p=producto: self._confirmar_eliminacion(p),
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
    # MODAL: NUEVO PRODUCTO
    # ============================================
    def _nuevo_producto(self, e):
        """Abre el modal para crear un nuevo producto"""
        
        # Texto de ayuda para margen
        margen_info = ft.Text("", size=12, color=AppColors.PRIMARY)
        error_precio = ft.Text("", size=12, color=AppColors.DANGER, visible=False)
        
        nombre_field = ft.TextField(
            label="Nombre *",
            hint_text="Nombre del producto",
            autofocus=True,
        )
        
        codigo_field = ft.TextField(
            label="Código de barras",
            hint_text="7790315241234",
            prefix_icon=ft.Icons.QR_CODE,
        )
        
        categoria_field = ft.TextField(
            label="Categoría",
            hint_text="Ej: Bebidas, Almacén, etc.",
            prefix_icon=ft.Icons.CATEGORY,
        )
        
        def validar_numero(e, campo):
            """Valida que solo se ingresen números"""
            valor = campo.value
            # Permitir solo números, punto decimal y vacío
            if valor and not all(c.isdigit() or c == '.' for c in valor):
                # Quitar caracteres no numéricos
                nuevo_valor = ''.join(c for c in valor if c.isdigit() or c == '.')
                campo.value = nuevo_valor
                campo.update()
        
        def calcular_margen(e):
            """Calcula y muestra el margen de ganancia"""
            try:
                costo = float(precio_proveedor_field.value or 0)
                venta = float(precio_venta_field.value or 0)
                
                if costo > 0:
                    if venta < costo:
                        error_precio.value = "⚠️ El precio de venta no puede ser menor al costo"
                        error_precio.visible = True
                        margen_info.value = ""
                        margen_info.color = AppColors.DANGER
                    else:
                        error_precio.visible = False
                        ganancia = venta - costo
                        margen = ((venta - costo) / costo) * 100
                        margen_info.value = f"💰 Ganancia: ${ganancia:.2f} | Margen: {margen:.1f}%"
                        margen_info.color = ft.Colors.GREEN_600
                else:
                    error_precio.visible = False
                    margen_info.value = ""
                
                margen_info.update()
                error_precio.update()
            except:
                pass
        
        precio_proveedor_field = ft.TextField(
            label="Precio Proveedor *",
            hint_text="0.00",
            value="0",
            prefix_icon=ft.Icons.SHOPPING_CART,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda e: [validar_numero(e, precio_proveedor_field), calcular_margen(e)],
        )
        
        precio_venta_field = ft.TextField(
            label="Precio Venta *",
            hint_text="0.00",
            value="0",
            prefix_icon=ft.Icons.ATTACH_MONEY,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda e: [validar_numero(e, precio_venta_field), calcular_margen(e)],
        )
        
        stock_field = ft.TextField(
            label="Stock Inicial",
            hint_text="0",
            value="0",
            prefix_icon=ft.Icons.INVENTORY,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda e: validar_numero(e, stock_field),
        )
        
        stock_minimo_field = ft.TextField(
            label="Stock Mínimo",
            hint_text="0",
            value="0",
            prefix_icon=ft.Icons.WARNING,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda e: validar_numero(e, stock_minimo_field),
        )
        
        unidad_field = ft.Dropdown(
            label="Unidad de medida",
            options=[
                ft.dropdown.Option("unidad"),
                ft.dropdown.Option("kg"),
                ft.dropdown.Option("litro"),
                ft.dropdown.Option("metro"),
                ft.dropdown.Option("caja"),
            ],
            value="unidad",
        )
        
        proveedor_field = ft.TextField(
            label="Proveedor",
            hint_text="Nombre del proveedor",
            prefix_icon=ft.Icons.LOCAL_SHIPPING,
        )
        
        descripcion_field = ft.TextField(
            label="Descripción",
            hint_text="Información adicional",
            multiline=True,
            min_lines=2,
            max_lines=3,
        )
        
        def guardar_producto(e):
            # Validaciones
            if not nombre_field.value or nombre_field.value.strip() == "":
                self._mostrar_error("El nombre es obligatorio")
                return
            
            try:
                precio_costo = float(precio_proveedor_field.value or 0)
                precio_vta = float(precio_venta_field.value or 0)
                
                if precio_costo < 0:
                    self._mostrar_error("El precio de proveedor no puede ser negativo")
                    return
                
                if precio_vta < 0:
                    self._mostrar_error("El precio de venta no puede ser negativo")
                    return
                
                if precio_vta < precio_costo:
                    self._mostrar_error("El precio de venta no puede ser menor al precio de proveedor")
                    return
                
                stock = float(stock_field.value or 0)
                stock_min = float(stock_minimo_field.value or 0)
                
                if stock < 0:
                    self._mostrar_error("El stock no puede ser negativo")
                    return
                
                if stock_min < 0:
                    self._mostrar_error("El stock mínimo no puede ser negativo")
                    return
                
                nuevo_producto = Producto(
                    nombre=nombre_field.value.strip(),
                    codigo_barras=codigo_field.value.strip() or None,
                    categoria=categoria_field.value.strip() or None,
                    precio_proveedor=precio_costo,
                    precio_venta=precio_vta,
                    cantidad_stock=stock,
                    stock_minimo=stock_min,
                    unidad_medida=unidad_field.value,
                    proveedor=proveedor_field.value.strip() or None,
                    descripcion=descripcion_field.value.strip() or None,
                )
                
                session = get_session_context()
                ProductoRepository.crear(session, nuevo_producto)
                session.close()
                
                modal.open = False
                self.page.update()
                self._mostrar_exito(f"Producto '{nuevo_producto.nombre}' creado exitosamente")
                self._cargar_productos(None)
                
            except ValueError:
                self._mostrar_error("Por favor, ingresa valores numéricos válidos")
            except Exception as error:
                self._mostrar_error(f"Error al crear producto: {error}")
        
        modal = ft.AlertDialog(
            modal=True,
            bgcolor=AppColors.MODAL_BG,
            title=ft.Text("Nuevo Producto", size=20, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
            content=ft.Container(
                content=ft.Column([
                    nombre_field,
                    ft.Row([codigo_field, categoria_field], spacing=10),
                    ft.Row([precio_proveedor_field, precio_venta_field], spacing=10),
                    error_precio,
                    margen_info,
                    ft.Row([stock_field, stock_minimo_field], spacing=10),
                    ft.Row([unidad_field, proveedor_field], spacing=10),
                    descripcion_field,
                ], tight=True, spacing=10, scroll=ft.ScrollMode.AUTO),
                width=600,
                height=550,
            ),
            actions=[
                ft.TextButton("Cancelar", style=ft.ButtonStyle(color=AppColors.PRIMARY), on_click=lambda e: self._cerrar_modal(modal)),
                ft.ElevatedButton("Guardar", on_click=guardar_producto),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(modal)
        modal.open = True
        self.page.update()
    
    # ============================================
    # MODAL: VER DETALLES
    # ============================================
    def _ver_producto(self, producto: Producto):
        """Muestra los detalles completos de un producto"""
        
        session = get_session_context()
        producto_actual = ProductoRepository.obtener_por_id(session, producto.id)
        session.close()
        
        if not producto_actual:
            self._mostrar_error("Producto no encontrado")
            return
        
        ganancia = producto_actual.calcular_ganancia()
        margen = producto_actual.calcular_margen()
        stock_bajo = producto_actual.esta_bajo_stock()
        
        contenido = ft.Column([
            # Información básica
            self._crear_campo_detalle("Nombre", producto_actual.nombre, ft.Icons.INVENTORY),
            self._crear_campo_detalle("Código de barras", producto_actual.codigo_barras or "No especificado", ft.Icons.QR_CODE),
            self._crear_campo_detalle("Categoría", producto_actual.categoria or "Sin categoría", ft.Icons.CATEGORY),
            
            ft.Divider(),
            
            # Precios y rentabilidad
            ft.Text("Información de Precios", weight=ft.FontWeight.BOLD, size=16),
            self._crear_campo_detalle("Precio Proveedor", f"${producto_actual.precio_proveedor:.2f}", ft.Icons.SHOPPING_CART),
            self._crear_campo_detalle("Precio Venta", f"${producto_actual.precio_venta:.2f}", ft.Icons.POINT_OF_SALE, color=ft.Colors.GREEN_600),
            self._crear_campo_detalle("Ganancia por unidad", f"${ganancia:.2f}", ft.Icons.TRENDING_UP, color=ft.Colors.BLUE_600),
            self._crear_campo_detalle("Margen de ganancia", f"{margen:.1f}%", ft.Icons.PERCENT, color=ft.Colors.PURPLE_600),
            
            ft.Divider(),
            
            # Inventario
            ft.Text("Inventario", weight=ft.FontWeight.BOLD, size=16),
            self._crear_campo_detalle(
                "Stock actual",
                f"{producto_actual.cantidad_stock} {producto_actual.unidad_medida}",
                ft.Icons.INVENTORY_2,
                color=AppColors.DANGER if stock_bajo else AppColors.SUCCESS
            ),
            self._crear_campo_detalle("Stock mínimo", f"{producto_actual.stock_minimo} {producto_actual.unidad_medida}", ft.Icons.WARNING),
            
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.WARNING, color=ft.Colors.ORANGE_400),
                    ft.Text("¡Stock bajo! Considere reabastecerse", color=ft.Colors.ORANGE_700),
                ]),
                bgcolor=ft.Colors.ORANGE_50,
                padding=10,
                border_radius=5,
            ) if stock_bajo else ft.Container(),
            
            ft.Divider(),
            
            # Proveedor
            ft.Text("Proveedor", weight=ft.FontWeight.BOLD, size=16),
            ft.Text(producto_actual.proveedor or "No especificado", color=AppColors.PRIMARY),
            
            ft.Divider(),
            
            # Descripción
            ft.Text("Descripción", weight=ft.FontWeight.BOLD, size=16),
            ft.Text(producto_actual.descripcion or "Sin descripción", color=AppColors.PRIMARY),
            
            ft.Divider(),
            
            # Metadata
            ft.Text("Información del sistema", size=12, color=AppColors.PRIMARY),
            ft.Text(f"Creado: {producto_actual.fecha_creacion.strftime('%d/%m/%Y %H:%M')}", size=12, color=AppColors.PRIMARY),
        ], spacing=10, scroll=ft.ScrollMode.AUTO)
        
        modal = ft.AlertDialog(
            modal=True,
            bgcolor=AppColors.MODAL_BG,
            title=ft.Row([
                ft.Icon(ft.Icons.INFO, color=ft.Colors.BLUE_400),
                ft.Text("Detalles del Producto", size=20, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
            ]),
            content=ft.Container(content=contenido, width=500, height=500),
            actions=[
                ft.TextButton("Cerrar", style=ft.ButtonStyle(color=AppColors.PRIMARY), on_click=lambda e: self._cerrar_modal(modal)),
                ft.ElevatedButton(
                    "Editar",
                    icon=ft.Icons.EDIT,
                    on_click=lambda e: [self._cerrar_modal(modal), self._editar_producto(producto_actual)]
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
            ft.Icon(icono, size=20, color=color or ft.Colors.GREY_600),
            ft.Column([
                ft.Text(label, size=12, color=AppColors.PRIMARY, weight=ft.FontWeight.BOLD),
                ft.Text(valor, size=14, color=color or ft.Colors.BLACK),
            ], spacing=2),
        ], spacing=10)
    
    # ============================================
    # MODAL: EDITAR PRODUCTO
    # ============================================
    def _editar_producto(self, producto: Producto):
        """Abre el modal para editar un producto"""
        
        # Texto de ayuda para margen
        margen_info = ft.Text("", size=12, color=AppColors.PRIMARY)
        error_precio = ft.Text("", size=12, color=AppColors.DANGER, visible=False)
        
        nombre_field = ft.TextField(
            label="Nombre *",
            value=producto.nombre,
            autofocus=True,
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )
        codigo_field = ft.TextField(
            label="Código de barras",
            value=producto.codigo_barras or "",
            prefix_icon=ft.Icons.QR_CODE,
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )
        categoria_field = ft.TextField(
            label="Categoría",
            value=producto.categoria or "",
            prefix_icon=ft.Icons.CATEGORY,
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )
        
        def validar_numero(e, campo):
            """Valida que solo se ingresen números"""
            valor = campo.value
            if valor and not all(c.isdigit() or c == '.' for c in valor):
                nuevo_valor = ''.join(c for c in valor if c.isdigit() or c == '.')
                campo.value = nuevo_valor
                campo.update()
        
        def calcular_margen(e):
            """Calcula y muestra el margen de ganancia"""
            try:
                costo = float(precio_proveedor_field.value or 0)
                venta = float(precio_venta_field.value or 0)
                
                if costo > 0:
                    if venta < costo:
                        error_precio.value = "⚠️ El precio de venta no puede ser menor al costo"
                        error_precio.visible = True
                        margen_info.value = ""
                        margen_info.color = AppColors.DANGER
                    else:
                        error_precio.visible = False
                        ganancia = venta - costo
                        margen = ((venta - costo) / costo) * 100
                        margen_info.value = f"💰 Ganancia: ${ganancia:.2f} | Margen: {margen:.1f}%"
                        margen_info.color = ft.Colors.GREEN_600
                else:
                    error_precio.visible = False
                    margen_info.value = ""
                
                margen_info.update()
                error_precio.update()
            except:
                pass
        
        precio_proveedor_field = ft.TextField(
            label="Precio Proveedor *",
            value=str(producto.precio_proveedor),
            prefix_icon=ft.Icons.SHOPPING_CART,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda e: [validar_numero(e, precio_proveedor_field), calcular_margen(e)],
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )

        precio_venta_field = ft.TextField(
            label="Precio Venta *",
            value=str(producto.precio_venta),
            prefix_icon=ft.Icons.ATTACH_MONEY,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda e: [validar_numero(e, precio_venta_field), calcular_margen(e)],
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )

        stock_field = ft.TextField(
            label="Stock",
            value=str(producto.cantidad_stock),
            prefix_icon=ft.Icons.INVENTORY,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda e: validar_numero(e, stock_field),
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )

        stock_minimo_field = ft.TextField(
            label="Stock Mínimo",
            value=str(producto.stock_minimo),
            prefix_icon=ft.Icons.WARNING,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda e: validar_numero(e, stock_minimo_field),
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )

        unidad_field = ft.Dropdown(
            label="Unidad de medida",
            options=[
                ft.dropdown.Option("unidad"),
                ft.dropdown.Option("kg"),
                ft.dropdown.Option("litro"),
                ft.dropdown.Option("metro"),
                ft.dropdown.Option("caja"),
            ],
            value=producto.unidad_medida,
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )

        proveedor_field = ft.TextField(
            label="Proveedor",
            value=producto.proveedor or "",
            prefix_icon=ft.Icons.LOCAL_SHIPPING,
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )
        descripcion_field = ft.TextField(
            label="Descripción",
            value=producto.descripcion or "",
            multiline=True,
            min_lines=2,
            max_lines=3,
            color=AppColors.PRIMARY,
            border_color=AppColors.INPUT_BORDER,
            focused_border_color=AppColors.INPUT_FOCUS,
        )
        
        # Calcular margen inicial
        calcular_margen(None)
        
        def actualizar_producto(e):
            # Validaciones
            if not nombre_field.value or nombre_field.value.strip() == "":
                self._mostrar_error("El nombre es obligatorio")
                return
            
            try:
                precio_costo = float(precio_proveedor_field.value or 0)
                precio_vta = float(precio_venta_field.value or 0)
                
                if precio_costo < 0:
                    self._mostrar_error("El precio de proveedor no puede ser negativo")
                    return
                
                if precio_vta < 0:
                    self._mostrar_error("El precio de venta no puede ser negativo")
                    return
                
                if precio_vta < precio_costo:
                    self._mostrar_error("El precio de venta no puede ser menor al precio de proveedor")
                    return
                
                stock = float(stock_field.value or 0)
                stock_min = float(stock_minimo_field.value or 0)
                
                if stock < 0:
                    self._mostrar_error("El stock no puede ser negativo")
                    return
                
                if stock_min < 0:
                    self._mostrar_error("El stock mínimo no puede ser negativo")
                    return
                
                producto.nombre = nombre_field.value.strip()
                producto.codigo_barras = codigo_field.value.strip() or None
                producto.categoria = categoria_field.value.strip() or None
                producto.precio_proveedor = precio_costo
                producto.precio_venta = precio_vta
                producto.cantidad_stock = stock
                producto.stock_minimo = stock_min
                producto.unidad_medida = unidad_field.value
                producto.proveedor = proveedor_field.value.strip() or None
                producto.descripcion = descripcion_field.value.strip() or None
                producto.fecha_actualizacion = datetime.now()
                
                session = get_session_context()
                ProductoRepository.actualizar(session, producto)
                session.close()
                
                modal.open = False
                self.page.update()
                self._mostrar_exito(f"Producto '{producto.nombre}' actualizado exitosamente")
                self._cargar_productos(None)
                
            except ValueError:
                self._mostrar_error("Por favor, ingresa valores numéricos válidos")
            except Exception as error:
                self._mostrar_error(f"Error al actualizar producto: {error}")
        
        modal = ft.AlertDialog(
            modal=True,
            bgcolor=AppColors.MODAL_BG,
            title=ft.Text("Editar Producto", size=20, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
            content=ft.Container(
                content=ft.Column([
                    nombre_field,
                    ft.Row([codigo_field, categoria_field], spacing=10),
                    ft.Row([precio_proveedor_field, precio_venta_field], spacing=10),
                    error_precio,
                    margen_info,
                    ft.Row([stock_field, stock_minimo_field], spacing=10),
                    ft.Row([unidad_field, proveedor_field], spacing=10),
                    descripcion_field,
                ], tight=True, spacing=10, scroll=ft.ScrollMode.AUTO),
                width=600,
                height=550,
            ),
            actions=[
                ft.TextButton("Cancelar", style=ft.ButtonStyle(color=AppColors.PRIMARY), on_click=lambda e: self._cerrar_modal(modal)),
                ft.ElevatedButton("Actualizar", bgcolor=AppColors.PRIMARY, color=ft.Colors.WHITE, on_click=actualizar_producto),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(modal)
        modal.open = True
        self.page.update()
    
    # ============================================
    # MODAL: CONFIRMAR ELIMINACIÓN
    # ============================================
    def _confirmar_eliminacion(self, producto: Producto):
        """Muestra un diálogo de confirmación antes de eliminar"""
        
        def eliminar(e):
            try:
                session = get_session_context()
                producto.activo = False
                producto.fecha_actualizacion = datetime.now()
                ProductoRepository.actualizar(session, producto)
                session.close()
                
                modal.open = False
                self.page.update()
                self._mostrar_exito(f"Producto '{producto.nombre}' eliminado exitosamente")
                self._cargar_productos(None)
                
            except Exception as error:
                self._mostrar_error(f"Error al eliminar producto: {error}")
        
        # Advertencia si tiene stock
        advertencia = None
        if producto.cantidad_stock > 0:
            advertencia = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.WARNING, color=ft.Colors.ORANGE_400),
                    ft.Text(
                        f"⚠️ Este producto tiene {producto.cantidad_stock} {producto.unidad_medida} en stock",
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
                    f"¿Estás seguro de que deseas eliminar el producto '{producto.nombre}'?",
                    size=16,
                ),
                ft.Text(
                    "Esta acción desactivará el producto pero no eliminará su historial.",
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