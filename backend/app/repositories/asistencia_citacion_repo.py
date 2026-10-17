from app.repositories.base import BaseRepository


class AsistenciaCitacionRepository(BaseRepository):
    tabla = "asistencia_citaciones"
    columnas = ["citacion_id", "asistio", "observaciones", "registrado_por"]

    def de_citacion(self, citacion_id: int) -> dict | None:
        return self._uno("""SELECT * FROM asistencia_citaciones
                            WHERE citacion_id = %s AND estado = 'activo'""", (citacion_id,))
