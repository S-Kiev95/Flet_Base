"""Generador de PDFs para comprobantes de venta y liquidaciones"""

import os
import io
import base64
import tempfile
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

# Tamaños de papel personalizados
# Para impresoras térmicas, usamos altura más corta y ajustable
TICKET_80MM = (80*mm, 200*mm)  # 80mm de ancho, altura ajustable para térmica


class PDFGenerator:
    """Clase para generar PDFs de ventas y liquidaciones"""
    
    @staticmethod
    def generar_comprobante_venta(venta, ruta_salida=None, tipo_papel='80mm'):
        """
        Genera un PDF con el comprobante de venta

        Args:
            venta: Objeto Venta con todos los datos
            ruta_salida: Ruta donde guardar el PDF (opcional)
            tipo_papel: '80mm' o 'A4' (por defecto '80mm')

        Returns:
            str: Ruta del archivo PDF generado
        """

        # Si no se proporciona ruta, crear archivo temporal
        if not ruta_salida:
            # Crear archivo temporal que se eliminará automáticamente
            temp_file = tempfile.NamedTemporaryFile(
                mode='w+b',
                suffix='.pdf',
                prefix=f'venta_{venta.id}_',
                delete=False  # No eliminar inmediatamente, lo haremos después de imprimir
            )
            ruta_salida = temp_file.name
            temp_file.close()

        # Seleccionar tamaño de papel
        pagesize = TICKET_80MM if tipo_papel == '80mm' else A4

        # Crear documento PDF
        doc = SimpleDocTemplate(
            ruta_salida,
            pagesize=pagesize,
            leftMargin=3*mm if tipo_papel == '80mm' else 0.75*inch,
            rightMargin=3*mm if tipo_papel == '80mm' else 0.75*inch,
            topMargin=3*mm if tipo_papel == '80mm' else 0.75*inch,
            bottomMargin=3*mm if tipo_papel == '80mm' else 0.75*inch,
        )
        elementos = []
        
        # Estilos adaptados al tamaño de papel
        estilos = getSampleStyleSheet()

        if tipo_papel == '80mm':
            # Estilos para ticket 80mm - optimizados para impresora térmica
            estilo_titulo = ParagraphStyle(
                'CustomTitle',
                parent=estilos['Heading1'],
                fontSize=12,
                textColor=colors.black,
                spaceAfter=4,
                alignment=TA_CENTER,
                wordWrap='CJK',
                leading=14,
            )

            estilo_subtitulo = ParagraphStyle(
                'CustomSubtitle',
                parent=estilos['Normal'],
                fontSize=7,
                textColor=colors.black,
                alignment=TA_CENTER,
                spaceAfter=3,
                leading=9,
            )

            estilo_normal = ParagraphStyle(
                'Normal80mm',
                parent=estilos['Normal'],
                fontSize=7,
                wordWrap='CJK',
                leading=9,
            )
        else:
            # Estilos para A4
            estilo_titulo = ParagraphStyle(
                'CustomTitle',
                parent=estilos['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#2E7D32'),
                spaceAfter=30,
                alignment=TA_CENTER,
            )

            estilo_subtitulo = ParagraphStyle(
                'CustomSubtitle',
                parent=estilos['Normal'],
                fontSize=12,
                textColor=colors.grey,
                alignment=TA_CENTER,
                spaceAfter=20,
            )

            estilo_normal = estilos['Normal']
        
        # ============================================
        # ENCABEZADO
        # ============================================
        
        # Logo (opcional - si tienes un logo)
        # elementos.append(Image("logo.png", width=2*inch, height=1*inch))
        # elementos.append(Spacer(1, 0.2*inch))
        
        # Título
        elementos.append(Paragraph("LA MILAGROSA", estilo_titulo))
        if tipo_papel != '80mm':
            elementos.append(Paragraph("Sistema de Gestión de Ventas", estilo_subtitulo))

        # Tipo de comprobante
        tipo_comprobante = "VENTA FIADA" if venta.es_fiado else "VENTA"
        elementos.append(Paragraph(
            f"<b>{tipo_comprobante}</b>",
            estilo_subtitulo
        ))
        elementos.append(Spacer(1, 2*mm if tipo_papel == '80mm' else 0.3*inch))
        
        # ============================================
        # INFORMACIÓN DE LA VENTA
        # ============================================
        
        info_data = [
            ["Nº Venta:", f"#{venta.id}"],
            ["Fecha:", venta.fecha.strftime("%d/%m/%Y %H:%M")],
        ]

        if venta.cliente_nombre:
            info_data.append(["Cliente:", venta.cliente_nombre])

        if venta.usuario_nombre:
            info_data.append(["Vendedor:", venta.usuario_nombre])

        if tipo_papel == '80mm':
            col_widths = [18*mm, 56*mm]
            font_size = 7
            padding = 2
        else:
            col_widths = [2*inch, 4*inch]
            font_size = 11
            padding = 8

        info_table = Table(info_data, colWidths=col_widths)
        info_table.setStyle(TableStyle([
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONT', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), font_size),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), padding),
            ('TOPPADDING', (0, 0), (-1, -1), 1 if tipo_papel == '80mm' else padding),
        ]))

        elementos.append(info_table)
        elementos.append(Spacer(1, 2*mm if tipo_papel == '80mm' else 0.4*inch))
        
        # ============================================
        # DETALLE DE PRODUCTOS
        # ============================================
        
        elementos.append(Paragraph("<b>DETALLE DE PRODUCTOS</b>", estilo_normal))
        elementos.append(Spacer(1, 2*mm if tipo_papel == '80mm' else 0.2*inch))

        # Encabezados de tabla
        if tipo_papel == '80mm':
            # Para ticket 80mm: formato compacto para térmica
            productos_data = [['Producto', 'Cant', 'Total']]
            for item in venta.productos:
                productos_data.append([
                    item['nombre'],
                    str(item['cantidad']),
                    f"${item['subtotal']:.2f}"
                ])
            prod_col_widths = [46*mm, 12*mm, 16*mm]
            header_font = 7
            content_font = 7
            header_pad = 2
            content_pad = 2
        else:
            # Para A4: formato completo
            productos_data = [['Producto', 'Precio Unit.', 'Cantidad', 'Subtotal']]
            for item in venta.productos:
                productos_data.append([
                    item['nombre'],
                    f"${item['precio_unitario']:.2f}",
                    str(item['cantidad']),
                    f"${item['subtotal']:.2f}"
                ])
            prod_col_widths = [3.5*inch, 1.2*inch, 1*inch, 1.3*inch]
            header_font = 11
            content_font = 10
            header_pad = 12
            content_pad = 8

        productos_table = Table(productos_data, colWidths=prod_col_widths)

        if tipo_papel == '80mm':
            # Estilo simplificado para impresoras térmicas (sin colores de fondo)
            productos_table.setStyle(TableStyle([
                # Encabezado
                ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), header_font),
                ('BOTTOMPADDING', (0, 0), (-1, 0), header_pad),
                ('TOPPADDING', (0, 0), (-1, 0), header_pad),
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),

                # Contenido
                ('FONT', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), content_font),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 1), (-1, -1), content_pad),
                ('TOPPADDING', (0, 1), (-1, -1), content_pad),

                # Línea simple de separación
                ('LINEBELOW', (0, 1), (-1, -1), 0.5, colors.black),
            ]))
        else:
            # Estilo completo para A4
            productos_table.setStyle(TableStyle([
                # Encabezado
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), header_font),
                ('BOTTOMPADDING', (0, 0), (-1, 0), header_pad),
                ('TOPPADDING', (0, 0), (-1, 0), header_pad),

                # Contenido
                ('FONT', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), content_font),
                ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 1), (-1, -1), content_pad),
                ('TOPPADDING', (0, 1), (-1, -1), content_pad),

                # Bordes
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#2E7D32')),

                # Alternar colores de filas
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
            ]))

        elementos.append(productos_table)
        elementos.append(Spacer(1, 2*mm if tipo_papel == '80mm' else 0.3*inch))

        # ============================================
        # TOTALES
        # ============================================

        totales_data = [
            ['', 'TOTAL:', f"${venta.total:.2f}"],
        ]

        if venta.es_fiado:
            totales_data.extend([
                ['', 'Abonado:', f"${venta.abonado:.2f}"],
                ['', 'RESTA:', f"${venta.resto:.2f}"],
            ])

        if tipo_papel == '80mm':
            total_col_widths = [46*mm, 12*mm, 16*mm]
            total_font = 8
            total_pad = 2
        else:
            total_col_widths = [3.5*inch, 1.5*inch, 2*inch]
            total_font = 12
            total_pad = 8

        totales_table = Table(totales_data, colWidths=total_col_widths)

        if tipo_papel == '80mm':
            # Estilo simplificado para térmica
            totales_table.setStyle(TableStyle([
                ('FONT', (1, 0), (1, -1), 'Helvetica-Bold'),
                ('FONT', (2, 0), (2, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (1, 0), (2, -1), total_font),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('TEXTCOLOR', (1, 0), (2, -1), colors.black),
                ('BOTTOMPADDING', (1, 0), (2, -1), total_pad),
                ('TOPPADDING', (1, 0), (2, -1), total_pad),
                ('LINEABOVE', (1, 0), (2, 0), 1.5, colors.black),
            ]))
        else:
            totales_table.setStyle(TableStyle([
                ('FONT', (1, 0), (1, -1), 'Helvetica-Bold'),
                ('FONT', (2, 0), (2, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (1, 0), (2, -1), total_font),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#2E7D32')),
                ('BOTTOMPADDING', (1, 0), (2, -1), total_pad),
            ]))

        elementos.append(totales_table)
        
        # Si es fiado, agregar nota
        if venta.es_fiado:
            elementos.append(Spacer(1, 2*mm if tipo_papel == '80mm' else 0.4*inch))
            if tipo_papel == '80mm':
                # Nota simplificada para térmica
                nota_estilo = ParagraphStyle(
                    'Nota',
                    parent=estilos['Normal'],
                    fontSize=7,
                    textColor=colors.black,
                    alignment=TA_CENTER,
                    borderWidth=1,
                    borderPadding=3,
                    borderColor=colors.black,
                    leading=9,
                )
                elementos.append(Paragraph(
                    f"<b>FIADO - RESTA: ${venta.resto:.2f}</b>",
                    nota_estilo
                ))
            else:
                nota_estilo = ParagraphStyle(
                    'Nota',
                    parent=estilos['Normal'],
                    fontSize=10,
                    textColor=colors.HexColor('#D32F2F'),
                    alignment=TA_CENTER,
                    borderColor=colors.HexColor('#D32F2F'),
                    borderWidth=1,
                    borderPadding=10,
                )
                elementos.append(Paragraph(
                    "<b>IMPORTANTE:</b> Esta es una venta fiada. "
                    f"El saldo pendiente de ${venta.resto:.2f} debe ser abonado.",
                    nota_estilo
                ))

        # ============================================
        # PIE DE PÁGINA
        # ============================================
        elementos.append(Spacer(1, 2*mm if tipo_papel == '80mm' else 0.5*inch))
        pie_estilo = ParagraphStyle(
            'Pie',
            parent=estilos['Normal'],
            fontSize=6 if tipo_papel == '80mm' else 9,
            textColor=colors.black if tipo_papel == '80mm' else colors.grey,
            alignment=TA_CENTER,
            leading=8 if tipo_papel == '80mm' else 12,
        )
        elementos.append(Paragraph(
            "Gracias por su compra",
            pie_estilo
        ))
        if tipo_papel != '80mm':
            elementos.append(Paragraph(
                f"Comprobante generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}",
                pie_estilo
            ))
        
        # Construir PDF
        doc.build(elementos)
        
        return ruta_salida
    
    @staticmethod
    def generar_comprobante_liquidacion(cliente, abono, nuevo_saldo, ventas_pagadas=None, ruta_salida=None, tipo_papel='80mm'):
        """
        Genera un PDF con el comprobante de liquidación de deuda

        Args:
            cliente: Objeto Cliente
            abono: Monto abonado
            nuevo_saldo: Saldo restante después del abono
            ventas_pagadas: Lista de ventas pagadas/abonadas (opcional)
            ruta_salida: Ruta donde guardar el PDF (opcional)
            tipo_papel: '80mm' o 'A4' (por defecto '80mm')

        Returns:
            str: Ruta del archivo PDF generado
        """

        if not ruta_salida:
            # Crear archivo temporal
            temp_file = tempfile.NamedTemporaryFile(
                mode='w+b',
                suffix='.pdf',
                prefix=f'liquidacion_{cliente.id}_',
                delete=False
            )
            ruta_salida = temp_file.name
            temp_file.close()

        # Seleccionar tamaño de papel
        pagesize = TICKET_80MM if tipo_papel == '80mm' else A4

        doc = SimpleDocTemplate(
            ruta_salida,
            pagesize=pagesize,
            leftMargin=3*mm if tipo_papel == '80mm' else 0.75*inch,
            rightMargin=3*mm if tipo_papel == '80mm' else 0.75*inch,
            topMargin=3*mm if tipo_papel == '80mm' else 0.75*inch,
            bottomMargin=3*mm if tipo_papel == '80mm' else 0.75*inch,
        )
        elementos = []
        
        estilos = getSampleStyleSheet()

        if tipo_papel == '80mm':
            # Estilos optimizados para impresora térmica
            estilo_titulo = ParagraphStyle(
                'CustomTitle',
                parent=estilos['Heading1'],
                fontSize=12,
                textColor=colors.black,
                spaceAfter=4,
                alignment=TA_CENTER,
                wordWrap='CJK',
                leading=14,
            )

            estilo_subtitulo = ParagraphStyle(
                'CustomSubtitle',
                parent=estilos['Normal'],
                fontSize=7,
                textColor=colors.black,
                alignment=TA_CENTER,
                spaceAfter=3,
                leading=9,
            )

            estilo_normal = ParagraphStyle(
                'Normal80mm',
                parent=estilos['Normal'],
                fontSize=7,
                wordWrap='CJK',
                leading=9,
            )
        else:
            estilo_titulo = ParagraphStyle(
                'CustomTitle',
                parent=estilos['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1976D2'),
                spaceAfter=30,
                alignment=TA_CENTER,
            )

            estilo_subtitulo = ParagraphStyle(
                'CustomSubtitle',
                parent=estilos['Normal'],
                fontSize=12,
                textColor=colors.grey,
                alignment=TA_CENTER,
                spaceAfter=20,
            )

            estilo_normal = estilos['Normal']
        
        # Encabezado
        elementos.append(Paragraph("LA MILAGROSA", estilo_titulo))
        if tipo_papel != '80mm':
            elementos.append(Paragraph("Sistema de Gestión de Ventas", estilo_subtitulo))
        elementos.append(Paragraph("<b>COMPROBANTE DE PAGO</b>", estilo_subtitulo))
        elementos.append(Spacer(1, 2*mm if tipo_papel == '80mm' else 0.5*inch))

        # Información del pago
        info_data = [
            ["Fecha:", datetime.now().strftime("%d/%m/%Y %H:%M")],
            ["Cliente:", cliente.nombre],
            ["", ""],
            ["Saldo Anterior:", f"${cliente.deuda_total:.2f}"],
            ["Abono:", f"${abono:.2f}"],
            ["Nuevo Saldo:", f"${nuevo_saldo:.2f}"],
        ]

        if tipo_papel == '80mm':
            info_col_widths = [22*mm, 52*mm]
            info_font = 7
            info_pad = 2
            nuevo_saldo_font = 9
        else:
            info_col_widths = [2.5*inch, 3.5*inch]
            info_font = 12
            info_pad = 10
            nuevo_saldo_font = 14

        info_table = Table(info_data, colWidths=info_col_widths)

        if tipo_papel == '80mm':
            # Estilo simplificado para térmica
            info_table.setStyle(TableStyle([
                ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONT', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), info_font),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), info_pad),
                ('TOPPADDING', (0, 0), (-1, -1), 1),

                # Resaltar nuevo saldo
                ('FONT', (0, 5), (1, 5), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 5), (1, 5), nuevo_saldo_font),
                ('TEXTCOLOR', (1, 5), (1, 5), colors.black),
                ('LINEABOVE', (0, 5), (1, 5), 1.5, colors.black),
            ]))
        else:
            info_table.setStyle(TableStyle([
                ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONT', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), info_font),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#424242')),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), info_pad),

                # Resaltar nuevo saldo
                ('FONT', (0, 5), (1, 5), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 5), (1, 5), nuevo_saldo_font),
                ('TEXTCOLOR', (1, 5), (1, 5), colors.HexColor('#2E7D32') if nuevo_saldo == 0 else colors.HexColor('#D32F2F')),
                ('BACKGROUND', (0, 5), (1, 5), colors.HexColor('#F5F5F5')),
            ]))

        elementos.append(info_table)
        elementos.append(Spacer(1, 2*mm if tipo_papel == '80mm' else 0.5*inch))

        # ============================================
        # DETALLE DE VENTAS PAGADAS (NUEVO)
        # ============================================
        if ventas_pagadas and len(ventas_pagadas) > 0:
            elementos.append(Paragraph("<b>DETALLE DE VENTAS ABONADAS</b>", estilo_normal))
            elementos.append(Spacer(1, 2*mm if tipo_papel == '80mm' else 0.2*inch))

            for venta_info in ventas_pagadas:
                venta = venta_info['venta']
                monto_abonado = venta_info['monto']

                # Información de la venta
                venta_data = [
                    [f"Venta #{venta.id}", f"${monto_abonado:.2f}"],
                    [f"Fecha: {venta.fecha.strftime('%d/%m/%Y')}", ""],
                ]

                if tipo_papel == '80mm':
                    venta_col_widths = [50*mm, 24*mm]
                    venta_font = 7
                else:
                    venta_col_widths = [4*inch, 2*inch]
                    venta_font = 9

                venta_table = Table(venta_data, colWidths=venta_col_widths)
                venta_table.setStyle(TableStyle([
                    ('FONT', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), venta_font),
                    ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                    ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#1976D2')),
                    ('FONT', (0, 0), (0, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ]))

                elementos.append(venta_table)

                # Productos de esta venta
                if tipo_papel == '80mm':
                    # Formato compacto para 80mm
                    for item in venta.productos:
                        prod_text = f"  • {item['nombre']} x{item['cantidad']}"
                        elementos.append(Paragraph(prod_text, estilo_normal))
                else:
                    # Formato tabla para A4
                    productos_data = [["Producto", "Cant", "Precio"]]
                    for item in venta.productos:
                        productos_data.append([
                            item['nombre'],
                            str(item['cantidad']),
                            f"${item['subtotal']:.2f}"
                        ])

                    prod_table = Table(productos_data, colWidths=[3*inch, 0.8*inch, 1*inch])
                    prod_table.setStyle(TableStyle([
                        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ]))
                    elementos.append(prod_table)

                elementos.append(Spacer(1, 2*mm if tipo_papel == '80mm' else 0.15*inch))

            elementos.append(Spacer(1, 2*mm if tipo_papel == '80mm' else 0.3*inch))
        
        # Mensaje según si quedó saldo
        if nuevo_saldo == 0:
            if tipo_papel == '80mm':
                mensaje_estilo = ParagraphStyle(
                    'Mensaje',
                    parent=estilos['Normal'],
                    fontSize=8,
                    textColor=colors.black,
                    alignment=TA_CENTER,
                    borderColor=colors.black,
                    borderWidth=1,
                    borderPadding=3,
                    leading=10,
                )
                elementos.append(Paragraph(
                    "<b>DEUDA LIQUIDADA</b>",
                    mensaje_estilo
                ))
            else:
                mensaje_estilo = ParagraphStyle(
                    'Mensaje',
                    parent=estilos['Normal'],
                    fontSize=14,
                    textColor=colors.HexColor('#2E7D32'),
                    alignment=TA_CENTER,
                    borderColor=colors.HexColor('#2E7D32'),
                    borderWidth=2,
                    borderPadding=15,
                )
                elementos.append(Paragraph(
                    "<b>✓ DEUDA LIQUIDADA COMPLETAMENTE</b>",
                    mensaje_estilo
                ))
        else:
            if tipo_papel == '80mm':
                mensaje_estilo = ParagraphStyle(
                    'Mensaje',
                    parent=estilos['Normal'],
                    fontSize=7,
                    textColor=colors.black,
                    alignment=TA_CENTER,
                    borderColor=colors.black,
                    borderWidth=1,
                    borderPadding=3,
                    leading=9,
                )
                elementos.append(Paragraph(
                    f"<b>Saldo: ${nuevo_saldo:.2f}</b>",
                    mensaje_estilo
                ))
            else:
                mensaje_estilo = ParagraphStyle(
                    'Mensaje',
                    parent=estilos['Normal'],
                    fontSize=12,
                    textColor=colors.HexColor('#D32F2F'),
                    alignment=TA_CENTER,
                    borderColor=colors.HexColor('#D32F2F'),
                    borderWidth=1,
                    borderPadding=10,
                )
                elementos.append(Paragraph(
                    f"<b>Saldo pendiente: ${nuevo_saldo:.2f}</b>",
                    mensaje_estilo
                ))

        # Pie de página
        elementos.append(Spacer(1, 2*mm if tipo_papel == '80mm' else 1*inch))
        pie_estilo = ParagraphStyle(
            'Pie',
            parent=estilos['Normal'],
            fontSize=6 if tipo_papel == '80mm' else 9,
            textColor=colors.black if tipo_papel == '80mm' else colors.grey,
            alignment=TA_CENTER,
            leading=8 if tipo_papel == '80mm' else 12,
        )
        elementos.append(Paragraph(
            "Gracias por su pago",
            pie_estilo
        ))
        
        doc.build(elementos)
        
        return ruta_salida
    
    @staticmethod
    def abrir_pdf(ruta_pdf):
        """
        Abre el PDF con el visor predeterminado del sistema
        
        Args:
            ruta_pdf: Ruta del archivo PDF
        """
        import subprocess
        import platform
        
        sistema = platform.system()
        
        try:
            if sistema == 'Windows':
                os.startfile(ruta_pdf)
            elif sistema == 'Darwin':  # macOS
                subprocess.call(['open', ruta_pdf])
            else:  # Linux
                subprocess.call(['xdg-open', ruta_pdf])
        except Exception as e:
            print(f"Error al abrir PDF: {e}")
    
    @staticmethod
    def imprimir_pdf(ruta_pdf, nombre_impresora=None, eliminar_despues=True):
        """
        Envía el PDF directo a la impresora sin abrirlo

        Args:
            ruta_pdf: Ruta del archivo PDF
            nombre_impresora: Nombre de la impresora (None = impresora predeterminada)
            eliminar_despues: Si True, elimina el archivo temporal después de imprimir

        Returns:
            bool: True si se envió correctamente
        """
        import platform
        import subprocess
        import time

        sistema = platform.system()

        try:
            if sistema == 'Windows':
                # Método 1: Intentar con SumatraPDF (más confiable y silencioso)
                # Obtener ruta relativa al proyecto (funciona tanto en dev como empaquetado)
                import sys

                if getattr(sys, 'frozen', False):
                    # Si está empaquetado con flet pack/PyInstaller
                    script_dir = os.path.dirname(sys.executable)
                else:
                    # Si está en modo desarrollo
                    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

                sumatra_local = os.path.join(script_dir, "Sumatra", "SumatraPDF-3.5.2-64.exe")

                sumatra_paths = [
                    sumatra_local,  # Buscar primero en la carpeta del proyecto
                    r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
                    r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe",
                ]

                sumatra_found = False
                for sumatra_path in sumatra_paths:
                    if os.path.exists(sumatra_path):
                        try:
                            if not nombre_impresora:
                                # Obtener impresora predeterminada
                                try:
                                    import win32print
                                    nombre_impresora = win32print.GetDefaultPrinter()
                                except ImportError:
                                    # Si no hay win32print, SumatraPDF usará la predeterminada
                                    nombre_impresora = None

                            if nombre_impresora:
                                cmd = [sumatra_path, "-print-to", nombre_impresora, ruta_pdf]
                            else:
                                cmd = [sumatra_path, "-print-to-default", ruta_pdf]

                            # Ejecutar SumatraPDF en modo silencioso
                            subprocess.run(
                                cmd,
                                creationflags=subprocess.CREATE_NO_WINDOW,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                                check=True
                            )
                            sumatra_found = True
                            print("PDF enviado a impresora usando SumatraPDF")
                            break
                        except Exception as e_sumatra:
                            print(f"SumatraPDF falló: {e_sumatra}")
                            continue

                # Si no encontró SumatraPDF, usar método alternativo con GhostScript o PowerShell
                if not sumatra_found:
                    # Método 2: Intentar con GhostScript (gs)
                    gs_paths = [
                        r"C:\Program Files\gs\gs10.03.1\bin\gswin64c.exe",
                        r"C:\Program Files\gs\gs10.03.0\bin\gswin64c.exe",
                        r"C:\Program Files (x86)\gs\gs10.03.1\bin\gswin32c.exe",
                        r"C:\Program Files (x86)\gs\gs10.03.0\bin\gswin32c.exe",
                    ]

                    gs_found = False
                    for gs_path in gs_paths:
                        if os.path.exists(gs_path):
                            try:
                                # Obtener nombre de impresora
                                if not nombre_impresora:
                                    try:
                                        import win32print
                                        nombre_impresora = win32print.GetDefaultPrinter()
                                    except ImportError:
                                        nombre_impresora = "default"

                                # Comando GhostScript para imprimir directamente
                                cmd = [
                                    gs_path,
                                    "-dPrinted",
                                    "-dBATCH",
                                    "-dNOPAUSE",
                                    "-dNOSAFER",
                                    "-dNumCopies=1",
                                    "-sDEVICE=mswinpr2",
                                    f"-sOutputFile=%printer%{nombre_impresora}",
                                    ruta_pdf
                                ]

                                subprocess.run(
                                    cmd,
                                    creationflags=subprocess.CREATE_NO_WINDOW,
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL,
                                    check=True
                                )
                                gs_found = True
                                print("PDF enviado a impresora usando GhostScript")
                                break
                            except Exception as e_gs:
                                print(f"GhostScript falló: {e_gs}")
                                continue

                    if not gs_found:
                        # Método 3: Usar PowerShell con Adobe Reader parameters
                        print("Usando PowerShell para imprimir (puede abrir ventana brevemente)...")

                        # Obtener impresora predeterminada
                        if not nombre_impresora:
                            try:
                                import win32print
                                nombre_impresora = win32print.GetDefaultPrinter()
                            except ImportError:
                                nombre_impresora = None

                        # Usar el verbo "print" que debería funcionar con cualquier visor PDF
                        if nombre_impresora:
                            # Intentar con parámetro /t de Adobe Reader
                            cmd = [
                                'cmd', '/c', 'start', '/min', '',
                                ruta_pdf,
                                '/t', nombre_impresora
                            ]
                        else:
                            # Imprimir a predeterminada
                            cmd = ['cmd', '/c', 'start', '/min', '', ruta_pdf, '/p']

                        subprocess.run(
                            cmd,
                            creationflags=subprocess.CREATE_NO_WINDOW,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        print("PDF enviado usando comando del sistema")

            elif sistema == 'Darwin':  # macOS
                if nombre_impresora:
                    subprocess.run(['lpr', '-P', nombre_impresora, ruta_pdf], check=True)
                else:
                    subprocess.run(['lpr', ruta_pdf], check=True)

            else:  # Linux
                if nombre_impresora:
                    subprocess.run(['lp', '-d', nombre_impresora, ruta_pdf], check=True)
                else:
                    subprocess.run(['lp', ruta_pdf], check=True)

            # Eliminar archivo temporal si se solicita
            if eliminar_despues:
                try:
                    # Esperar un momento para que termine de enviar a la cola de impresión
                    time.sleep(3)
                    os.remove(ruta_pdf)
                except Exception as e_del:
                    print(f"No se pudo eliminar archivo temporal: {e_del}")

            return True

        except Exception as e:
            print(f"Error al imprimir PDF: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def obtener_impresoras():
        """
        Obtiene la lista de impresoras disponibles en el sistema

        Returns:
            list: Lista de nombres de impresoras
        """
        import platform

        sistema = platform.system()
        impresoras = []

        try:
            if sistema == 'Windows':
                try:
                    # Usar win32print para obtener impresoras
                    import win32print
                    # Enumerar todas las impresoras
                    impresoras = [printer[2] for printer in win32print.EnumPrinters(2)]
                except ImportError:
                    # Fallback a PowerShell si no está win32print
                    import subprocess
                    resultado = subprocess.run([
                        'powershell', '-Command',
                        'Get-Printer | Select-Object -ExpandProperty Name'
                    ], capture_output=True, text=True, check=True)
                    impresoras = [imp.strip() for imp in resultado.stdout.split('\n') if imp.strip()]

            elif sistema == 'Darwin':  # macOS
                import subprocess
                resultado = subprocess.run(['lpstat', '-p'], capture_output=True, text=True)
                for linea in resultado.stdout.split('\n'):
                    if linea.startswith('printer'):
                        impresoras.append(linea.split()[1])

            else:  # Linux
                import subprocess
                resultado = subprocess.run(['lpstat', '-p'], capture_output=True, text=True)
                for linea in resultado.stdout.split('\n'):
                    if linea.startswith('printer'):
                        impresoras.append(linea.split()[1])

        except Exception as e:
            print(f"Error al obtener impresoras: {e}")

        return impresoras

    # ============================================
    # FUNCIONES PARA WEB
    # ============================================

    @staticmethod
    def generar_comprobante_venta_bytes(venta, tipo_papel='A4'):
        """
        Genera un PDF en memoria (bytes) para uso en web

        Args:
            venta: Objeto Venta con todos los datos
            tipo_papel: 'A4' (recomendado para web)

        Returns:
            bytes: Contenido del PDF en bytes
        """
        buffer = io.BytesIO()

        # Seleccionar tamaño de papel
        pagesize = TICKET_80MM if tipo_papel == '80mm' else A4

        # Crear documento PDF en memoria
        doc = SimpleDocTemplate(
            buffer,
            pagesize=pagesize,
            leftMargin=3*mm if tipo_papel == '80mm' else 0.75*inch,
            rightMargin=3*mm if tipo_papel == '80mm' else 0.75*inch,
            topMargin=3*mm if tipo_papel == '80mm' else 0.75*inch,
            bottomMargin=3*mm if tipo_papel == '80mm' else 0.75*inch,
        )

        elementos = PDFGenerator._crear_elementos_venta(venta, tipo_papel)
        doc.build(elementos)

        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def generar_comprobante_liquidacion_bytes(cliente, abono, nuevo_saldo, ventas_pagadas=None, tipo_papel='A4'):
        """
        Genera un PDF de liquidación en memoria (bytes) para uso en web

        Args:
            cliente: Objeto Cliente
            abono: Monto abonado
            nuevo_saldo: Saldo restante después del abono
            ventas_pagadas: Lista de ventas pagadas/abonadas (opcional)
            tipo_papel: 'A4' (recomendado para web)

        Returns:
            bytes: Contenido del PDF en bytes
        """
        buffer = io.BytesIO()

        # Seleccionar tamaño de papel
        pagesize = TICKET_80MM if tipo_papel == '80mm' else A4

        doc = SimpleDocTemplate(
            buffer,
            pagesize=pagesize,
            leftMargin=3*mm if tipo_papel == '80mm' else 0.75*inch,
            rightMargin=3*mm if tipo_papel == '80mm' else 0.75*inch,
            topMargin=3*mm if tipo_papel == '80mm' else 0.75*inch,
            bottomMargin=3*mm if tipo_papel == '80mm' else 0.75*inch,
        )

        elementos = PDFGenerator._crear_elementos_liquidacion(cliente, abono, nuevo_saldo, ventas_pagadas, tipo_papel)
        doc.build(elementos)

        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def _get_temp_pdf_dir():
        """Obtiene o crea el directorio temporal para PDFs"""
        # Usar directorio assets dentro del proyecto para que Flet lo sirva
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        temp_dir = os.path.join(script_dir, "assets", "temp_pdfs")
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir

    @staticmethod
    def _limpiar_pdfs_antiguos():
        """Limpia PDFs temporales con más de 10 minutos"""
        import time
        temp_dir = PDFGenerator._get_temp_pdf_dir()
        ahora = time.time()
        for archivo in os.listdir(temp_dir):
            ruta = os.path.join(temp_dir, archivo)
            if os.path.isfile(ruta) and archivo.endswith('.pdf'):
                edad = ahora - os.path.getmtime(ruta)
                if edad > 600:  # 10 minutos
                    try:
                        os.remove(ruta)
                    except:
                        pass

    # Servidor HTTP para servir PDFs (singleton)
    _pdf_server = None
    _pdf_server_port = None

    @staticmethod
    def _iniciar_servidor_pdf():
        """Inicia un servidor HTTP simple para servir los PDFs"""
        import http.server
        import socketserver
        import threading

        if PDFGenerator._pdf_server is not None:
            return PDFGenerator._pdf_server_port

        temp_dir = PDFGenerator._get_temp_pdf_dir()

        class PDFHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=temp_dir, **kwargs)

            def end_headers(self):
                # Permitir CORS para que el navegador pueda acceder
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Disposition', 'inline')
                super().end_headers()

            def log_message(self, format, *args):
                pass  # Silenciar logs

        # Buscar puerto disponible
        for port in range(8600, 8700):
            try:
                server = socketserver.TCPServer(("", port), PDFHandler)
                PDFGenerator._pdf_server = server
                PDFGenerator._pdf_server_port = port

                # Iniciar en hilo separado
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                print(f"Servidor PDF iniciado en puerto {port}")
                return port
            except OSError:
                continue

        return None

    @staticmethod
    def abrir_pdf_en_navegador(page, pdf_bytes: bytes, nombre_archivo: str = "comprobante.pdf"):
        """
        En web: guarda el PDF y lo sirve via HTTP local
        En desktop: abre el PDF directamente

        Args:
            page: Objeto page de Flet
            pdf_bytes: Contenido del PDF en bytes
            nombre_archivo: Nombre del archivo
        """
        import flet as ft
        import uuid

        # Limpiar PDFs antiguos
        PDFGenerator._limpiar_pdfs_antiguos()

        # Generar nombre único para el archivo
        unique_id = str(uuid.uuid4())[:8]
        archivo_temp = f"{unique_id}_{nombre_archivo}"

        # Guardar PDF en directorio temporal
        temp_dir = PDFGenerator._get_temp_pdf_dir()
        ruta_pdf = os.path.join(temp_dir, archivo_temp)

        with open(ruta_pdf, 'wb') as f:
            f.write(pdf_bytes)

        # Detectar si es web
        es_web = getattr(page, 'web', False)

        if not es_web:
            # En desktop: abrir directamente con el visor de PDF del sistema
            PDFGenerator.abrir_pdf(ruta_pdf)
            return

        # En WEB: Iniciar servidor HTTP y servir el PDF
        port = PDFGenerator._iniciar_servidor_pdf()

        if port:
            pdf_url = f"http://localhost:{port}/{archivo_temp}"
        else:
            pdf_url = None

        def cerrar_modal(e):
            modal.open = False
            page.update()

        def abrir_pdf(e):
            if pdf_url:
                page.launch_url(pdf_url)

        # Crear el modal
        modal = ft.AlertDialog(
            modal=True,
            bgcolor=ft.Colors.WHITE,
            title=ft.Row([
                ft.Icon(ft.Icons.PICTURE_AS_PDF, color=ft.Colors.RED_400),
                ft.Text("Comprobante Generado", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
            ]),
            content=ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_500, size=50),
                    ft.Container(height=10),
                    ft.Text(
                        "El comprobante se ha generado exitosamente.",
                        size=14,
                        color=ft.Colors.GREY_700,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=15),
                    ft.ElevatedButton(
                        "Abrir PDF",
                        icon=ft.Icons.OPEN_IN_NEW,
                        bgcolor=ft.Colors.BLUE_600,
                        color=ft.Colors.WHITE,
                        width=200,
                        on_click=abrir_pdf,
                        disabled=pdf_url is None,
                    ),
                    ft.Container(height=10),
                    ft.Text(
                        "Se abrirá en una nueva pestaña del navegador",
                        size=11,
                        color=ft.Colors.GREY_500,
                        italic=True,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                width=350,
                padding=20,
            ),
            actions=[
                ft.TextButton("Cerrar", on_click=cerrar_modal),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(modal)
        modal.open = True
        page.update()

    @staticmethod
    def descargar_pdf(page, pdf_bytes: bytes, nombre_archivo: str = "comprobante.pdf"):
        """
        Guarda y abre el PDF para descarga

        Args:
            page: Objeto page de Flet
            pdf_bytes: Contenido del PDF en bytes
            nombre_archivo: Nombre del archivo para descargar
        """
        PDFGenerator.abrir_pdf_en_navegador(page, pdf_bytes, nombre_archivo)

    @staticmethod
    def _crear_elementos_venta(venta, tipo_papel):
        """Helper: Crea los elementos del PDF de venta (reutilizable)"""
        elementos = []
        estilos = getSampleStyleSheet()

        if tipo_papel == '80mm':
            estilo_titulo = ParagraphStyle(
                'CustomTitle',
                parent=estilos['Heading1'],
                fontSize=12,
                textColor=colors.black,
                spaceAfter=4,
                alignment=TA_CENTER,
                wordWrap='CJK',
                leading=14,
            )
            estilo_subtitulo = ParagraphStyle(
                'CustomSubtitle',
                parent=estilos['Normal'],
                fontSize=7,
                textColor=colors.black,
                alignment=TA_CENTER,
                spaceAfter=3,
                leading=9,
            )
            estilo_normal = ParagraphStyle(
                'Normal80mm',
                parent=estilos['Normal'],
                fontSize=7,
                wordWrap='CJK',
                leading=9,
            )
        else:
            estilo_titulo = ParagraphStyle(
                'CustomTitle',
                parent=estilos['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#2E7D32'),
                spaceAfter=30,
                alignment=TA_CENTER,
            )
            estilo_subtitulo = ParagraphStyle(
                'CustomSubtitle',
                parent=estilos['Normal'],
                fontSize=12,
                textColor=colors.grey,
                alignment=TA_CENTER,
                spaceAfter=20,
            )
            estilo_normal = estilos['Normal']

        # Encabezado
        elementos.append(Paragraph("LA MILAGROSA", estilo_titulo))
        if tipo_papel != '80mm':
            elementos.append(Paragraph("Sistema de Gestión de Ventas", estilo_subtitulo))

        tipo_comprobante = "VENTA FIADA" if venta.es_fiado else "VENTA"
        elementos.append(Paragraph(f"<b>{tipo_comprobante}</b>", estilo_subtitulo))
        elementos.append(Spacer(1, 2*mm if tipo_papel == '80mm' else 0.3*inch))

        # Info de la venta
        info_data = [
            ["Nº Venta:", f"#{venta.id}"],
            ["Fecha:", venta.fecha.strftime("%d/%m/%Y %H:%M")],
        ]
        if venta.cliente_nombre:
            info_data.append(["Cliente:", venta.cliente_nombre])
        if venta.usuario_nombre:
            info_data.append(["Vendedor:", venta.usuario_nombre])

        if tipo_papel == '80mm':
            col_widths = [18*mm, 56*mm]
            font_size = 7
            padding = 2
        else:
            col_widths = [2*inch, 4*inch]
            font_size = 11
            padding = 8

        info_table = Table(info_data, colWidths=col_widths)
        info_table.setStyle(TableStyle([
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONT', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), font_size),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), padding),
            ('TOPPADDING', (0, 0), (-1, -1), 1 if tipo_papel == '80mm' else padding),
        ]))
        elementos.append(info_table)
        elementos.append(Spacer(1, 2*mm if tipo_papel == '80mm' else 0.4*inch))

        # Detalle de productos
        elementos.append(Paragraph("<b>DETALLE DE PRODUCTOS</b>", estilo_normal))
        elementos.append(Spacer(1, 2*mm if tipo_papel == '80mm' else 0.2*inch))

        if tipo_papel == '80mm':
            productos_data = [['Producto', 'Cant', 'Total']]
            for item in venta.productos:
                productos_data.append([
                    item['nombre'],
                    str(item['cantidad']),
                    f"${item['subtotal']:.2f}"
                ])
            prod_col_widths = [46*mm, 12*mm, 16*mm]
            header_font = 7
            content_font = 7
            header_pad = 2
            content_pad = 2
        else:
            productos_data = [['Producto', 'Precio Unit.', 'Cantidad', 'Subtotal']]
            for item in venta.productos:
                productos_data.append([
                    item['nombre'],
                    f"${item['precio_unitario']:.2f}",
                    str(item['cantidad']),
                    f"${item['subtotal']:.2f}"
                ])
            prod_col_widths = [3.5*inch, 1.2*inch, 1*inch, 1.3*inch]
            header_font = 11
            content_font = 10
            header_pad = 12
            content_pad = 8

        productos_table = Table(productos_data, colWidths=prod_col_widths)

        if tipo_papel == '80mm':
            productos_table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), header_font),
                ('BOTTOMPADDING', (0, 0), (-1, 0), header_pad),
                ('TOPPADDING', (0, 0), (-1, 0), header_pad),
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
                ('FONT', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), content_font),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 1), (-1, -1), content_pad),
                ('TOPPADDING', (0, 1), (-1, -1), content_pad),
                ('LINEBELOW', (0, 1), (-1, -1), 0.5, colors.black),
            ]))
        else:
            productos_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), header_font),
                ('BOTTOMPADDING', (0, 0), (-1, 0), header_pad),
                ('TOPPADDING', (0, 0), (-1, 0), header_pad),
                ('FONT', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), content_font),
                ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 1), (-1, -1), content_pad),
                ('TOPPADDING', (0, 1), (-1, -1), content_pad),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#2E7D32')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
            ]))

        elementos.append(productos_table)
        elementos.append(Spacer(1, 2*mm if tipo_papel == '80mm' else 0.3*inch))

        # Totales
        totales_data = [['', 'TOTAL:', f"${venta.total:.2f}"]]
        if venta.es_fiado:
            totales_data.extend([
                ['', 'Abonado:', f"${venta.abonado:.2f}"],
                ['', 'RESTA:', f"${venta.resto:.2f}"],
            ])

        if tipo_papel == '80mm':
            total_col_widths = [46*mm, 12*mm, 16*mm]
            total_font = 8
            total_pad = 2
        else:
            total_col_widths = [3.5*inch, 1.5*inch, 2*inch]
            total_font = 12
            total_pad = 8

        totales_table = Table(totales_data, colWidths=total_col_widths)

        if tipo_papel == '80mm':
            totales_table.setStyle(TableStyle([
                ('FONT', (1, 0), (1, -1), 'Helvetica-Bold'),
                ('FONT', (2, 0), (2, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (1, 0), (2, -1), total_font),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('TEXTCOLOR', (1, 0), (2, -1), colors.black),
                ('BOTTOMPADDING', (1, 0), (2, -1), total_pad),
                ('TOPPADDING', (1, 0), (2, -1), total_pad),
                ('LINEABOVE', (1, 0), (2, 0), 1.5, colors.black),
            ]))
        else:
            totales_table.setStyle(TableStyle([
                ('FONT', (1, 0), (1, -1), 'Helvetica-Bold'),
                ('FONT', (2, 0), (2, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (1, 0), (2, -1), total_font),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#2E7D32')),
                ('BOTTOMPADDING', (1, 0), (2, -1), total_pad),
            ]))

        elementos.append(totales_table)

        # Nota si es fiado
        if venta.es_fiado:
            elementos.append(Spacer(1, 2*mm if tipo_papel == '80mm' else 0.4*inch))
            if tipo_papel == '80mm':
                nota_estilo = ParagraphStyle(
                    'Nota',
                    parent=estilos['Normal'],
                    fontSize=7,
                    textColor=colors.black,
                    alignment=TA_CENTER,
                    borderWidth=1,
                    borderPadding=3,
                    borderColor=colors.black,
                    leading=9,
                )
                elementos.append(Paragraph(f"<b>FIADO - RESTA: ${venta.resto:.2f}</b>", nota_estilo))
            else:
                nota_estilo = ParagraphStyle(
                    'Nota',
                    parent=estilos['Normal'],
                    fontSize=10,
                    textColor=colors.HexColor('#D32F2F'),
                    alignment=TA_CENTER,
                    borderColor=colors.HexColor('#D32F2F'),
                    borderWidth=1,
                    borderPadding=10,
                )
                elementos.append(Paragraph(
                    f"<b>IMPORTANTE:</b> Esta es una venta fiada. El saldo pendiente de ${venta.resto:.2f} debe ser abonado.",
                    nota_estilo
                ))

        # Pie de página
        elementos.append(Spacer(1, 2*mm if tipo_papel == '80mm' else 0.5*inch))
        pie_estilo = ParagraphStyle(
            'Pie',
            parent=estilos['Normal'],
            fontSize=6 if tipo_papel == '80mm' else 9,
            textColor=colors.black if tipo_papel == '80mm' else colors.grey,
            alignment=TA_CENTER,
            leading=8 if tipo_papel == '80mm' else 12,
        )
        elementos.append(Paragraph("Gracias por su compra", pie_estilo))
        if tipo_papel != '80mm':
            elementos.append(Paragraph(
                f"Comprobante generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}",
                pie_estilo
            ))

        return elementos

    @staticmethod
    def _crear_elementos_liquidacion(cliente, abono, nuevo_saldo, ventas_pagadas, tipo_papel):
        """Helper: Crea los elementos del PDF de liquidación (reutilizable)"""
        elementos = []
        estilos = getSampleStyleSheet()

        if tipo_papel == '80mm':
            estilo_titulo = ParagraphStyle(
                'CustomTitle',
                parent=estilos['Heading1'],
                fontSize=12,
                textColor=colors.black,
                spaceAfter=4,
                alignment=TA_CENTER,
                wordWrap='CJK',
                leading=14,
            )
            estilo_subtitulo = ParagraphStyle(
                'CustomSubtitle',
                parent=estilos['Normal'],
                fontSize=7,
                textColor=colors.black,
                alignment=TA_CENTER,
                spaceAfter=3,
                leading=9,
            )
            estilo_normal = ParagraphStyle(
                'Normal80mm',
                parent=estilos['Normal'],
                fontSize=7,
                wordWrap='CJK',
                leading=9,
            )
        else:
            estilo_titulo = ParagraphStyle(
                'CustomTitle',
                parent=estilos['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1976D2'),
                spaceAfter=30,
                alignment=TA_CENTER,
            )
            estilo_subtitulo = ParagraphStyle(
                'CustomSubtitle',
                parent=estilos['Normal'],
                fontSize=12,
                textColor=colors.grey,
                alignment=TA_CENTER,
                spaceAfter=20,
            )
            estilo_normal = estilos['Normal']

        # Encabezado
        elementos.append(Paragraph("LA MILAGROSA", estilo_titulo))
        if tipo_papel != '80mm':
            elementos.append(Paragraph("Sistema de Gestión de Ventas", estilo_subtitulo))
        elementos.append(Paragraph("<b>COMPROBANTE DE PAGO</b>", estilo_subtitulo))
        elementos.append(Spacer(1, 2*mm if tipo_papel == '80mm' else 0.5*inch))

        # Info del pago
        info_data = [
            ["Fecha:", datetime.now().strftime("%d/%m/%Y %H:%M")],
            ["Cliente:", cliente.nombre],
            ["", ""],
            ["Saldo Anterior:", f"${cliente.deuda_total:.2f}"],
            ["Abono:", f"${abono:.2f}"],
            ["Nuevo Saldo:", f"${nuevo_saldo:.2f}"],
        ]

        if tipo_papel == '80mm':
            info_col_widths = [22*mm, 52*mm]
            info_font = 7
            info_pad = 2
            nuevo_saldo_font = 9
        else:
            info_col_widths = [2.5*inch, 3.5*inch]
            info_font = 12
            info_pad = 10
            nuevo_saldo_font = 14

        info_table = Table(info_data, colWidths=info_col_widths)

        if tipo_papel == '80mm':
            info_table.setStyle(TableStyle([
                ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONT', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), info_font),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), info_pad),
                ('TOPPADDING', (0, 0), (-1, -1), 1),
                ('FONT', (0, 5), (1, 5), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 5), (1, 5), nuevo_saldo_font),
                ('TEXTCOLOR', (1, 5), (1, 5), colors.black),
                ('LINEABOVE', (0, 5), (1, 5), 1.5, colors.black),
            ]))
        else:
            info_table.setStyle(TableStyle([
                ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONT', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), info_font),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#424242')),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), info_pad),
                ('FONT', (0, 5), (1, 5), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 5), (1, 5), nuevo_saldo_font),
                ('TEXTCOLOR', (1, 5), (1, 5), colors.HexColor('#2E7D32') if nuevo_saldo == 0 else colors.HexColor('#D32F2F')),
                ('BACKGROUND', (0, 5), (1, 5), colors.HexColor('#F5F5F5')),
            ]))

        elementos.append(info_table)
        elementos.append(Spacer(1, 2*mm if tipo_papel == '80mm' else 0.5*inch))

        # Detalle de ventas pagadas
        if ventas_pagadas and len(ventas_pagadas) > 0:
            elementos.append(Paragraph("<b>DETALLE DE VENTAS ABONADAS</b>", estilo_normal))
            elementos.append(Spacer(1, 2*mm if tipo_papel == '80mm' else 0.2*inch))

            for venta_info in ventas_pagadas:
                venta = venta_info['venta']
                monto_abonado = venta_info['monto']

                venta_data = [
                    [f"Venta #{venta.id}", f"${monto_abonado:.2f}"],
                    [f"Fecha: {venta.fecha.strftime('%d/%m/%Y')}", ""],
                ]

                if tipo_papel == '80mm':
                    venta_col_widths = [50*mm, 24*mm]
                    venta_font = 7
                else:
                    venta_col_widths = [4*inch, 2*inch]
                    venta_font = 9

                venta_table = Table(venta_data, colWidths=venta_col_widths)
                venta_table.setStyle(TableStyle([
                    ('FONT', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), venta_font),
                    ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                    ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#1976D2')),
                    ('FONT', (0, 0), (0, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ]))
                elementos.append(venta_table)

                if tipo_papel == '80mm':
                    for item in venta.productos:
                        prod_text = f"  - {item['nombre']} x{item['cantidad']}"
                        elementos.append(Paragraph(prod_text, estilo_normal))
                else:
                    productos_data = [["Producto", "Cant", "Precio"]]
                    for item in venta.productos:
                        productos_data.append([
                            item['nombre'],
                            str(item['cantidad']),
                            f"${item['subtotal']:.2f}"
                        ])

                    prod_table = Table(productos_data, colWidths=[3*inch, 0.8*inch, 1*inch])
                    prod_table.setStyle(TableStyle([
                        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ]))
                    elementos.append(prod_table)

                elementos.append(Spacer(1, 2*mm if tipo_papel == '80mm' else 0.15*inch))

            elementos.append(Spacer(1, 2*mm if tipo_papel == '80mm' else 0.3*inch))

        # Mensaje según saldo
        if nuevo_saldo == 0:
            if tipo_papel == '80mm':
                mensaje_estilo = ParagraphStyle(
                    'Mensaje',
                    parent=estilos['Normal'],
                    fontSize=8,
                    textColor=colors.black,
                    alignment=TA_CENTER,
                    borderColor=colors.black,
                    borderWidth=1,
                    borderPadding=3,
                    leading=10,
                )
                elementos.append(Paragraph("<b>DEUDA LIQUIDADA</b>", mensaje_estilo))
            else:
                mensaje_estilo = ParagraphStyle(
                    'Mensaje',
                    parent=estilos['Normal'],
                    fontSize=14,
                    textColor=colors.HexColor('#2E7D32'),
                    alignment=TA_CENTER,
                    borderColor=colors.HexColor('#2E7D32'),
                    borderWidth=2,
                    borderPadding=15,
                )
                elementos.append(Paragraph("<b>DEUDA LIQUIDADA COMPLETAMENTE</b>", mensaje_estilo))
        else:
            if tipo_papel == '80mm':
                mensaje_estilo = ParagraphStyle(
                    'Mensaje',
                    parent=estilos['Normal'],
                    fontSize=7,
                    textColor=colors.black,
                    alignment=TA_CENTER,
                    borderColor=colors.black,
                    borderWidth=1,
                    borderPadding=3,
                    leading=9,
                )
                elementos.append(Paragraph(f"<b>Saldo: ${nuevo_saldo:.2f}</b>", mensaje_estilo))
            else:
                mensaje_estilo = ParagraphStyle(
                    'Mensaje',
                    parent=estilos['Normal'],
                    fontSize=12,
                    textColor=colors.HexColor('#D32F2F'),
                    alignment=TA_CENTER,
                    borderColor=colors.HexColor('#D32F2F'),
                    borderWidth=1,
                    borderPadding=10,
                )
                elementos.append(Paragraph(f"<b>Saldo pendiente: ${nuevo_saldo:.2f}</b>", mensaje_estilo))

        # Pie de página
        elementos.append(Spacer(1, 2*mm if tipo_papel == '80mm' else 1*inch))
        pie_estilo = ParagraphStyle(
            'Pie',
            parent=estilos['Normal'],
            fontSize=6 if tipo_papel == '80mm' else 9,
            textColor=colors.black if tipo_papel == '80mm' else colors.grey,
            alignment=TA_CENTER,
            leading=8 if tipo_papel == '80mm' else 12,
        )
        elementos.append(Paragraph("Gracias por su pago", pie_estilo))

        return elementos

    @staticmethod
    def es_web():
        """Detecta si la aplicación está corriendo en modo web"""
        import flet as ft
        try:
            # En web, algunas funciones de sistema no están disponibles
            import platform
            return platform.system() == 'Emscripten' or hasattr(ft, 'WEB_BROWSER')
        except:
            return False

    @staticmethod
    def imprimir_o_mostrar(page, venta=None, cliente=None, abono=None, nuevo_saldo=None, ventas_pagadas=None, tipo='venta'):
        """
        Método unificado: imprime en desktop, muestra en navegador en web

        Args:
            page: Objeto page de Flet
            venta: Objeto Venta (para tipo='venta')
            cliente: Objeto Cliente (para tipo='liquidacion')
            abono: Monto abonado (para tipo='liquidacion')
            nuevo_saldo: Saldo después del abono (para tipo='liquidacion')
            ventas_pagadas: Lista de ventas pagadas (para tipo='liquidacion')
            tipo: 'venta' o 'liquidacion'
        """
        # Detectar si es web basándose en el tipo de plataforma
        es_web = page.web if hasattr(page, 'web') else False

        if es_web:
            # Modo web: generar en memoria y abrir en navegador
            if tipo == 'venta':
                pdf_bytes = PDFGenerator.generar_comprobante_venta_bytes(venta, tipo_papel='A4')
                PDFGenerator.abrir_pdf_en_navegador(page, pdf_bytes, f"venta_{venta.id}.pdf")
            else:
                pdf_bytes = PDFGenerator.generar_comprobante_liquidacion_bytes(
                    cliente, abono, nuevo_saldo, ventas_pagadas, tipo_papel='A4'
                )
                PDFGenerator.abrir_pdf_en_navegador(page, pdf_bytes, f"liquidacion_{cliente.id}.pdf")
        else:
            # Modo desktop: generar archivo e imprimir
            if tipo == 'venta':
                ruta = PDFGenerator.generar_comprobante_venta(venta)
                PDFGenerator.imprimir_pdf(ruta)
            else:
                ruta = PDFGenerator.generar_comprobante_liquidacion(
                    cliente, abono, nuevo_saldo, ventas_pagadas
                )
                PDFGenerator.imprimir_pdf(ruta)