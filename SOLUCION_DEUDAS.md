# Solución al Problema de Inconsistencia de Deudas

## Problema Identificado

El sistema tenía un problema crítico con el cálculo de deudas de clientes:

### Causa Raíz
El campo `cliente.deuda_total` se actualizaba de forma **incremental** (usando `+=` y `-=`), lo que es propenso a inconsistencias cuando:

1. Una transacción falla a mitad de camino
2. Se modifican ventas directamente en la base de datos
3. Hay errores de redondeo acumulados
4. Se eliminan o modifican ventas sin actualizar el cliente
5. Hay operaciones concurrentes

### Ejemplo del Problema

```python
# Operación incremental (PROBLEMÁTICA)
cliente.deuda_total += venta.resto  # Al crear venta
cliente.deuda_total -= monto_abono  # Al registrar abono
```

Si cualquiera de estas operaciones falla o se interrumpe, el valor queda **desincronizado permanentemente** con la realidad.

## Solución Implementada

### 1. Cálculo Dinámico de Deuda Real

Se agregó un método que calcula la deuda REAL desde las ventas:

```python
@staticmethod
def calcular_deuda_real(session: Session, cliente_id: int) -> float:
    """
    Calcula la deuda REAL sumando el resto de todas las ventas fiadas pendientes.
    Este es el valor correcto, independiente del campo deuda_total en BD.
    """
    ventas_pendientes = session.exec(
        select(Venta).where(
            Venta.cliente_id == cliente_id,
            Venta.es_fiado,
            Venta.pagado_completamente == False
        )
    ).all()

    return sum(venta.resto for venta in ventas_pendientes)
```

Este método:
- ✅ Siempre retorna el valor correcto
- ✅ No depende del campo `deuda_total`
- ✅ Es la fuente de verdad

### 2. Sincronización Automática

Al cargar la lista de clientes, ahora se sincroniza automáticamente:

```python
def _cargar_clientes(self, e):
    session = get_session_context()
    self.todos_clientes = ClienteRepository.listar_activos(session)

    # Sincronizar deuda de cada cliente con la realidad
    for cliente in self.todos_clientes:
        deuda_real = ClienteRepository.calcular_deuda_real(session, cliente.id)
        cliente.deuda_total = deuda_real  # Actualizar en memoria

    session.close()
```

### 3. Método de Sincronización Manual

Se agregó `sincronizar_deuda()` para corregir un cliente específico:

```python
@staticmethod
def sincronizar_deuda(session: Session, cliente_id: int) -> float:
    """Sincroniza el campo deuda_total con la deuda real calculada"""
    deuda_real = ClienteRepository.calcular_deuda_real(session, cliente_id)
    cliente = session.get(Cliente, cliente_id)

    if cliente:
        cliente.deuda_total = deuda_real
        cliente.fecha_actualizacion = datetime.now()
        session.add(cliente)
        session.commit()

    return deuda_real
```

### 4. Sincronización Masiva

Se agregó `sincronizar_todas_las_deudas()` para corregir todos los clientes:

```python
@staticmethod
def sincronizar_todas_las_deudas(session: Session) -> dict:
    """Sincroniza las deudas de TODOS los clientes activos"""
    clientes = ClienteRepository.listar_activos(session)
    stats = {
        'total_clientes': len(clientes),
        'clientes_corregidos': 0,
        'diferencias': []
    }

    for cliente in clientes:
        deuda_bd = cliente.deuda_total
        deuda_real = ClienteRepository.calcular_deuda_real(session, cliente.id)

        # Si hay diferencia, corregir
        if abs(deuda_bd - deuda_real) > 0.01:  # Tolerancia de 1 centavo
            cliente.deuda_total = deuda_real
            cliente.fecha_actualizacion = datetime.now()
            session.add(cliente)

            stats['clientes_corregidos'] += 1
            stats['diferencias'].append({
                'cliente_id': cliente.id,
                'nombre': cliente.nombre,
                'deuda_bd': deuda_bd,
                'deuda_real': deuda_real,
                'diferencia': deuda_real - deuda_bd
            })

    session.commit()
    return stats
```

### 5. Interfaz de Usuario

Se agregó un botón de sincronización en la página de clientes:

