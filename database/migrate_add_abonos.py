"""
Script de migración para:
1. Agregar la tabla de abonos
2. Agregar la tabla de usuarios
3. Agregar la tabla de sesiones
4. Agregar columnas usuario_id a ventas y abonos
5. Migrar datos existentes
"""

from sqlmodel import SQLModel, create_engine, Session, select, text
from datetime import datetime
import sys
import os

# Agregar el directorio raíz al path para importar los modelos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.venta import Venta
from models.abono import Abono
from models.usuario import Usuario, RolUsuario
from models.sesion import Sesion
from database.connection import engine


def migrate():
    """Ejecuta la migración completa"""

    print("=" * 70)
    print("MIGRACIÓN: Sistema de Abonos y Usuarios")
    print("=" * 70)

    # engine ya importado desde database.connection

    # 1. Crear tablas nuevas
    print("\n[1/6] Creando nuevas tablas...")
    SQLModel.metadata.create_all(engine, tables=[
        Usuario.__table__,
        Sesion.__table__,
        Abono.__table__,
    ])
    print("✓ Tablas 'usuarios', 'sesiones' y 'abonos' creadas")

    # 2. Crear usuario admin inicial
    print("\n[2/6] Creando usuario administrador inicial...")
    with Session(engine) as session:
        # Verificar si ya existe un admin
        admin_existente = session.exec(
            select(Usuario).where(Usuario.nombre == "admin")
        ).first()

        if not admin_existente:
            admin = Usuario(
                nombre="admin",
                rol=RolUsuario.SUPERADMIN.value,
                contraseña="admin",
                activo=True
            )
            session.add(admin)
            session.commit()
            session.refresh(admin)
            print(f"✓ Usuario administrador creado: admin/admin (ID: {admin.id})")
            usuario_default_id = admin.id
        else:
            print(f"✓ Usuario administrador ya existe (ID: {admin_existente.id})")
            usuario_default_id = admin_existente.id

    # 3. Agregar columnas usuario_id a ventas (si no existen)
    print("\n[3/6] Agregando columnas de usuario a tabla 'ventas'...")
    with engine.begin() as conn:
        try:
            # Intentar agregar la columna usuario_id
            conn.execute(text(
                "ALTER TABLE ventas ADD COLUMN usuario_id INTEGER"
            ))
            conn.execute(text(
                "ALTER TABLE ventas ADD COLUMN usuario_nombre VARCHAR(100)"
            ))
            print("✓ Columnas agregadas a 'ventas'")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("✓ Columnas ya existen en 'ventas'")
            else:
                raise e

    # 4. Actualizar ventas existentes con usuario por defecto
    print("\n[4/6] Asignando usuario por defecto a ventas existentes...")
    with Session(engine) as session:
        ventas_sin_usuario = session.exec(
            select(Venta).where(Venta.usuario_id == None)
        ).all()

        if ventas_sin_usuario:
            for venta in ventas_sin_usuario:
                venta.usuario_id = usuario_default_id
                venta.usuario_nombre = "admin"
                session.add(venta)

            session.commit()
            print(f"✓ {len(ventas_sin_usuario)} ventas actualizadas con usuario 'admin'")
        else:
            print("✓ Todas las ventas ya tienen usuario asignado")

    # 5. Migrar abonos desde campo abonado en ventas
    print("\n[5/6] Migrando abonos desde ventas existentes...")
    with Session(engine) as session:
        # Obtener todas las ventas fiadas con abonos
        statement = select(Venta).where(Venta.es_fiado, Venta.abonado > 0)
        ventas_con_abonos = session.exec(statement).all()

        print(f"   Encontradas {len(ventas_con_abonos)} ventas con abonos")

        abonos_creados = 0
        for venta in ventas_con_abonos:
            # Verificar si ya existe un abono para esta venta
            abono_existente = session.exec(
                select(Abono).where(Abono.venta_id == venta.id)
            ).first()

            if not abono_existente:
                # Crear un abono por cada venta que tenga monto abonado
                abono = Abono(
                    venta_id=venta.id,
                    usuario_id=venta.usuario_id or usuario_default_id,
                    usuario_nombre=venta.usuario_nombre or "admin",
                    monto=venta.abonado,
                    fecha=venta.fecha_pago_completo if venta.pagado_completamente else venta.fecha,
                    notas="Abono migrado automáticamente desde datos históricos",
                    fecha_creacion=venta.fecha_creacion
                )
                session.add(abono)
                abonos_creados += 1

        session.commit()
        print(f"✓ {abonos_creados} abonos creados exitosamente")

    # 6. Verificar migración
    print("\n[6/6] Verificando migración...")
    with Session(engine) as session:
        total_usuarios = len(session.exec(select(Usuario)).all())
        total_ventas = len(session.exec(select(Venta)).all())
        total_abonos = len(session.exec(select(Abono)).all())
        ventas_con_usuario = len(session.exec(
            select(Venta).where(Venta.usuario_id != None)
        ).all())

        print(f"✓ Total de usuarios: {total_usuarios}")
        print(f"✓ Total de ventas: {total_ventas}")
        print(f"✓ Ventas con usuario asignado: {ventas_con_usuario}")
        print(f"✓ Total de abonos: {total_abonos}")

    print("\n" + "=" * 70)
    print("MIGRACIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 70)
    print("\nInformación importante:")
    print("- Usuario administrador: admin / admin")
    print("- Todas las ventas existentes han sido asignadas al usuario 'admin'")
    print("- Los campos 'abonado' y 'resto' en 'ventas' se mantienen para compatibilidad")
    print("- Todos los abonos históricos han sido migrados a la tabla 'abonos'")
    print("- A partir de ahora:")
    print("  • Los usuarios deben iniciar sesión para usar el sistema")
    print("  • Las sesiones duran 8 horas")
    print("  • Cada venta y abono registra quién lo realizó")
    print("  • Solo los SuperAdmin pueden gestionar usuarios")
    print()


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"\n❌ ERROR durante la migración: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
