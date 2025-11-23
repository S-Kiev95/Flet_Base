"""
Script de mantenimiento para sincronizar todas las deudas de clientes
con la realidad calculada desde las ventas pendientes.

Uso:
    python sincronizar_deudas.py
"""

from database.connection import get_session_context
from database.db_service import ClienteRepository


def main():
    print("=" * 70)
    print("SINCRONIZACIÓN DE DEUDAS DE CLIENTES")
    print("=" * 70)
    print()
    print("Este script corregirá las deudas de todos los clientes")
    print("calculándolas desde las ventas pendientes reales.")
    print()

    respuesta = input("¿Deseas continuar? (s/n): ")

    if respuesta.lower() != 's':
        print("Operación cancelada.")
        return

    print()
    print("Sincronizando...")
    print()

    try:
        session = get_session_context()
        stats = ClienteRepository.sincronizar_todas_las_deudas(session)
        session.close()

        print("=" * 70)
        print("SINCRONIZACIÓN COMPLETADA")
        print("=" * 70)
        print()
        print(f"Total de clientes: {stats['total_clientes']}")
        print(f"Clientes corregidos: {stats['clientes_corregidos']}")
        print()

        if stats['diferencias']:
            print("Detalles de las correcciones:")
            print("-" * 70)

            for diff in stats['diferencias']:
                print(f"\nCliente: {diff['nombre']} (ID: {diff['cliente_id']})")
                print(f"  Deuda en BD:   ${diff['deuda_bd']:.2f}")
                print(f"  Deuda real:    ${diff['deuda_real']:.2f}")
                diferencia = diff['diferencia']
                signo = "+" if diferencia > 0 else ""
                print(f"  Diferencia:    {signo}${diferencia:.2f}")

            print()
            print("-" * 70)
        else:
            print("✓ Todas las deudas estaban correctas. No se realizaron cambios.")

        print()
        print("Sincronización completada exitosamente.")

    except Exception as e:
        print()
        print(f"❌ ERROR durante la sincronización: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
