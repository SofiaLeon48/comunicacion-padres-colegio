from app.repositories.base import BaseRepository

_SELECT = """
    SELECT m.*, u.nombre AS remitente_nombre, r.nombre AS remitente_rol
    FROM mensajes m
    JOIN usuarios u ON u.id = m.remitente_id
    JOIN roles r    ON r.id = u.rol_id
"""


class MensajeRepository(BaseRepository):
    tabla = "mensajes"
    columnas = ["remitente_id", "grupo_id", "destinatario_id", "contenido", "leido"]
    orden = "fecha_envio"

    def obtener_detallado(self, mensaje_id: int) -> dict | None:
        return self._uno(_SELECT + " WHERE m.id = %s", (mensaje_id,))

    def del_grupo(self, grupo_id: int, limite: int = 50, antes_de: int | None = None) -> list[dict]:
        """Últimos mensajes del chat de un grupo (paginación hacia atrás con antes_de)."""
        q = _SELECT + " WHERE m.grupo_id = %s AND m.estado = 'activo'"
        valores: list = [grupo_id]
        if antes_de:
            q += " AND m.id < %s"
            valores.append(antes_de)
        q += " ORDER BY m.id DESC LIMIT %s"
        valores.append(limite)
        return list(reversed(self._todos(q, valores)))   # de más antiguo a más reciente

    def conversacion(self, usuario_a: int, usuario_b: int, limite: int = 50) -> list[dict]:
        filas = self._todos(_SELECT + """
            WHERE m.estado = 'activo' AND m.grupo_id IS NULL
              AND ((m.remitente_id = %(a)s AND m.destinatario_id = %(b)s)
                OR (m.remitente_id = %(b)s AND m.destinatario_id = %(a)s))
            ORDER BY m.id DESC LIMIT %(lim)s
        """, {"a": usuario_a, "b": usuario_b, "lim": limite})
        return list(reversed(filas))

    def bandeja(self, usuario_id: int) -> list[dict]:
        """Lista de conversaciones directas: último mensaje con cada persona y no leídos."""
        return self._todos("""
            WITH directos AS (
                SELECT m.*,
                       CASE WHEN m.remitente_id = %(u)s THEN m.destinatario_id
                            ELSE m.remitente_id END AS contraparte_id
                FROM mensajes m
                WHERE m.grupo_id IS NULL AND m.estado = 'activo'
                  AND (m.remitente_id = %(u)s OR m.destinatario_id = %(u)s)
            ),
            ultimos AS (
                SELECT DISTINCT ON (contraparte_id) *
                FROM directos ORDER BY contraparte_id, id DESC
            )
            SELECT ul.contraparte_id, u.nombre AS contraparte_nombre, r.nombre AS contraparte_rol,
                   ul.contenido AS ultimo_mensaje, ul.fecha_envio,
                   (SELECT COUNT(*) FROM directos d
                     WHERE d.contraparte_id = ul.contraparte_id
                       AND d.destinatario_id = %(u)s AND NOT d.leido) AS no_leidos
            FROM ultimos ul
            JOIN usuarios u ON u.id = ul.contraparte_id
            JOIN roles r    ON r.id = u.rol_id
            ORDER BY ul.fecha_envio DESC
        """, {"u": usuario_id})

    def marcar_leidos(self, remitente_id: int, destinatario_id: int) -> int:
        filas = self._todos("""
            UPDATE mensajes SET leido = TRUE
            WHERE remitente_id = %s AND destinatario_id = %s AND NOT leido
            RETURNING id
        """, (remitente_id, destinatario_id))
        return len(filas)
