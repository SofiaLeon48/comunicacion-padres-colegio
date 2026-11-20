"""
Tablero (dashboard): indicadores y datos para gráficos, calculados en vivo con SQL.

Todos los métodos aceptan los mismos filtros:
  - grupo_id: solo la actividad de ese grupo (None = todo el colegio)
  - desde / hasta: rango de fechas (inclusive)
"""
from datetime import date

from app.repositories.base import BaseRepository


class TableroRepository(BaseRepository):

    @staticmethod
    def _params(grupo_id: int | None, desde: date | None, hasta: date | None) -> dict:
        return {"g": grupo_id, "d": desde, "h": hasta}

    # Fragmentos de filtro por tabla (NULL en un parámetro = sin filtro)
    F_COMUNICADO = """c.estado = 'activo'
        AND (%(g)s::int IS NULL OR c.grupo_id = %(g)s)
        AND (%(d)s::date IS NULL OR c.fecha_publicacion::date >= %(d)s)
        AND (%(h)s::date IS NULL OR c.fecha_publicacion::date <= %(h)s)"""
    F_MENSAJE = """m.estado = 'activo'
        AND (%(g)s::int IS NULL OR m.grupo_id = %(g)s)
        AND (%(d)s::date IS NULL OR m.fecha_envio::date >= %(d)s)
        AND (%(h)s::date IS NULL OR m.fecha_envio::date <= %(h)s)"""
    F_CITACION = """ci.estado = 'activo'
        AND (%(g)s::int IS NULL OR e.grupo_id = %(g)s)
        AND (%(d)s::date IS NULL OR ci.fecha_hora::date >= %(d)s)
        AND (%(h)s::date IS NULL OR ci.fecha_hora::date <= %(h)s)"""

    LECTURA = """
        WITH destinatarios AS (
            SELECT c.id, COUNT(DISTINCT ae.acudiente_id) AS total
            FROM comunicados c
            JOIN estudiantes e ON (c.grupo_id IS NULL OR e.grupo_id = c.grupo_id) AND e.estado = 'activo'
            JOIN acudiente_estudiante ae ON ae.estudiante_id = e.id AND ae.estado = 'activo'
            GROUP BY c.id
        ),
        confirmados AS (
            SELECT comunicado_id AS id, COUNT(*) AS total
            FROM confirmaciones_lectura WHERE estado = 'activo' GROUP BY comunicado_id
        ),
        lectura AS (
            SELECT c.id, COALESCE(g.nombre, 'General') AS grupo, g.grado,
                   CASE WHEN COALESCE(d.total, 0) = 0 THEN 0
                        ELSE 100.0 * COALESCE(cf.total, 0) / d.total END AS porcentaje
            FROM comunicados c
            LEFT JOIN grupos g        ON g.id = c.grupo_id
            LEFT JOIN destinatarios d ON d.id = c.id
            LEFT JOIN confirmados cf  ON cf.id = c.id
            WHERE c.requiere_confirmacion AND {filtro}
        )
    """

    def indicadores(self, grupo_id=None, desde=None, hasta=None) -> dict:
        p = self._params(grupo_id, desde, hasta)
        fila = self._uno(f"""
            {self.LECTURA.format(filtro=self.F_COMUNICADO)}
            SELECT
              (SELECT COUNT(*) FROM comunicados c WHERE {self.F_COMUNICADO})            AS comunicados,
              (SELECT ROUND(COALESCE(AVG(porcentaje), 0), 1) FROM lectura)             AS lectura_promedio,
              (SELECT COUNT(*) FROM citaciones ci JOIN estudiantes e ON e.id = ci.estudiante_id
                WHERE {self.F_CITACION})                                               AS citaciones,
              (SELECT COUNT(*) FROM mensajes m WHERE {self.F_MENSAJE})                 AS mensajes
        """, p)
        return {k: float(v) if k == "lectura_promedio" else int(v) for k, v in fila.items()}

    def comunicados_por_grupo(self, grupo_id=None, desde=None, hasta=None) -> list[dict]:
        return self._todos(f"""
            SELECT COALESCE(g.nombre, 'General') AS etiqueta, COUNT(*) AS valor
            FROM comunicados c LEFT JOIN grupos g ON g.id = c.grupo_id
            WHERE {self.F_COMUNICADO}
            GROUP BY g.nombre, g.grado ORDER BY g.grado NULLS FIRST, g.nombre
        """, self._params(grupo_id, desde, hasta))

    def lectura_por_grupo(self, grupo_id=None, desde=None, hasta=None) -> list[dict]:
        return self._todos(f"""
            {self.LECTURA.format(filtro=self.F_COMUNICADO)}
            SELECT grupo AS etiqueta, ROUND(AVG(porcentaje), 1) AS valor
            FROM lectura GROUP BY grupo, grado ORDER BY grado NULLS FIRST, grupo
        """, self._params(grupo_id, desde, hasta))

    def comunicados_por_prioridad(self, grupo_id=None, desde=None, hasta=None) -> list[dict]:
        return self._todos(f"""
            SELECT INITCAP(c.prioridad) AS etiqueta, COUNT(*) AS valor
            FROM comunicados c WHERE {self.F_COMUNICADO}
            GROUP BY c.prioridad ORDER BY valor DESC
        """, self._params(grupo_id, desde, hasta))

    def citaciones_por_estado(self, grupo_id=None, desde=None, hasta=None) -> list[dict]:
        return self._todos(f"""
            SELECT INITCAP(ci.estado_citacion) AS etiqueta, COUNT(*) AS valor
            FROM citaciones ci JOIN estudiantes e ON e.id = ci.estudiante_id
            WHERE {self.F_CITACION}
            GROUP BY ci.estado_citacion ORDER BY valor DESC
        """, self._params(grupo_id, desde, hasta))

    def asistencia_citaciones(self, grupo_id=None, desde=None, hasta=None) -> list[dict]:
        return self._todos(f"""
            SELECT CASE WHEN a.asistio THEN 'Asistió' ELSE 'No asistió' END AS etiqueta, COUNT(*) AS valor
            FROM asistencia_citaciones a
            JOIN citaciones ci ON ci.id = a.citacion_id
            JOIN estudiantes e ON e.id = ci.estudiante_id
            WHERE a.estado = 'activo' AND {self.F_CITACION}
            GROUP BY a.asistio ORDER BY a.asistio DESC
        """, self._params(grupo_id, desde, hasta))

    def actividad_por_periodo(self, grupo_id=None, desde=None, hasta=None) -> dict:
        """Comunicados, mensajes y citaciones por semana (si caben en 12 semanas) o por mes."""
        datos = self._actividad("week", grupo_id, desde, hasta)
        if len(datos) > 12:
            return {"unidad": "mes", "periodos": self._actividad("month", grupo_id, desde, hasta)}
        return {"unidad": "semana", "periodos": datos}

    def _actividad(self, unidad: str, grupo_id, desde, hasta) -> list[dict]:
        p = {**self._params(grupo_id, desde, hasta), "u": unidad}
        return self._todos(f"""
            WITH eventos AS (
                SELECT date_trunc(%(u)s, c.fecha_publicacion) AS periodo, 'comunicados' AS tipo
                FROM comunicados c WHERE {self.F_COMUNICADO}
                UNION ALL
                SELECT date_trunc(%(u)s, m.fecha_envio), 'mensajes'
                FROM mensajes m WHERE {self.F_MENSAJE}
                UNION ALL
                SELECT date_trunc(%(u)s, ci.fecha_hora), 'citaciones'
                FROM citaciones ci JOIN estudiantes e ON e.id = ci.estudiante_id WHERE {self.F_CITACION}
            )
            SELECT to_char(periodo, 'YYYY-MM-DD') AS inicio,
                   COUNT(*) FILTER (WHERE tipo = 'comunicados') AS comunicados,
                   COUNT(*) FILTER (WHERE tipo = 'mensajes')    AS mensajes,
                   COUNT(*) FILTER (WHERE tipo = 'citaciones')  AS citaciones
            FROM eventos GROUP BY periodo ORDER BY periodo
        """, p)

    def grupos(self) -> list[dict]:
        """Grupos activos para el filtro (se muestra el nombre, el id solo viaja internamente)."""
        return self._todos("""
            SELECT id, nombre || ' · ' || CASE jornada WHEN 'manana' THEN 'Mañana'
                                                WHEN 'tarde' THEN 'Tarde' ELSE 'Única' END AS nombre
            FROM grupos WHERE estado = 'activo' ORDER BY grado, nombre
        """)

    def todo(self, grupo_id=None, desde=None, hasta=None) -> dict:
        f = (grupo_id, desde, hasta)
        return {
            "indicadores": self.indicadores(*f),
            "comunicados_por_grupo": self.comunicados_por_grupo(*f),
            "lectura_por_grupo": self.lectura_por_grupo(*f),
            "comunicados_por_prioridad": self.comunicados_por_prioridad(*f),
            "citaciones_por_estado": self.citaciones_por_estado(*f),
            "asistencia_citaciones": self.asistencia_citaciones(*f),
            "actividad": self.actividad_por_periodo(*f),
        }
