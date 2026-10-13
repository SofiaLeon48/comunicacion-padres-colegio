from app.repositories.base import BaseRepository


class RolModuloRepository(BaseRepository):
    tabla = "rol_modulo"
    columnas = ["rol_id", "modulo_id"]

    def modulos_de_rol(self, rol_id: int) -> list[dict]:
        """Módulos activos asignados a un rol, en el orden del menú."""
        return self._todos("""
            SELECT m.id, m.clave, m.nombre, m.descripcion, m.ruta, m.icono, m.orden
            FROM rol_modulo rm
            JOIN modulos m ON m.id = rm.modulo_id
            WHERE rm.rol_id = %s AND rm.estado = 'activo' AND m.estado = 'activo'
            ORDER BY m.orden, m.nombre
        """, (rol_id,))

    def rol_tiene_modulo(self, rol_id: int, clave: str) -> bool:
        return self._uno("""
            SELECT 1 FROM rol_modulo rm JOIN modulos m ON m.id = rm.modulo_id
            WHERE rm.rol_id = %s AND m.clave = %s AND rm.estado = 'activo' AND m.estado = 'activo'
        """, (rol_id, clave)) is not None

    def matriz(self) -> list[dict]:
        """Todas las combinaciones rol x módulo con su estado de permiso."""
        return self._todos("""
            SELECT r.id AS rol_id, r.nombre AS rol, m.id AS modulo_id, m.clave, m.nombre AS modulo,
                   m.icono, m.orden,
                   COALESCE(rm.estado = 'activo', FALSE) AS permitido
            FROM roles r CROSS JOIN modulos m
            LEFT JOIN rol_modulo rm ON rm.rol_id = r.id AND rm.modulo_id = m.id
            WHERE r.estado = 'activo' AND m.estado = 'activo'
            ORDER BY r.id, m.orden
        """)

    def asignar(self, rol_id: int, modulo_id: int, permitido: bool) -> None:
        """Activa o desactiva el permiso (crea la fila si no existe)."""
        self._uno("""
            INSERT INTO rol_modulo (rol_id, modulo_id, estado) VALUES (%s, %s, %s)
            ON CONFLICT (rol_id, modulo_id) DO UPDATE SET estado = EXCLUDED.estado
            RETURNING id
        """, (rol_id, modulo_id, "activo" if permitido else "inactivo"))
