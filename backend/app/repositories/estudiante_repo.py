from app.repositories.base import BaseRepository


class EstudianteRepository(BaseRepository):
    tabla = "estudiantes"
    columnas = ["nombre", "documento", "curso_id"]
    orden = "nombre"

    def listar_detallado(self, curso_id: int | None = None, acudiente_id: int | None = None,
                         buscar: str | None = None, incluir_inactivos: bool = False) -> list[dict]:
        condiciones, valores = [], []
        if not incluir_inactivos:
            condiciones.append("e.estado = 'activo'")
        if curso_id:
            condiciones.append("e.curso_id = %s")
            valores.append(curso_id)
        if acudiente_id:
            condiciones.append("""e.id IN (SELECT estudiante_id FROM acudiente_estudiante
                                  WHERE acudiente_id = %s AND estado = 'activo')""")
            valores.append(acudiente_id)
        if buscar:
            condiciones.append("(e.nombre ILIKE %s OR e.documento ILIKE %s)")
            valores += [f"%{buscar}%", f"%{buscar}%"]
        where = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""
        return self._todos(f"""
            SELECT e.*, c.nombre AS curso_nombre
            FROM estudiantes e
            JOIN cursos c ON c.id = e.curso_id
            {where}
            ORDER BY e.nombre
        """, valores)

    def acudientes(self, estudiante_id: int) -> list[dict]:
        return self._todos("""
            SELECT u.id, u.nombre, u.correo, u.telefono, ae.parentesco, ae.es_principal
            FROM acudiente_estudiante ae
            JOIN usuarios u ON u.id = ae.acudiente_id
            WHERE ae.estudiante_id = %s AND ae.estado = 'activo' AND u.estado = 'activo'
            ORDER BY ae.es_principal DESC, u.nombre
        """, (estudiante_id,))

    def es_acudiente_de(self, acudiente_id: int, estudiante_id: int) -> bool:
        return self._uno("""
            SELECT 1 FROM acudiente_estudiante
            WHERE acudiente_id = %s AND estudiante_id = %s AND estado = 'activo'
        """, (acudiente_id, estudiante_id)) is not None
