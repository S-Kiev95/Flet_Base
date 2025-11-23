"""Repositorio para operaciones CRUD"""

from typing import List, Optional
from sqlmodel import Session, select
from datetime import datetime

from models.cliente import Cliente
from models.producto import Producto
from models.venta import Venta
from models.abono import Abono
from models.usuario import Usuario, RolUsuario
from models.sesion import Sesion


class ClienteRepository:
    """Repositorio para operaciones de Cliente"""
    
    @staticmethod
    def crear(session: Session, cliente: Cliente) -> Cliente:
        """Crea un nuevo cliente"""
        session.add(cliente)
        session.commit()
        session.refresh(cliente)
        return cliente
    
    @staticmethod
    def obtener_por_id(session: Session, cliente_id: int) -> Optional[Cliente]:
        """Obtiene un cliente por ID"""
        return session.get(Cliente, cliente_id)
    
    @staticmethod
    def listar_activos(session: Session) -> List[Cliente]:
        """Lista todos los clientes activos"""
        statement = select(Cliente).where(Cliente.activo).order_by(Cliente.nombre)
        return session.exec(statement).all()
    
    @staticmethod
    def buscar_por_nombre(session: Session, nombre: str) -> List[Cliente]:
        """Busca clientes por nombre (parcial)"""
        statement = select(Cliente).where(
            Cliente.nombre.ilike(f"%{nombre}%"),
            Cliente.activo
        )
        return session.exec(statement).all()
    
    @staticmethod
    def actualizar(session: Session, cliente: Cliente) -> Cliente:
        """Actualiza un cliente"""
        cliente.fecha_actualizacion = datetime.now()
        session.add(cliente)
        session.commit()
        session.refresh(cliente)
        return cliente
    
    @staticmethod
    def actualizar_deuda(session: Session, cliente_id: int, monto: float):
        """Actualiza la deuda de un cliente"""
        cliente = session.get(Cliente, cliente_id)
        if cliente:
            cliente.deuda_total += monto
            cliente.fecha_actualizacion = datetime.now()
            session.add(cliente)
            session.commit()
    
    @staticmethod
    def listar_con_deuda(session: Session) -> List[Cliente]:
        """Lista clientes con deuda pendiente"""
        statement = select(Cliente).where(
            Cliente.deuda_total > 0,
            Cliente
        ).order_by(Cliente.deuda_total.desc())
        return session.exec(statement).all()

    @staticmethod
    def calcular_deuda_real(session: Session, cliente_id: int) -> float:
        """
        Calcula la deuda REAL sumando el resto de todas las ventas fiadas pendientes.
        Este es el valor correcto, independiente del campo deuda_total en BD.
        """
        statement = select(Venta).where(
            Venta.cliente_id == cliente_id,
            Venta.es_fiado,
            Venta.pagado_completamente == False
        )
        ventas_pendientes = session.exec(statement).all()
        return sum(venta.resto for venta in ventas_pendientes)

    @staticmethod
    def sincronizar_deuda(session: Session, cliente_id: int) -> float:
        """
        Sincroniza el campo deuda_total con la deuda real calculada desde las ventas.
        Retorna la deuda real después de la sincronización.
        """
        deuda_real = ClienteRepository.calcular_deuda_real(session, cliente_id)
        cliente = session.get(Cliente, cliente_id)

        if cliente:
            cliente.deuda_total = deuda_real
            cliente.fecha_actualizacion = datetime.now()
            session.add(cliente)
            session.commit()

        return deuda_real

    @staticmethod
    def sincronizar_todas_las_deudas(session: Session) -> dict:
        """
        Sincroniza las deudas de TODOS los clientes activos.
        Retorna un diccionario con estadísticas de la sincronización.
        """
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


