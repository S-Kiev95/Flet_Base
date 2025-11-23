"""Modelo de Abono"""

from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class Abono(SQLModel, table=True):
    """Modelo de Abono - Registra los pagos parciales o totales de una venta fiada"""

    __tablename__ = "abonos"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Relación con la venta
    venta_id: int = Field(foreign_key="ventas.id", index=True)

    # Usuario que realizó el abono
    usuario_id: Optional[int] = Field(default=None, foreign_key="usuarios.id", index=True)
    usuario_nombre: Optional[str] = Field(default=None, max_length=100)

    # Información del abono
    monto: float = Field(ge=0)
    fecha: datetime = Field(default_factory=datetime.now, index=True)

    # Metadata
    notas: Optional[str] = Field(default=None, max_length=500)
    fecha_creacion: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "venta_id": 1,
                "monto": 100.0,
                "notas": "Pago parcial en efectivo"
            }
        }

    def __repr__(self):
        return f"Abono(id={self.id}, venta_id={self.venta_id}, monto=${self.monto}, fecha={self.fecha.strftime('%d/%m/%Y')})"
