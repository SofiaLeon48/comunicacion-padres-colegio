from app.repositories.base import BaseRepository

# Subconsulta reutilizable: acudientes destinatarios de un comunicado.
# Si curso_id es NULL (circular general) => todos los acudientes activos.
_DESTINATARIOS = """
    SELECT DISTINCT u.id, u.nombre, u.correo
    FROM usuarios u
    JOIN roles r ON r.id = u.rol_id AND r.nombre = 'acudiente'
    JOIN acudiente_estudiante ae ON ae.acudiente_id = u.id AND ae.estado = 'activo'
    JOIN estudiantes e ON e.id = ae.estudiante_id AND e.estado = 'activo'
    WHERE u.estado = 'activo'
      AND (%(curso_id)s::int IS NULL OR e.curso_id = %(curso_id)s::int)
"""


class ComunicadoRepository(BaseRepository):
    tabla = "comunicados"
    columnas = ["titulo", "contenido", "curso_id", "autor_id", "prioridad", "requiere_confirmacion"]
    orden = "fecha_publicacion"

    def listar_visibles(self, usuario_id: int, es_acudiente: bool, curso_id: int | None = None,
                        prioridad: str | None = None, incluir_inactivos: bool = False) -> list[dict]:
        """Comunicados con autor, curso y si el usuario actual ya confirmó lectura.
        Un acudiente solo ve los generales y los de los cursos de sus hijos."""
        condiciones = []
        valores: dict = {"uid": usuario_id}
        if not incluir_inactivos:
            condiciones.append("c.estado = 'activo'")
        if curso_id:
            condiciones.append("c.curso_id = %(curso_id)s")
            valores["curso_id"] = curso_id
        if prioridad:
            condiciones.append("c.prioridad = %(prioridad)s")
            valores["prioridad"] = prioridad
        if es_acudiente:
            condiciones.append("""(c.curso_id IS NULL OR c.curso_id IN (
                SELECT e.curso_id FROM estudiantes e
                JOIN acudiente_estudiante ae ON ae.estudiante_id = e.id
                WHERE ae.acudiente_id = %(uid)s AND ae.estado = 'activo' AND e.estado = 'activo'))""")
        where = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""
        return self._todos(f"""
            SELECT c.*, u.nombre AS autor_nombre, cu.nombre AS curso_nombre,
                   EXISTS (SELECT 1 FROM confirmaciones_lectura cl
                           WHERE cl.comunicado_id = c.id AND cl.usuario_id = %(uid)s
                             AND cl.estado = 'activo') AS confirmado_por_mi,
                   (SELECT COUNT(*) FROM confirmaciones_lectura cl
                     WHERE cl.comunicado_id = c.id AND cl.estado = 'activo') AS total_confirmados
            FROM comunicados c
            JOIN usuarios u ON u.id = c.autor_id
            LEFT JOIN cursos cu ON cu.id = c.curso_id
            {where}
            ORDER BY c.fecha_publicacion DESC
        """, valores)

    def obtener_detallado(self, comunicado_id: int, usuario_id: int) -> dict | None:
        return self._uno("""
            SELECT c.*, u.nombre AS autor_nombre, cu.nombre AS curso_nombre,
                   EXISTS (SELECT 1 FROM confirmaciones_lectura cl
                           WHERE cl.comunicado_id = c.id AND cl.usuario_id = %(uid)s
                             AND cl.estado = 'activo') AS confirmado_por_mi
            FROM comunicados c
            JOIN usuarios u ON u.id = c.autor_id
            LEFT JOIN cursos cu ON cu.id = c.curso_id
            WHERE c.id = %(id)s AND c.estado = 'activo'
        """, {"id": comunicado_id, "uid": usuario_id})

    def destinatarios(self, curso_id: int | None) -> list[dict]:
        return self._todos(_DESTINATARIOS, {"curso_id": curso_id})

    def es_destinatario(self, curso_id: int | None, acudiente_id: int) -> bool:
        return any(d["id"] == acudiente_id for d in self.destinatarios(curso_id))

    def estado_lectura(self, comunicado_id: int, curso_id: int | None) -> list[dict]:
        """Cada destinatario con su confirmación (o NULL si no ha leído)."""
        return self._todos(f"""
            SELECT d.id AS usuario_id, d.nombre, d.correo,
                   cl.fecha_confirmacion,
                   (cl.id IS NOT NULL) AS confirmado
            FROM ({_DESTINATARIOS}) d
            LEFT JOIN confirmaciones_lectura cl
                   ON cl.usuario_id = d.id AND cl.comunicado_id = %(comunicado_id)s
                  AND cl.estado = 'activo'
            ORDER BY confirmado, d.nombre
        """, {"curso_id": curso_id, "comunicado_id": comunicado_id})