class ProductoRepository:
    """Repositorio para operaciones de Producto"""
    
    @staticmethod
    def crear(session: Session, producto: Producto) -> Producto:
        """Crea un nuevo producto"""
        session.add(producto)
        session.commit()
        session.refresh(producto)
        return producto
    
    @staticmethod
    def obtener_por_id(session: Session, producto_id: int) -> Optional[Producto]:
        """Obtiene un producto por ID"""
        return session.get(Producto, producto_id)
    
    @staticmethod
    def listar_activos(session: Session) -> List[Producto]:
        """Lista todos los productos activos"""
        statement = select(Producto).where(Producto.activo).order_by(Producto.nombre)
        return session.exec(statement).all()
    
    @staticmethod
    def buscar_por_nombre(session: Session, nombre: str) -> List[Producto]:
        """Busca productos por nombre (parcial)"""
        statement = select(Producto).where(
            Producto.nombre.ilike(f"%{nombre}%"),
            Producto.activo
        )
        return session.exec(statement).all()
    
    @staticmethod
    def buscar_por_codigo(session: Session, codigo: str) -> Optional[Producto]:
        """Busca producto por código de barras"""
        statement = select(Producto).where(
            Producto.codigo_barras == codigo,
            Producto.activo
        )
        return session.exec(statement).first()
    
    @staticmethod
    def actualizar(session: Session, producto: Producto) -> Producto:
        """Actualiza un producto"""
        producto.fecha_actualizacion = datetime.now()
        session.add(producto)
        session.commit()
        session.refresh(producto)
        return producto
    
    @staticmethod
    def descontar_stock(session: Session, producto_id: int, cantidad: float):
        """Descuenta stock de un producto"""
        producto = session.get(Producto, producto_id)
        if producto:
            producto.cantidad_stock -= cantidad
            producto.fecha_actualizacion = datetime.now()
            session.add(producto)
            session.commit()
    
    @staticmethod
    def listar_bajo_stock(session: Session) -> List[Producto]:
        """Lista productos con stock bajo"""
        statement = select(Producto).where(
            Producto.cantidad_stock <= Producto.stock_minimo,
            Producto.activo
        )
        return session.exec(statement).all()


