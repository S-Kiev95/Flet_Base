"""Modelo de Producto"""

from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class Producto(SQLModel, table=True):
    """Modelo de Producto para el inventario"""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(index=True, max_length=200)
    codigo_barras: Optional[str] = Field(default=None, max_length=100, index=True)
    
    # Precios
    precio_proveedor: float = Field(default=0.0, ge=0)
    precio_venta: float = Field(default=0.0, ge=0)
    
    # Inventario
    cantidad_stock: float = Field(default=0.0, ge=0)  # Float para productos fraccionables
    stock_minimo: float = Field(default=0.0, ge=0)
    unidad_medida: str = Field(default="unidad", max_length=50)  # ej: unidad, kg, litro
    
    # Categoría y organización
    categoria: Optional[str] = Field(default=None, max_length=100)
    proveedor: Optional[str] = Field(default=None, max_length=200)
    
    # Metadata
    descripcion: Optional[str] = Field(default=None, max_length=1000)
    activo: bool = Field(default=True)
    fecha_creacion: datetime = Field(default_factory=datetime.now)
    fecha_actualizacion: Optional[datetime] = Field(default=None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "Coca Cola 2L",
                "codigo_barras": "7790315241234",
                "precio_proveedor": 80.0,
                "precio_venta": 120.0,
                "cantidad_stock": 50,
                "categoria": "Bebidas"
            }
        }
    
    def tiene_stock(self, cantidad: float) -> bool:
        """Verifica si hay stock disponible"""
        return self.cantidad_stock >= cantidad
    
    def esta_bajo_stock(self) -> bool:
        """Verifica si el stock está bajo"""
        return self.cantidad_stock <= self.stock_minimo
    
    def calcular_ganancia(self) -> float:
        """Calcula la ganancia por unidad"""
        return self.precio_venta - self.precio_proveedor
    
    def calcular_margen(self) -> float:
        """Calcula el margen de ganancia en porcentaje"""
        if self.precio_proveedor == 0:
            return 0.0
        return ((self.precio_venta - self.precio_proveedor) / self.precio_proveedor) * 100
    
    def __repr__(self):
        return f"Producto(id={self.id}, nombre={self.nombre}, stock={self.cantidad_stock})"