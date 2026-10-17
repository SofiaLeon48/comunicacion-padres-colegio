from app.repositories.base import BaseRepository


class AcudienteEstudianteRepository(BaseRepository):
    tabla = "acudiente_estudiante"
    columnas = ["acudiente_id", "estudiante_id", "parentesco", "es_principal"]

    def listar_detallado(self, acudiente_id: int | None = None, estudiante_id: int | None = None,
                         incluir_inactivos: bool = False) -> list[dict]:
        condiciones, valores = [], []
        if not incluir_inactivos:
            condiciones.append("ae.estado = 'activo'")
        if acudiente_id:
            condiciones.append("ae.acudiente_id = %s")
            valores.append(acudiente_id)
        if estudiante_id:
            condiciones.append("ae.estudiante_id = %s")
            valores.append(estudiante_id)
        where = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""
        return self._todos(f"""
            SELECT ae.*, u.nombre AS acudiente_nombre, e.nombre AS estudiante_nombre,
                   c.nombre AS grupo_nombre
            FROM acudiente_estudiante ae
            JOIN usuarios u    ON u.id = ae.acudiente_id
            JOIN estudiantes e ON e.id = ae.estudiante_id
            JOIN grupos c      ON c.id = e.grupo_id
            {where}
            ORDER BY e.nombre, u.nombre
        """, valores)
