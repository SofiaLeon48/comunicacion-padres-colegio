from app.repositories.base import BaseRepository


class GrupoRepository(BaseRepository):
    tabla = "grupos"
    columnas = ["nombre", "grado", "jornada", "anio_lectivo", "director_id"]
    orden = "grado"

    def listar_detallado(self, acudiente_id: int | None = None, anio_lectivo: int | None = None,
                         incluir_inactivos: bool = False) -> list[dict]:
        """Grupos con el nombre del director y la cantidad de estudiantes.
        Si se pasa acudiente_id, solo los grupos donde ese acudiente tiene hijos."""
        condiciones, valores = [], []
        if not incluir_inactivos:
            condiciones.append("c.estado = 'activo'")
        if anio_lectivo:
            condiciones.append("c.anio_lectivo = %s")
            valores.append(anio_lectivo)
        if acudiente_id:
            condiciones.append("""c.id IN (
                SELECT e.grupo_id FROM estudiantes e
                JOIN acudiente_estudiante ae ON ae.estudiante_id = e.id
                WHERE ae.acudiente_id = %s AND ae.estado = 'activo' AND e.estado = 'activo')""")
            valores.append(acudiente_id)
        where = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""
        return self._todos(f"""
            SELECT c.*, u.nombre AS director_nombre,
                   (SELECT COUNT(*) FROM estudiantes e
                     WHERE e.grupo_id = c.id AND e.estado = 'activo') AS total_estudiantes
            FROM grupos c
            LEFT JOIN usuarios u ON u.id = c.director_id
            {where}
            ORDER BY c.grado, c.nombre
        """, valores)

    def ids_acudientes(self, grupo_id: int) -> list[int]:
        filas = self._todos("""
            SELECT DISTINCT ae.acudiente_id
            FROM acudiente_estudiante ae
            JOIN estudiantes e ON e.id = ae.estudiante_id
            WHERE e.grupo_id = %s AND e.estado = 'activo' AND ae.estado = 'activo'
        """, (grupo_id,))
        return [f["acudiente_id"] for f in filas]

    def ids_miembros(self, grupo_id: int) -> list[int]:
        """Acudientes del grupo + director de grupo (quienes reciben el chat en tiempo real)."""
        ids = set(self.ids_acudientes(grupo_id))
        grupo = self.obtener(grupo_id)
        if grupo and grupo["director_id"]:
            ids.add(grupo["director_id"])
        return list(ids)

    def acudiente_pertenece(self, grupo_id: int, acudiente_id: int) -> bool:
        return acudiente_id in self.ids_acudientes(grupo_id)
