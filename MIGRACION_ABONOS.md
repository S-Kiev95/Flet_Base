# Migración: Sistema de Abonos

## Descripción

Esta migración agrega un sistema de seguimiento detallado de abonos para las ventas fiadas. En lugar de tener un solo campo `abonado` en la tabla de ventas, ahora cada abono se registra individualmente en una nueva tabla `abonos`, permitiendo un historial completo de pagos.

## Cambios realizados

### 1. Nuevo modelo `Abono`
- Archivo: `models/abono.py`
- Tabla: `abonos`
- Campos:
  - `id`: ID único del abono
  - `venta_id`: Referencia a la venta
  - `monto`: Monto del abono
  - `fecha`: Fecha y hora del abono
  - `notas`: Notas opcionales sobre el abono
  - `fecha_creacion`: Timestamp de creación

### 2. Nuevos repositorios y métodos
- `AbonoRepository`: Nuevo repositorio para gestionar abonos
  - `crear()`: Crea un nuevo abono
  - `listar_por_venta()`: Lista abonos de una venta
  - `eliminar()`: Elimina un abono
- `VentaRepository`: Métodos actualizados
  - `calcular_abonado()`: Calcula el total abonado desde los abonos
  - `obtener_abonos()`: Obtiene abonos de una venta
  - `sincronizar_abonado()`: Sincroniza campo abonado con suma de abonos

### 3. Actualizaciones en la interfaz
- **clientes_page.py**:
  - Modal "Gestionar Abonos" con lista de abonos por venta
  - Permite agregar nuevos abonos con notas
  - Permite eliminar abonos individuales
  - Historial muestra fecha y monto de cada abono

- **nueva_venta_page.py**:
  - Al crear una venta fiada con abono inicial, se registra en la tabla de abonos

## Instrucciones para ejecutar la migración

### Paso 1: Backup de la base de datos (IMPORTANTE)
Antes de ejecutar la migración, realiza un backup de tu base de datos:

```bash
# Si usas SQLite
cp database/app.db database/app.db.backup

# Si usas PostgreSQL
pg_dump tu_base_de_datos > backup_antes_migracion.sql
```

### Paso 2: Instalar dependencias (si es necesario)
```bash
# Con uv
uv sync

# O con pip
pip install -r requirements.txt
```

### Paso 3: Ejecutar la migración
```bash
python database/migrate_add_abonos.py
```

### Paso 4: Verificar la migración
El script mostrará:
- ✓ Tabla 'abonos' creada exitosamente
- ✓ X abonos creados exitosamente (donde X es el número de ventas con abonos)
- ✓ Total de abonos en la base de datos: X

## Qué hace la migración

1. **Crea la tabla `abonos`** con todos sus campos y relaciones
2. **Migra datos existentes**: Por cada venta que tenga un campo `abonado > 0`, crea un registro en la tabla `abonos` con:
   - El monto abonado
   - La fecha de pago (si está disponible) o la fecha de la venta
   - Una nota indicando que fue migrado automáticamente
3. **Verifica** que todos los datos se hayan migrado correctamente

## Compatibilidad hacia atrás

Los campos `abonado` y `resto` en la tabla `ventas` se mantienen por compatibilidad, pero ahora:
- `abonado` se calcula sumando todos los abonos de la tabla `abonos`
- `resto` se calcula como `total - abonado`

Esto significa que el código anterior seguirá funcionando, pero los nuevos abonos se registrarán en la tabla de abonos.

## Ventajas del nuevo sistema

1. **Historial completo**: Cada pago queda registrado con fecha y hora exacta
2. **Trazabilidad**: Se puede ver cuándo y cuánto se pagó en cada abono
3. **Notas por abono**: Permite agregar información adicional a cada pago
4. **Auditoría**: Facilita el seguimiento de pagos para contabilidad
5. **Flexibilidad**: Permite eliminar abonos individuales si hubo un error

## Ejemplo de uso

### Antes (sistema antiguo):
```python
# Solo se guardaba el total abonado
venta.abonado = 100.0
```

### Ahora (nuevo sistema):
```python
# Se registra cada abono individualmente
AbonoRepository.crear(session, venta_id=1, monto=50.0, notas="Primer pago")
AbonoRepository.crear(session, venta_id=1, monto=50.0, notas="Segundo pago")
# La venta automáticamente tendrá abonado = 100.0
```

## Rollback (si es necesario)

Si necesitas revertir la migración:

1. Restaura el backup de la base de datos
2. Revierte los cambios en el código usando git:
```bash
git checkout HEAD~1 models/abono.py
git checkout HEAD~1 database/db_service.py
git checkout HEAD~1 views/clientes_page.py
git checkout HEAD~1 views/nueva_venta_page.py
```

## Soporte

Si tienes problemas con la migración:
1. Verifica que el backup de la base de datos esté completo
2. Revisa los logs de error del script de migración
3. Verifica que todas las dependencias estén instaladas
