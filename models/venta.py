"""Modelo de Venta"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON


class ItemVenta(SQLModel):
    """Modelo para un item dentro de una venta (no es tabla, es para validación)"""
    
    # Producto de la BD (si existe)
    producto_id: Optional[int] = None
    
    # Datos del producto (pueden ser de BD o ingresados manualmente)
    nombre: str
    precio_unitario: float
    cantidad: float
    subtotal: float
    
    # Flag para saber si afecta el stock
    descontar_stock: bool = True  # True si es producto de BD
    
    class Config:
        json_schema_extra = {
            "example": {
                "producto_id": 5,
                "nombre": "Coca Cola 2L",
                "precio_unitario": 120.0,
                "cantidad": 2,
                "subtotal": 240.0,
                "descontar_stock": True
            }
        }


class Venta(SQLModel, table=True):
    """Modelo de Venta - Puede ser al contado o fiada"""
    
    __tablename__ = "ventas"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    fecha: datetime = Field(default_factory=datetime.now, index=True)

    # Usuario que realizó la venta
    usuario_id: Optional[int] = Field(default=None, foreign_key="usuarios.id", index=True)
    usuario_nombre: Optional[str] = Field(default=None, max_length=100)

    # Cliente (opcional - solo si es fiado)
    # SIN foreign_key para evitar problemas de orden de creación
    cliente_id: Optional[int] = Field(default=None, index=True)
    cliente_nombre: Optional[str] = Field(default=None, max_length=200)
    
    # Productos (JSON flexible)
    productos: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSON))
    
    # Montos
    total: float = Field(default=0.0, ge=0)
    
    # Gestión de fiado
    es_fiado: bool = Field(default=False, index=True)
    # NOTA: El campo 'abonado' y 'resto' ahora se calculan dinámicamente desde la tabla de abonos
    # Se mantienen aquí para compatibilidad durante la migración, pero serán calculados
    abonado: float = Field(default=0.0, ge=0)  # Se calculará desde abonos
    resto: float = Field(default=0.0, ge=0)  # Se calculará como total - abonado
    
    # Estado
    pagado_completamente: bool = Field(default=False, index=True)
    fecha_pago_completo: Optional[datetime] = Field(default=None)
    
    # Metadata
    notas: Optional[str] = Field(default=None, max_length=1000)
    metodo_pago: Optional[str] = Field(default=None, max_length=50)
    fecha_creacion: datetime = Field(default_factory=datetime.now)
    fecha_actualizacion: Optional[datetime] = Field(default=None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "cliente_id": 1,
                "productos": [
                    {
                        "producto_id": 5,
                        "nombre": "Coca Cola 2L",
                        "precio_unitario": 120.0,
                        "cantidad": 2,
                        "subtotal": 240.0,
                        "descontar_stock": True
                    }
                ],
                "total": 240.0,
                "es_fiado": True,
                "abonado": 100.0,
                "resto": 140.0
            }
        }
    
    def calcular_totales(self):
        """Calcula el total basado en los productos"""
        self.total = sum(item.get("subtotal", 0) for item in self.productos)
        self.resto = self.total - self.abonado
        self.pagado_completamente = self.resto <= 0
        
        if self.pagado_completamente and not self.fecha_pago_completo:
            self.fecha_pago_completo = datetime.now()
    
    def registrar_abono(self, monto: float):
        """Registra un abono adicional a la venta"""
        self.abonado += monto
        self.calcular_totales()
        self.fecha_actualizacion = datetime.now()
    
    def esta_pendiente(self) -> bool:
        """Verifica si la venta tiene saldo pendiente"""
        return self.es_fiado and not self.pagado_completamente
    
    def get_items_con_stock(self) -> List[Dict[str, Any]]:
        """Obtiene solo los items que deben descontar stock"""
        return [item for item in self.productos if item.get("descontar_stock", False)]
    
    def __repr__(self):
        estado = "PAGADO" if self.pagado_completamente else f"DEBE ${self.resto}"
        return f"Venta(id={self.id}, total=${self.total}, {estado})"