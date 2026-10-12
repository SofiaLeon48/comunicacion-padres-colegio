from app.repositories.base import BaseRepository


class NotificacionRepository(BaseRepository):
    tabla = "notificaciones"
    columnas = ["usuario_id", "tipo", "titulo", "contenido", "referencia_id", "leido", "enviado_correo"]
    orden = "fecha"

    def de_usuario(self, usuario_id: int, solo_no_leidas: bool = False, limite: int = 50) -> list[dict]:
        q = "SELECT * FROM notificaciones WHERE usuario_id = %s AND estado = 'activo'"
        if solo_no_leidas:
            q += " AND NOT leido"
        return self._todos(q + " ORDER BY fecha DESC, id DESC LIMIT %s", (usuario_id, limite))

    def contar_no_leidas(self, usuario_id: int) -> int:
        fila = self._uno("""SELECT COUNT(*) AS total FROM notificaciones
                            WHERE usuario_id = %s AND NOT leido AND estado = 'activo'""", (usuario_id,))
        return fila["total"]

    def marcar_leida(self, notificacion_id: int, usuario_id: int) -> dict | None:
        return self._uno("""UPDATE notificaciones SET leido = TRUE
                            WHERE id = %s AND usuario_id = %s AND estado = 'activo'
                            RETURNING *""", (notificacion_id, usuario_id))

    def marcar_todas_leidas(self, usuario_id: int) -> int:
        return len(self._todos("""UPDATE notificaciones SET leido = TRUE
                                  WHERE usuario_id = %s AND NOT leido RETURNING id""", (usuario_id,)))

    def crear_para_varios(self, usuario_ids: list[int], tipo: str, titulo: str, contenido: str,
                          referencia_id: int | None = None) -> list[dict]:
        """Inserta una notificación por cada usuario en UNA sola sentencia SQL."""
        if not usuario_ids:
            return []
        return self._todos("""
            INSERT INTO notificaciones (usuario_id, tipo, titulo, contenido, referencia_id)
            SELECT uid, %s, %s, %s, %s FROM UNNEST(%s::int[]) AS uid
            RETURNING *
        """, (tipo, titulo[:150], contenido[:255], referencia_id, list(set(usuario_ids))))

    def marcar_correo_enviado(self, ids: list[int]) -> None:
        if ids:
            self._todos("UPDATE notificaciones SET enviado_correo = TRUE WHERE id = ANY(%s) RETURNING id",
                        (ids,))