class VentaRepository:
    """Repositorio para operaciones de Venta"""
    
    @staticmethod
    def crear(session: Session, venta: Venta) -> Venta:
        """Crea una nueva venta y actualiza stock si corresponde"""
        # Calcular totales
        venta.calcular_totales()
        
        # Descontar stock de productos de BD
        for item in venta.get_items_con_stock():
            producto_id = item.get("producto_id")
            cantidad = item.get("cantidad", 0)
            if producto_id:
                ProductoRepository.descontar_stock(session, producto_id, cantidad)
        
        # Si es fiado, actualizar deuda del cliente
        if venta.es_fiado and venta.cliente_id:
            ClienteRepository.actualizar_deuda(session, venta.cliente_id, venta.resto)
        
        session.add(venta)
        session.commit()
        session.refresh(venta)
        return venta
    
    @staticmethod
    def obtener_por_id(session: Session, venta_id: int) -> Optional[Venta]:
        """Obtiene una venta por ID"""
        return session.get(Venta, venta_id)
    
    @staticmethod
    def listar_todas(session: Session, limit: int = 100) -> List[Venta]:
        """Lista todas las ventas (las más recientes primero)"""
        statement = select(Venta).order_by(Venta.fecha.desc()).limit(limit)
        return session.exec(statement).all()
    
    @staticmethod
    def listar_pendientes(session: Session) -> List[Venta]:
        """Lista ventas fiadas pendientes de pago"""
        statement = select(Venta).where(
            Venta.es_fiado,
            Venta.pagado_completamente == False
        ).order_by(Venta.fecha.desc())
        return session.exec(statement).all()
    
    @staticmethod
    def listar_por_cliente(session: Session, cliente_id: int) -> List[Venta]:
        """Lista ventas de un cliente específico"""
        statement = select(Venta).where(
            Venta.cliente_id == cliente_id
        ).order_by(Venta.fecha.desc())
        return session.exec(statement).all()
    
    @staticmethod
    def registrar_abono(session: Session, venta_id: int, monto: float, notas: Optional[str] = None, usuario_id: Optional[int] = None, usuario_nombre: Optional[str] = None) -> Optional[Venta]:
        """Registra un abono a una venta fiada (usa AbonoRepository internamente)"""
        # Ahora delegamos a AbonoRepository para crear el abono
        abono = AbonoRepository.crear(session, venta_id, monto, notas, usuario_id, usuario_nombre)
        # Devolver la venta actualizada
        return session.get(Venta, venta_id)
    
    @staticmethod
    def listar_fiados_cliente(session: Session, cliente_id: int) -> List[Venta]:
        """Lista ventas fiadas pendientes de un cliente"""
        statement = select(Venta).where(
            Venta.cliente_id == cliente_id,
            Venta.es_fiado,
            Venta.pagado_completamente == False
        ).order_by(Venta.fecha.desc())
        return session.exec(statement).all()

    @staticmethod
    def actualizar(session: Session, venta: Venta) -> Venta:
        """Actualiza una venta existente"""
        venta.fecha_actualizacion = datetime.now()
        venta.calcular_totales()
        session.add(venta)
        session.commit()
        session.refresh(venta)
        return venta

    @staticmethod
    def eliminar(session: Session, venta_id: int) -> bool:
        """Elimina una venta y revierte los cambios de stock y deuda"""
        venta = session.get(Venta, venta_id)
        if not venta:
            return False

        # Revertir stock de productos
        for item in venta.get_items_con_stock():
            producto_id = item.get("producto_id")
            cantidad = item.get("cantidad", 0)
            if producto_id:
                producto = session.get(Producto, producto_id)
                if producto:
                    producto.cantidad_stock += cantidad
                    producto.fecha_actualizacion = datetime.now()
                    session.add(producto)

        # Si es fiado, revertir la deuda del cliente
        if venta.es_fiado and venta.cliente_id:
            cliente = session.get(Cliente, venta.cliente_id)
            if cliente:
                # Restar el resto pendiente de la deuda (lo que aún debe)
                # Si la venta está completamente pagada, resto = 0, entonces no afecta
                # Si tiene saldo pendiente, resto > 0, entonces se resta de la deuda
                cliente.deuda_total -= venta.resto
                cliente.fecha_actualizacion = datetime.now()
                session.add(cliente)

        # Eliminar la venta
        session.delete(venta)
        session.commit()
        return True

    @staticmethod
    def calcular_abonado(session: Session, venta_id: int) -> float:
        """Calcula el total abonado de una venta desde los abonos registrados"""
        statement = select(Abono).where(Abono.venta_id == venta_id)
        abonos = session.exec(statement).all()
        return sum(abono.monto for abono in abonos)

    @staticmethod
    def obtener_abonos(session: Session, venta_id: int) -> List[Abono]:
        """Obtiene todos los abonos de una venta"""
        statement = select(Abono).where(Abono.venta_id == venta_id).order_by(Abono.fecha)
        return session.exec(statement).all()

    @staticmethod
    def sincronizar_abonado(session: Session, venta_id: int):
        """Sincroniza el campo abonado de la venta con la suma de abonos"""
        venta = session.get(Venta, venta_id)
        if venta:
            total_abonado = VentaRepository.calcular_abonado(session, venta_id)
            venta.abonado = total_abonado
            venta.calcular_totales()
            session.add(venta)
            session.commit()


