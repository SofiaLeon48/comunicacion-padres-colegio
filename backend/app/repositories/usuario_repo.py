from app.repositories.base import BaseRepository

_SELECT_CON_ROL = """
    SELECT u.*, r.nombre AS rol
    FROM usuarios u
    JOIN roles r ON r.id = u.rol_id
"""


class UsuarioRepository(BaseRepository):
    tabla = "usuarios"
    columnas = ["nombre", "correo", "password_hash", "telefono", "rol_id"]
    orden = "nombre"

    def obtener_con_rol(self, usuario_id: int, incluir_inactivos: bool = False) -> dict | None:
        q = _SELECT_CON_ROL + " WHERE u.id = %s"
        if not incluir_inactivos:
            q += " AND u.estado = 'activo'"
        return self._uno(q, (usuario_id,))

    def obtener_por_correo(self, correo: str) -> dict | None:
        return self._uno(_SELECT_CON_ROL + " WHERE LOWER(u.correo) = LOWER(%s)", (correo,))

    def listar_con_rol(self, rol: str | None = None, buscar: str | None = None,
                       incluir_inactivos: bool = False) -> list[dict]:
        condiciones, valores = [], []
        if not incluir_inactivos:
            condiciones.append("u.estado = 'activo'")
        if rol:
            condiciones.append("r.nombre = %s")
            valores.append(rol)
        if buscar:
            condiciones.append("(u.nombre ILIKE %s OR u.correo ILIKE %s)")
            valores += [f"%{buscar}%", f"%{buscar}%"]
        q = _SELECT_CON_ROL
        if condiciones:
            q += " WHERE " + " AND ".join(condiciones)
        return self._todos(q + " ORDER BY u.nombre", valores)

    def registrar_acceso(self, usuario_id: int) -> None:
        self._uno("UPDATE usuarios SET ultimo_acceso = NOW() WHERE id = %s RETURNING id", (usuario_id,))

    def ids_por_roles(self, roles: list[str]) -> list[int]:
        filas = self._todos(
            "SELECT u.id FROM usuarios u JOIN roles r ON r.id = u.rol_id "
            "WHERE r.nombre = ANY(%s) AND u.estado = 'activo'", (roles,))
        return [f["id"] for f in filas]
