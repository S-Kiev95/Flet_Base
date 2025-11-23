"""Modelo de Cliente"""

from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class Cliente(SQLModel, table=True):
    """Modelo de Cliente para la tienda"""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(index=True, max_length=200)
    telefono: Optional[str] = Field(default=None, max_length=50)
    direccion: Optional[str] = Field(default=None, max_length=500)
    email: Optional[str] = Field(default=None, max_length=200)
    
    # Información de crédito
    limite_credito: float = Field(default=0.0)  # Límite de crédito permitido
    deuda_total: float = Field(default=0.0)  # Deuda acumulada (puede desincronizarse, usar calcular_deuda_real())
    
    # Metadata
    notas: Optional[str] = Field(default=None, max_length=1000)
    activo: bool = Field(default=True)  # Para "desactivar" clientes sin borrar
    fecha_creacion: datetime = Field(default_factory=datetime.now)
    fecha_actualizacion: Optional[datetime] = Field(default=None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "Juan Pérez",
                "telefono": "099123456",
                "direccion": "Av. 18 de Julio 1234",
                "limite_credito": 5000.0,
                "notas": "Cliente frecuente"
            }
        }
    
    def puede_fiar(self, monto: float) -> bool:
        """Verifica si el cliente puede fiar un monto adicional"""
        return (self.deuda_total + monto) <= self.limite_credito
    
    def tiene_deuda(self) -> bool:
        """Verifica si el cliente tiene deuda pendiente"""
        return self.deuda_total > 0
    
    def __repr__(self):
        return f"Cliente(id={self.id}, nombre={self.nombre}, deuda={self.deuda_total})"