class AbonoRepository:
    """Repositorio para operaciones de Abono"""

    @staticmethod
    def crear(session: Session, venta_id: int, monto: float, notas: Optional[str] = None, usuario_id: Optional[int] = None, usuario_nombre: Optional[str] = None) -> Abono:
        """Crea un nuevo abono para una venta"""
        venta = session.get(Venta, venta_id)
        if not venta:
            raise ValueError(f"Venta con id {venta_id} no encontrada")

        if not venta.es_fiado:
            raise ValueError("Solo se pueden registrar abonos en ventas fiadas")

        if monto <= 0:
            raise ValueError("El monto del abono debe ser mayor a 0")

        # Calcular cuánto se ha abonado hasta ahora
        total_abonado_actual = VentaRepository.calcular_abonado(session, venta_id)
        resto_pendiente = venta.total - total_abonado_actual

        if monto > resto_pendiente:
            raise ValueError(f"El monto del abono (${monto:.2f}) excede el resto pendiente (${resto_pendiente:.2f})")

        # Crear el abono
        abono = Abono(
            venta_id=venta_id,
            monto=monto,
            notas=notas,
            usuario_id=usuario_id,
            usuario_nombre=usuario_nombre
        )
        session.add(abono)

        # Actualizar la venta
        venta.abonado = total_abonado_actual + monto
        venta.calcular_totales()
        session.add(venta)

        # Actualizar deuda del cliente
        if venta.cliente_id:
            ClienteRepository.actualizar_deuda(session, venta.cliente_id, -monto)

        session.commit()
        session.refresh(abono)
        return abono

    @staticmethod
    def listar_por_venta(session: Session, venta_id: int) -> List[Abono]:
        """Lista todos los abonos de una venta"""
        statement = select(Abono).where(Abono.venta_id == venta_id).order_by(Abono.fecha)
        return session.exec(statement).all()

    @staticmethod
    def obtener_por_id(session: Session, abono_id: int) -> Optional[Abono]:
        """Obtiene un abono por ID"""
        return session.get(Abono, abono_id)

    @staticmethod
    def eliminar(session: Session, abono_id: int) -> bool:
        """Elimina un abono y actualiza la venta"""
        abono = session.get(Abono, abono_id)
        if not abono:
            return False

        # Obtener la venta
        venta = session.get(Venta, abono.venta_id)
        if not venta:
            return False

        # Actualizar la venta
        venta.abonado -= abono.monto
        venta.calcular_totales()
        session.add(venta)

        # Actualizar deuda del cliente (sumar el monto que se elimina)
        if venta.cliente_id:
            ClienteRepository.actualizar_deuda(session, venta.cliente_id, abono.monto)

        # Eliminar el abono
        session.delete(abono)
        session.commit()
        return True


class UsuarioRepository:
    """Repositorio para operaciones de Usuario"""

    @staticmethod
    def crear(session: Session, usuario: Usuario) -> Usuario:
        """Crea un nuevo usuario"""
        session.add(usuario)
        session.commit()
        session.refresh(usuario)
        return usuario

    @staticmethod
    def obtener_por_id(session: Session, usuario_id: int) -> Optional[Usuario]:
        """Obtiene un usuario por ID"""
        return session.get(Usuario, usuario_id)

    @staticmethod
    def obtener_por_nombre(session: Session, nombre: str) -> Optional[Usuario]:
        """Obtiene un usuario por nombre (para login)"""
        statement = select(Usuario).where(
            Usuario.nombre == nombre,
            Usuario.activo
        )
        return session.exec(statement).first()

    @staticmethod
    def listar_activos(session: Session) -> List[Usuario]:
        """Lista todos los usuarios activos"""
        statement = select(Usuario).where(Usuario.activo).order_by(Usuario.nombre)
        return session.exec(statement).all()

    @staticmethod
    def listar_todos(session: Session) -> List[Usuario]:
        """Lista todos los usuarios (incluyendo inactivos)"""
        statement = select(Usuario).order_by(Usuario.activo.desc(), Usuario.nombre)
        return session.exec(statement).all()

    @staticmethod
    def actualizar(session: Session, usuario: Usuario) -> Usuario:
        """Actualiza un usuario"""
        usuario.fecha_actualizacion = datetime.now()
        session.add(usuario)
        session.commit()
        session.refresh(usuario)
        return usuario

    @staticmethod
    def autenticar(session: Session, nombre: str, contraseña: str) -> Optional[Usuario]:
        """Autentica un usuario con nombre y contraseña"""
        usuario = UsuarioRepository.obtener_por_nombre(session, nombre)
        if usuario and usuario.contraseña == contraseña and usuario.activo:
            # Actualizar último acceso
            usuario.actualizar_ultimo_acceso()
            session.add(usuario)
            session.commit()
            session.refresh(usuario)  # Mantener el objeto vinculado a la sesión
            return usuario
        return None

    @staticmethod
    def existe_superadmin(session: Session) -> bool:
        """Verifica si existe al menos un SuperAdmin activo"""
        statement = select(Usuario).where(
            Usuario.rol == RolUsuario.SUPERADMIN.value,
            Usuario.activo
        )
        return session.exec(statement).first() is not None

    @staticmethod
    def crear_usuario_inicial(session: Session) -> Usuario:
        """Crea el usuario SuperAdmin inicial si no existe ninguno"""
        if not UsuarioRepository.existe_superadmin(session):
            admin = Usuario(
                nombre="admin",
                rol=RolUsuario.SUPERADMIN.value,
                contraseña="admin"
            )
            return UsuarioRepository.crear(session, admin)
        return None


