"""Modelo de Sesión"""

from typing import Optional
from datetime import datetime, timedelta
from sqlmodel import SQLModel, Field


class Sesion(SQLModel, table=True):
    """Modelo de Sesión - Gestiona las sesiones activas de usuarios"""

    __tablename__ = "sesiones"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Relación con usuario
    usuario_id: int = Field(foreign_key="usuarios.id", index=True)

    # Token de sesión (simple, basado en timestamp)
    token: str = Field(max_length=100, unique=True, index=True)

    # Timestamps
    fecha_inicio: datetime = Field(default_factory=datetime.now)
    fecha_expiracion: datetime = Field(index=True)
    fecha_ultimo_uso: datetime = Field(default_factory=datetime.now)

    # Estado
    activa: bool = Field(default=True, index=True)

    class Config:
        json_schema_extra = {
            "example": {
                "usuario_id": 1,
                "token": "session_123456789",
                "fecha_expiracion": "2024-01-01T20:00:00"
            }
        }

    @staticmethod
    def generar_token(usuario_id: int) -> str:
        """Genera un token único para la sesión"""
        import hashlib
        import time

        data = f"{usuario_id}_{time.time()}_{datetime.now().isoformat()}"
        return hashlib.md5(data.encode()).hexdigest()

    @staticmethod
    def crear_nueva(usuario_id: int, duracion_horas: int = 8) -> "Sesion":
        """Crea una nueva sesión para un usuario"""
        token = Sesion.generar_token(usuario_id)
        fecha_expiracion = datetime.now() + timedelta(hours=duracion_horas)

        return Sesion(
            usuario_id=usuario_id,
            token=token,
            fecha_expiracion=fecha_expiracion
        )

    def es_valida(self) -> bool:
        """Verifica si la sesión es válida (activa y no expirada)"""
        return self.activa and datetime.now() < self.fecha_expiracion

    def renovar(self, duracion_horas: int = 8):
        """Renueva la sesión extendiendo su fecha de expiración"""
        self.fecha_expiracion = datetime.now() + timedelta(hours=duracion_horas)
        self.fecha_ultimo_uso = datetime.now()

    def cerrar(self):
        """Cierra la sesión"""
        self.activa = False

    def __repr__(self):
        return f"Sesion(id={self.id}, usuario_id={self.usuario_id}, token='{self.token[:8]}...', valida={self.es_valida()})"
