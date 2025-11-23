"""Modelo de Usuario"""

from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from enum import Enum


class RolUsuario(str, Enum):
    """Roles de usuario en el sistema"""
    SUPERADMIN = "SuperAdmin"
    VENDEDOR = "Vendedor"


class Usuario(SQLModel, table=True):
    """Modelo de Usuario - Gestiona el acceso al sistema"""

    __tablename__ = "usuarios"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Información básica
    nombre: str = Field(max_length=100, index=True)
    rol: str = Field(max_length=20, index=True)  # SuperAdmin o Vendedor
    contraseña: str = Field(max_length=100)  # Texto plano (app interna)

    # Estado
    activo: bool = Field(default=True, index=True)

    # Metadata
    fecha_creacion: datetime = Field(default_factory=datetime.now)
    fecha_actualizacion: Optional[datetime] = Field(default=None)
    ultimo_acceso: Optional[datetime] = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "Juan Pérez",
                "rol": "Vendedor",
                "contraseña": "1234"
            }
        }

    def es_superadmin(self) -> bool:
        """Verifica si el usuario es SuperAdmin"""
        return self.rol == RolUsuario.SUPERADMIN.value

    def puede_gestionar_usuarios(self) -> bool:
        """Verifica si el usuario puede gestionar otros usuarios"""
        return self.es_superadmin()

    def actualizar_ultimo_acceso(self):
        """Actualiza la fecha de último acceso"""
        self.ultimo_acceso = datetime.now()

    def __repr__(self):
        return f"Usuario(id={self.id}, nombre='{self.nombre}', rol='{self.rol}')"