class SesionRepository:
    """Repositorio para operaciones de Sesión"""

    @staticmethod
    def crear(db_session: Session, sesion: Sesion) -> Sesion:
        """Crea una nueva sesión"""
        db_session.add(sesion)
        db_session.commit()
        db_session.refresh(sesion)
        return sesion

    @staticmethod
    def obtener_por_token(session: Session, token: str) -> Optional[Sesion]:
        """Obtiene una sesión por su token"""
        statement = select(Sesion).where(Sesion.token == token)
        return session.exec(statement).first()

    @staticmethod
    def obtener_activa_usuario(session: Session, usuario_id: int) -> Optional[Sesion]:
        """Obtiene la sesión activa de un usuario"""
        statement = select(Sesion).where(
            Sesion.usuario_id == usuario_id,
            Sesion.activa
        ).order_by(Sesion.fecha_inicio.desc())
        return session.exec(statement).first()

    @staticmethod
    def validar_sesion(session: Session, token: str) -> Optional[Usuario]:
        """Valida un token de sesión y devuelve el usuario si es válido"""
        sesion = SesionRepository.obtener_por_token(session, token)

        if not sesion or not sesion.es_valida():
            return None

        # Actualizar último uso
        sesion.fecha_ultimo_uso = datetime.now()
        session.add(sesion)
        session.commit()

        # Obtener usuario
        return session.get(Usuario, sesion.usuario_id)

    @staticmethod
    def cerrar_sesion(session: Session, token: str) -> bool:
        """Cierra una sesión por su token"""
        sesion = SesionRepository.obtener_por_token(session, token)
        if sesion:
            sesion.cerrar()
            session.add(sesion)
            session.commit()
            return True
        return False

    @staticmethod
    def cerrar_sesiones_usuario(session: Session, usuario_id: int):
        """Cierra todas las sesiones activas de un usuario"""
        statement = select(Sesion).where(
            Sesion.usuario_id == usuario_id,
            Sesion.activa
        )
        sesiones = session.exec(statement).all()

        for sesion in sesiones:
            sesion.cerrar()
            session.add(sesion)

        session.commit()

    @staticmethod
    def limpiar_sesiones_expiradas(session: Session):
        """Cierra todas las sesiones expiradas"""
        statement = select(Sesion).where(
            Sesion.activa,
            Sesion.fecha_expiracion < datetime.now()
        )
        sesiones = session.exec(statement).all()

        for sesion in sesiones:
            sesion.cerrar()
            session.add(sesion)

        session.commit()

    @staticmethod
    def iniciar_sesion(session: Session, usuario_id: int, duracion_horas: int = 8) -> Sesion:
        """Inicia una nueva sesión para un usuario (cierra sesiones anteriores)"""
        # Cerrar sesiones anteriores del usuario
        SesionRepository.cerrar_sesiones_usuario(session, usuario_id)

        # Crear nueva sesión
        nueva_sesion = Sesion.crear_nueva(usuario_id, duracion_horas)
        return SesionRepository.crear(session, nueva_sesion)