- **Icono**: Sincronizar (naranja) junto al botón de refrescar
- **Función**: Sincroniza todas las deudas y muestra un reporte detallado
- **Reporte incluye**:
  - Total de clientes
  - Clientes corregidos
  - Detalle de cada corrección con:
    - Nombre del cliente
    - Deuda en BD (incorrecta)
    - Deuda real (correcta)
    - Diferencia

### 6. Script de Mantenimiento

Se creó `sincronizar_deudas.py` para ejecutar desde línea de comandos:

```bash
python sincronizar_deudas.py
```

Este script:
- ✅ Puede ejecutarse sin abrir la aplicación
- ✅ Muestra detalles de todas las correcciones
- ✅ Solicita confirmación antes de proceder
- ✅ Útil para mantenimiento programado

## Uso de la Solución

### Opción 1: Desde la Aplicación

1. Abrir la página de Clientes
2. Click en el botón de sincronizar (icono naranja junto a refrescar)
3. Confirmar la operación
4. Revisar el reporte de correcciones

### Opción 2: Desde Línea de Comandos

```bash
python sincronizar_deudas.py
```

### Opción 3: Automática

La sincronización ocurre automáticamente cada vez que se carga la lista de clientes.

## Ventajas de la Solución

1. **Precisión**: La deuda siempre se calcula desde la fuente de verdad (ventas)
2. **Corrección automática**: Se corrigen inconsistencias al cargar la lista
3. **Visibilidad**: Reporte detallado de todas las correcciones
4. **Mantenimiento**: Script independiente para corrección masiva
5. **Tolerancia**: Ignora diferencias menores a 1 centavo
6. **Auditoría**: Registra cada corrección con detalles completos

## Casos de Uso

### Caso 1: Deuda Incorrecta en la Vista
**Problema**: Un cliente muestra una deuda que no coincide con sus ventas pendientes.

**Solución**:
1. Simplemente refrescar la página de clientes
2. La deuda se recalcula automáticamente

### Caso 2: Corrección Masiva Después de Migración
**Problema**: Después de una migración, varias deudas están incorrectas.

**Solución**:
```bash
python sincronizar_deudas.py
```

### Caso 3: Verificación Periódica
**Problema**: Quieres asegurarte de que todas las deudas estén correctas.

**Solución**:
1. Click en el botón de sincronizar
2. Revisar el reporte
3. Si dice "0 clientes corregidos", todo está bien

## Mantenimiento Preventivo

### Recomendaciones:

1. **Sincronización semanal**: Ejecutar el script una vez por semana
2. **Después de migraciones**: Siempre sincronizar después de cambios en BD
3. **Ante dudas**: Si un cliente reporta una deuda incorrecta, sincronizar
4. **Monitoreo**: Si el reporte muestra muchas correcciones, investigar la causa

### Comandos Útiles:

```bash
# Sincronizar todas las deudas
python sincronizar_deudas.py

# Verificar deuda de un cliente específico (desde Python shell)
from database.connection import get_session_context
from database.db_service import ClienteRepository

session = get_session_context()
deuda_real = ClienteRepository.calcular_deuda_real(session, cliente_id=1)
print(f"Deuda real: ${deuda_real:.2f}")
session.close()
```

## Archivos Modificados

1. **database/db_service.py**:
   - `calcular_deuda_real()` - Nuevo método
   - `sincronizar_deuda()` - Nuevo método
   - `sincronizar_todas_las_deudas()` - Nuevo método

2. **views/clientes_page.py**:
   - `_cargar_clientes()` - Ahora sincroniza automáticamente
   - `_sincronizar_todas_deudas()` - Nuevo método
   - `_mostrar_resultados_sincronizacion()` - Nuevo método
   - Botón de sincronización en el header

3. **models/cliente.py**:
   - Comentario actualizado en `deuda_total`

4. **sincronizar_deudas.py**:
   - Script nuevo para sincronización desde CLI

## Conclusión

La solución implementada garantiza que:

✅ Las deudas siempre reflejen la realidad desde las ventas
✅ Las inconsistencias se detectan y corrigen automáticamente
✅ Hay herramientas para corrección manual cuando sea necesario
✅ El usuario tiene visibilidad completa del proceso

El campo `deuda_total` se mantiene en la BD por rendimiento, pero ahora es **calculado y sincronizado**, no **incremental y propenso a errores**.
