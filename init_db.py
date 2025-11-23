"""
Script para inicializar la base de datos y cargar datos de prueba
Ejecutar con: python init_db.py
"""

from database.connection import init_database, get_session_context
from database.db_service import ClienteRepository, ProductoRepository
from models.cliente import Cliente
from models.producto import Producto


def cargar_datos_prueba():
    """Carga datos de prueba en la base de datos"""
    
    session = get_session_context()
    
    try:
        print("\n📦 Cargando datos de prueba...")
        
        # Crear clientes de prueba
        clientes = [
            Cliente(
                nombre="Juan Pérez",
                telefono="099123456",
                direccion="Av. 18 de Julio 1234",
                limite_credito=10000.0,
                notas="Cliente frecuente"
            ),
            Cliente(
                nombre="María González",
                telefono="098765432",
                direccion="Bulevar Artigas 567",
                limite_credito=5000.0
            ),
            Cliente(
                nombre="Pedro Rodríguez",
                telefono="091234567",
                limite_credito=3000.0
            ),
        ]
        
        for cliente in clientes:
            ClienteRepository.crear(session, cliente)
        
        print(f"✅ Creados {len(clientes)} clientes")
        
        # Crear productos de prueba
        productos = [
            Producto(
                nombre="Coca Cola 2L",
                codigo_barras="7790315241234",
                precio_proveedor=80.0,
                precio_venta=120.0,
                cantidad_stock=50,
                stock_minimo=10,
                categoria="Bebidas",
                unidad_medida="unidad"
            ),
            Producto(
                nombre="Pan de Molde",
                codigo_barras="7791234567890",
                precio_proveedor=50.0,
                precio_venta=80.0,
                cantidad_stock=30,
                stock_minimo=5,
                categoria="Panadería",
                unidad_medida="unidad"
            ),
            Producto(
                nombre="Leche Entera 1L",
                precio_proveedor=45.0,
                precio_venta=70.0,
                cantidad_stock=40,
                stock_minimo=10,
                categoria="Lácteos",
                unidad_medida="litro"
            ),
            Producto(
                nombre="Arroz 1kg",
                precio_proveedor=35.0,
                precio_venta=55.0,
                cantidad_stock=100,
                stock_minimo=20,
                categoria="Almacén",
                unidad_medida="kg"
            ),
            Producto(
                nombre="Aceite Girasol 900ml",
                precio_proveedor=90.0,
                precio_venta=140.0,
                cantidad_stock=25,
                stock_minimo=5,
                categoria="Almacén",
                unidad_medida="unidad"
            ),
        ]
        
        for producto in productos:
            ProductoRepository.crear(session, producto)
        
        print(f"✅ Creados {len(productos)} productos")
        print("\n✅ ¡Datos de prueba cargados exitosamente!")
        
    except Exception as e:
        print(f"\n❌ Error al cargar datos de prueba: {e}")
        session.rollback()
    finally:
        session.close()


def main():
    """Función principal"""
    print("="*50)
    print("  INICIALIZACIÓN DE BASE DE DATOS")
    print("="*50)
    
    # Inicializar base de datos
    if init_database():
        # Preguntar si desea cargar datos de prueba
        respuesta = input("\n¿Deseas cargar datos de prueba? (s/n): ").lower()
        
        if respuesta == 's':
            cargar_datos_prueba()
        else:
            print("\n✅ Base de datos lista para usar")
    else:
        print("\n❌ No se pudo inicializar la base de datos")
        print("Verifica tu archivo .env y la conexión a Supabase")


if __name__ == "__main__":
    main()