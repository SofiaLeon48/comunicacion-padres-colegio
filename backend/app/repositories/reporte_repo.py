"""
Reportes y Analítica: consultas de solo lectura que agregan datos de varias
tablas. No necesitan tablas propias: se calculan en vivo con SQL.
"""
from app.repositories.base import BaseRepository


class ReporteRepository(BaseRepository):

    def resumen_general(self) -> dict:
        return self._uno("""
            SELECT
              (SELECT COUNT(*) FROM usuarios    WHERE estado = 'activo') AS usuarios_activos,
              (SELECT COUNT(*) FROM grupos      WHERE estado = 'activo') AS grupos,
              (SELECT COUNT(*) FROM estudiantes WHERE estado = 'activo') AS estudiantes,
              (SELECT COUNT(*) FROM comunicados WHERE estado = 'activo') AS comunicados,
              (SELECT COUNT(*) FROM mensajes    WHERE estado = 'activo') AS mensajes,
              (SELECT COUNT(*) FROM citaciones  WHERE estado = 'activo'
                  AND estado_citacion IN ('pendiente', 'confirmada')
                  AND fecha_hora >= NOW())                               AS citaciones_proximas,
              (SELECT COUNT(*) FROM notificaciones WHERE estado = 'activo' AND NOT leido)
                                                                         AS notificaciones_sin_leer
        """)

    def usuarios_por_rol(self) -> list[dict]:
        return self._todos("""
            SELECT r.nombre AS rol, COUNT(u.id) AS total
            FROM roles r
            LEFT JOIN usuarios u ON u.rol_id = r.id AND u.estado = 'activo'
            GROUP BY r.nombre ORDER BY total DESC
        """)

    def lectura_comunicados(self, grupo_id: int | None = None) -> list[dict]:
        """Por cada comunicado que exige confirmación: destinatarios, confirmados y %."""
        filtro = "AND c.grupo_id = %(grupo_id)s" if grupo_id else ""
        return self._todos(f"""
            WITH destinatarios AS (
                SELECT c.id AS comunicado_id, COUNT(DISTINCT ae.acudiente_id) AS total
                FROM comunicados c
                JOIN estudiantes e ON (c.grupo_id IS NULL OR e.grupo_id = c.grupo_id)
                                  AND e.estado = 'activo'
                JOIN acudiente_estudiante ae ON ae.estudiante_id = e.id AND ae.estado = 'activo'
                GROUP BY c.id
            ),
            confirmados AS (
                SELECT comunicado_id, COUNT(*) AS total
                FROM confirmaciones_lectura WHERE estado = 'activo'
                GROUP BY comunicado_id
            )
            SELECT c.id, c.titulo, c.prioridad, c.fecha_publicacion,
                   COALESCE(cu.nombre, 'General') AS grupo,
                   COALESCE(d.total, 0)  AS destinatarios,
                   COALESCE(cf.total, 0) AS confirmados,
                   CASE WHEN COALESCE(d.total, 0) = 0 THEN 0
                        ELSE ROUND(100.0 * COALESCE(cf.total, 0) / d.total, 1) END AS porcentaje_lectura
            FROM comunicados c
            LEFT JOIN grupos cu        ON cu.id = c.grupo_id
            LEFT JOIN destinatarios d  ON d.comunicado_id = c.id
            LEFT JOIN confirmados cf   ON cf.comunicado_id = c.id
            WHERE c.estado = 'activo' AND c.requiere_confirmacion {filtro}
            ORDER BY c.fecha_publicacion DESC
        """, {"grupo_id": grupo_id})

    def citaciones_por_estado(self) -> list[dict]:
        return self._todos("""
            SELECT estado_citacion, COUNT(*) AS total
            FROM citaciones WHERE estado = 'activo'
            GROUP BY estado_citacion ORDER BY total DESC
        """)

    def asistencia_citaciones(self) -> dict:
        return self._uno("""
            SELECT COUNT(*)                                   AS registradas,
                   COUNT(*) FILTER (WHERE asistio)            AS asistieron,
                   COUNT(*) FILTER (WHERE NOT asistio)        AS no_asistieron,
                   CASE WHEN COUNT(*) = 0 THEN 0
                        ELSE ROUND(100.0 * COUNT(*) FILTER (WHERE asistio) / COUNT(*), 1)
                   END                                        AS porcentaje_asistencia
            FROM asistencia_citaciones WHERE estado = 'activo'
        """)

    def actividad_por_grupo(self) -> list[dict]:
        return self._todos("""
            SELECT c.id, c.nombre AS grupo,
                   (SELECT COUNT(*) FROM estudiantes e WHERE e.grupo_id = c.id AND e.estado = 'activo')
                       AS estudiantes,
                   (SELECT COUNT(*) FROM comunicados co WHERE co.grupo_id = c.id AND co.estado = 'activo')
                       AS comunicados,
                   (SELECT COUNT(*) FROM mensajes m WHERE m.grupo_id = c.id AND m.estado = 'activo')
                       AS mensajes,
                   (SELECT COUNT(*) FROM citaciones ci JOIN estudiantes e ON e.id = ci.estudiante_id
                     WHERE e.grupo_id = c.id AND ci.estado = 'activo') AS citaciones
            FROM grupos c WHERE c.estado = 'activo'
            ORDER BY c.grado, c.nombre
        """)

    def acudientes_sin_leer(self, limite: int = 20) -> list[dict]:
        """Acudientes con más comunicados pendientes por confirmar."""
        return self._todos("""
            WITH pendientes AS (
                SELECT DISTINCT ae.acudiente_id, c.id AS comunicado_id
                FROM comunicados c
                JOIN estudiantes e ON (c.grupo_id IS NULL OR e.grupo_id = c.grupo_id) AND e.estado = 'activo'
                JOIN acudiente_estudiante ae ON ae.estudiante_id = e.id AND ae.estado = 'activo'
                WHERE c.estado = 'activo' AND c.requiere_confirmacion
                  AND NOT EXISTS (SELECT 1 FROM confirmaciones_lectura cl
                                  WHERE cl.comunicado_id = c.id AND cl.usuario_id = ae.acudiente_id
                                    AND cl.estado = 'activo')
            )
            SELECT u.id, u.nombre, u.correo, u.telefono, COUNT(*) AS pendientes
            FROM pendientes p JOIN usuarios u ON u.id = p.acudiente_id
            WHERE u.estado = 'activo'
            GROUP BY u.id ORDER BY pendientes DESC, u.nombre
            LIMIT %s
        """, (limite,))

    # ------------------------------------------------------------------
    # Reportes exportables (PDF / Excel). Sin IDs: solo datos legibles.
    # Filtros comunes: rango de fechas, grupo y estado/prioridad.
    # ------------------------------------------------------------------
    def reporte_comunicados(self, desde=None, hasta=None, grupo_id=None, prioridad=None) -> list[dict]:
        """Comunicados + grupos + usuarios (autor) + confirmaciones + acudientes destinatarios."""
        return self._todos("""
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
            )
            SELECT c.fecha_publicacion                       AS fecha,
                   c.titulo,
                   COALESCE(g.nombre, 'Todos los grupos')    AS grupo,
                   u.nombre                                  AS autor,
                   INITCAP(c.prioridad)                      AS prioridad,
                   COALESCE(d.total, 0)                      AS destinatarios,
                   COALESCE(cf.total, 0)                     AS confirmados,
                   CASE WHEN NOT c.requiere_confirmacion OR COALESCE(d.total, 0) = 0 THEN NULL
                        ELSE ROUND(100.0 * COALESCE(cf.total, 0) / d.total, 1) END AS lectura
            FROM comunicados c
            JOIN usuarios u           ON u.id = c.autor_id
            LEFT JOIN grupos g        ON g.id = c.grupo_id
            LEFT JOIN destinatarios d ON d.id = c.id
            LEFT JOIN confirmados cf  ON cf.id = c.id
            WHERE c.estado = 'activo'
              AND (%(d)s::date IS NULL OR c.fecha_publicacion::date >= %(d)s)
              AND (%(h)s::date IS NULL OR c.fecha_publicacion::date <= %(h)s)
              AND (%(g)s::int  IS NULL OR c.grupo_id = %(g)s)
              AND (%(e)s::text IS NULL OR c.prioridad = %(e)s)
            ORDER BY c.fecha_publicacion DESC
        """, {"d": desde, "h": hasta, "g": grupo_id, "e": prioridad})

    def reporte_citaciones(self, desde=None, hasta=None, grupo_id=None, estado=None) -> list[dict]:
        """Citaciones + estudiantes + grupos + usuarios (docente y acudiente) + asistencia."""
        return self._todos("""
            SELECT ci.fecha_hora                                    AS fecha,
                   e.nombre                                         AS estudiante,
                   g.nombre                                         AS grupo,
                   d.nombre                                         AS docente,
                   COALESCE(a.nombre, 'Todos los acudientes')       AS acudiente,
                   ci.motivo,
                   COALESCE(ci.lugar, '—')                          AS lugar,
                   INITCAP(ci.estado_citacion)                      AS estado,
                   CASE WHEN asi.id IS NULL THEN 'Sin registrar'
                        WHEN asi.asistio THEN 'Asistió' ELSE 'No asistió' END AS asistencia
            FROM citaciones ci
            JOIN estudiantes e ON e.id = ci.estudiante_id
            JOIN grupos g      ON g.id = e.grupo_id
            JOIN usuarios d    ON d.id = ci.docente_id
            LEFT JOIN usuarios a ON a.id = ci.acudiente_id
            LEFT JOIN asistencia_citaciones asi ON asi.citacion_id = ci.id AND asi.estado = 'activo'
            WHERE ci.estado = 'activo'
              AND (%(d)s::date IS NULL OR ci.fecha_hora::date >= %(d)s)
              AND (%(h)s::date IS NULL OR ci.fecha_hora::date <= %(h)s)
              AND (%(g)s::int  IS NULL OR e.grupo_id = %(g)s)
              AND (%(e)s::text IS NULL OR ci.estado_citacion = %(e)s)
            ORDER BY ci.fecha_hora DESC
        """, {"d": desde, "h": hasta, "g": grupo_id, "e": estado})

    def nombre_grupo(self, grupo_id: int) -> str | None:
        fila = self._uno("SELECT nombre FROM grupos WHERE id = %s", (grupo_id,))
        return fila["nombre"] if fila else None
