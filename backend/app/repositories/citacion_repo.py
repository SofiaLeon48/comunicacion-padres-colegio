from datetime import datetime

from app.repositories.base import BaseRepository

_SELECT = """
    SELECT ci.*,
           e.nombre  AS estudiante_nombre,
           cu.nombre AS curso_nombre,
           d.nombre  AS docente_nombre,
           a.nombre  AS acudiente_nombre,
           ac.asistio, ac.observaciones
    FROM citaciones ci
    JOIN estudiantes e ON e.id = ci.estudiante_id
    JOIN cursos cu     ON cu.id = e.curso_id
    JOIN usuarios d    ON d.id = ci.docente_id
    LEFT JOIN usuarios a ON a.id = ci.acudiente_id
    LEFT JOIN asistencia_citaciones ac ON ac.citacion_id = ci.id AND ac.estado = 'activo'
"""


class CitacionRepository(BaseRepository):
    tabla = "citaciones"
    columnas = ["estudiante_id", "docente_id", "acudiente_id", "motivo", "fecha_hora", "lugar",
                "estado_citacion"]
    orden = "fecha_hora"

    def listar_detallado(self, desde: datetime | None = None, hasta: datetime | None = None,
                         docente_id: int | None = None, acudiente_id: int | None = None,
                         estudiante_id: int | None = None, estado_citacion: str | None = None,
                         incluir_inactivos: bool = False) -> list[dict]:
        """Sirve tanto para la lista como para el calendario (rango desde/hasta)."""
        condiciones, valores = [], []
        if not incluir_inactivos:
            condiciones.append("ci.estado = 'activo'")
        if desde:
            condiciones.append("ci.fecha_hora >= %s")
            valores.append(desde)
        if hasta:
            condiciones.append("ci.fecha_hora < %s")
            valores.append(hasta)
        if docente_id:
            condiciones.append("ci.docente_id = %s")
            valores.append(docente_id)
        if estudiante_id:
            condiciones.append("ci.estudiante_id = %s")
            valores.append(estudiante_id)
        if estado_citacion:
            condiciones.append("ci.estado_citacion = %s")
            valores.append(estado_citacion)
        if acudiente_id:
            # Citaciones dirigidas a ese acudiente, o a todos los acudientes de su hijo
            condiciones.append("""(ci.acudiente_id = %s OR (ci.acudiente_id IS NULL AND ci.estudiante_id IN (
                SELECT estudiante_id FROM acudiente_estudiante
                WHERE acudiente_id = %s AND estado = 'activo')))""")
            valores += [acudiente_id, acudiente_id]
        where = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""
        return self._todos(f"{_SELECT} {where} ORDER BY ci.fecha_hora", valores)

    def obtener_detallado(self, citacion_id: int) -> dict | None:
        return self._uno(_SELECT + " WHERE ci.id = %s AND ci.estado = 'activo'", (citacion_id,))

    def ids_acudientes_destino(self, citacion: dict) -> list[int]:
        if citacion.get("acudiente_id"):
            return [citacion["acudiente_id"]]
        filas = self._todos("""SELECT acudiente_id FROM acudiente_estudiante
                               WHERE estudiante_id = %s AND estado = 'activo'""",
                            (citacion["estudiante_id"],))
        return [f["acudiente_id"] for f in filas]
