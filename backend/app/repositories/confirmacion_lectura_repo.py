from app.repositories.base import BaseRepository


class ConfirmacionLecturaRepository(BaseRepository):
    tabla = "confirmaciones_lectura"
    columnas = ["comunicado_id", "usuario_id"]
    orden = "fecha_confirmacion"

    def de_usuario(self, comunicado_id: int, usuario_id: int) -> dict | None:
        return self._uno("""
            SELECT * FROM confirmaciones_lectura
            WHERE comunicado_id = %s AND usuario_id = %s
        """, (comunicado_id, usuario_id))
