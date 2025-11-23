"""Gestión de conexión a la base de datos"""

import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine, Session
from typing import Generator, TYPE_CHECKING

if TYPE_CHECKING:
    from models.cliente import Cliente
    from models.producto import Producto
    from models.venta import Venta

# Cargar variables de entorno
load_dotenv()

# URL de conexión desde .env
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL no está configurada. "
        "Crea un archivo .env con: DATABASE_URL=postgresql://..."
    )

# Crear engine con pool de conexiones
engine = create_engine(
    DATABASE_URL,
    echo=False,  # True para ver SQL queries en consola (debug)
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verifica conexiones antes de usarlas
)


def create_db_and_tables():
    """Crea todas las tablas definidas en los modelos"""
    from models.cliente import Cliente
    from models.producto import Producto
    from models.venta import Venta
    
    SQLModel.metadata.create_all(engine)
    print("✅ Tablas creadas/verificadas correctamente")


def get_session() -> Generator[Session, None, None]:
    """
    Generador de sesiones de base de datos.
    Uso:
        with get_session() as session:
            # operaciones con session
    """
    with Session(engine) as session:
        yield session


def get_session_context() -> Session:
    """
    Obtiene una sesión directa (para usar fuera de context manager).
    IMPORTANTE: Recuerda cerrar con session.close()
    """
    return Session(engine)


# Función de inicialización
def init_database():
    """Inicializa la base de datos"""
    try:
        print("🔌 Conectando a la base de datos...")
        create_db_and_tables()
        print("✅ Base de datos inicializada correctamente")
        return True
    except Exception as e:
        print(f"❌ Error al inicializar base de datos: {e}")
        return False