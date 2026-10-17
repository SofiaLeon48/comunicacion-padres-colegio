"""
Capa de modelos: UNA sola clase, `Modelos`, que agrupa todas las definiciones de datos del sistema.

Cada definición interna describe la forma de los datos que entran o salen de la API:
  - ...Crear       → lo que se pide al crear un registro
  - ...Actualizar  → lo que se puede editar (todo opcional)
  - ...Salida      → lo que la API responde

Nunca se piden datos automáticos (id, creado, modificado, estado, fechas de envío o publicación,
autor, remitente...): los asigna la base de datos o se toman del usuario que inició sesión.
El estado se cambia solo con los endpoints de desactivar / reactivar.

Uso en las rutas:  def crear_grupo(datos: Modelos.GrupoCrear): ...
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.core.config import a_hora_local

# Listas de valores permitidos (no son clases, solo tipos)
Estado = Literal["activo", "inactivo"]
NombreRol = Literal["coordinacion", "docente", "acudiente"]
Jornada = Literal["manana", "tarde", "unica"]
Prioridad = Literal["normal", "urgente"]
EstadoCitacion = Literal["pendiente", "confirmada", "cancelada", "realizada"]


class Modelos:
    """Todos los modelos de datos de Conecta Escolar."""

    # ------------------------------------------------------------------ comunes
    class Auditoria(BaseModel):
        """Campos de auditoría presentes en las 13 tablas (solo lectura)."""
        model_config = ConfigDict(from_attributes=True)
        creado: datetime
        modificado: datetime
        estado: Estado

    class Mensaje(BaseModel):
        """Respuesta simple con un texto."""
        mensaje: str

    # ------------------------------------------------------------------ usuarios
    class UsuarioCrear(BaseModel):
        nombre: str = Field(min_length=3, max_length=100, examples=["María Pérez"])
        correo: EmailStr = Field(examples=["maria.perez@correo.com"])
        password: str = Field(min_length=8, max_length=72, description="Se guarda cifrada con bcrypt")
        telefono: str | None = Field(default=None, max_length=20)
        rol_id: int

    class UsuarioActualizar(BaseModel):
        nombre: str | None = Field(default=None, min_length=3, max_length=100)
        correo: EmailStr | None = None
        password: str | None = Field(default=None, min_length=8, max_length=72)
        telefono: str | None = Field(default=None, max_length=20)
        rol_id: int | None = None

    class PerfilActualizar(BaseModel):
        """Lo que un usuario puede cambiar de sí mismo."""
        nombre: str | None = Field(default=None, min_length=3, max_length=100)
        telefono: str | None = Field(default=None, max_length=20)

    class CambioPassword(BaseModel):
        password_actual: str
        password_nueva: str = Field(min_length=8, max_length=72)

    class UsuarioSalida(Auditoria):
        """Nunca incluye password_hash."""
        id: int
        nombre: str
        correo: str
        telefono: str | None
        rol_id: int
        rol: NombreRol | str | None = None
        ultimo_acceso: datetime | None = None

    # ------------------------------------------------------------------ autenticación
    class LoginEntrada(BaseModel):
        correo: EmailStr = Field(examples=["coordinacion@colegio.edu.co"])
        password: str = Field(examples=["Colegio2026*"])
        rol: str = Field(description="Rol con el que se ingresa (debe coincidir con el del usuario)",
                         examples=["coordinacion"])

    class ModuloMenu(BaseModel):
        clave: str
        nombre: str
        descripcion: str | None
        ruta: str
        icono: str
        orden: int

    class Token(BaseModel):
        access_token: str
        token_type: str = "bearer"
        usuario: "Modelos.UsuarioSalida"
        modulos: list["Modelos.ModuloMenu"] = []

    class RolPublico(BaseModel):
        nombre: str
        descripcion: str | None

    # ------------------------------------------------------------------ roles
    class RolCrear(BaseModel):
        nombre: str = Field(min_length=3, max_length=30, examples=["docente"])
        descripcion: str | None = Field(default=None, max_length=150)

    class RolActualizar(BaseModel):
        nombre: str | None = Field(default=None, min_length=3, max_length=30)
        descripcion: str | None = Field(default=None, max_length=150)

    class RolSalida(Auditoria):
        id: int
        nombre: str
        descripcion: str | None

    # ------------------------------------------------------------------ grupos
    class GrupoCrear(BaseModel):
        nombre: str = Field(min_length=1, max_length=20, examples=["5A"])
        grado: int = Field(ge=0, le=11, examples=[5])
        jornada: Jornada = "manana"
        anio_lectivo: int | None = Field(default=None, ge=2000, le=2100,
                                         description="Vacío = año actual (lo pone la base de datos)")
        director_id: int | None = None

    class GrupoActualizar(BaseModel):
        nombre: str | None = Field(default=None, min_length=1, max_length=20)
        grado: int | None = Field(default=None, ge=0, le=11)
        jornada: Jornada | None = None
        anio_lectivo: int | None = Field(default=None, ge=2000, le=2100)
        director_id: int | None = None

    class GrupoSalida(Auditoria):
        id: int
        nombre: str
        grado: int
        jornada: str
        anio_lectivo: int
        director_id: int | None
        director_nombre: str | None = None
        total_estudiantes: int | None = None

    # ------------------------------------------------------------------ estudiantes
    class EstudianteCrear(BaseModel):
        nombre: str = Field(min_length=3, max_length=100, examples=["Juan Pérez"])
        documento: str = Field(min_length=4, max_length=20, examples=["1043000111"])
        grupo_id: int

    class EstudianteActualizar(BaseModel):
        nombre: str | None = Field(default=None, min_length=3, max_length=100)
        documento: str | None = Field(default=None, min_length=4, max_length=20)
        grupo_id: int | None = None

    class EstudianteSalida(Auditoria):
        id: int
        nombre: str
        documento: str
        grupo_id: int
        grupo_nombre: str | None = None
        grupo_jornada: str | None = None
        director_nombre: str | None = None
        acudientes: str | None = None

    class AcudienteDeEstudiante(BaseModel):
        id: int
        nombre: str
        correo: str
        telefono: str | None
        parentesco: str
        es_principal: bool

    # ------------------------------------------------------------------ acudiente ↔ estudiante
    class VinculoCrear(BaseModel):
        acudiente_id: int
        estudiante_id: int
        parentesco: str = Field(default="acudiente", max_length=30, examples=["madre"])
        es_principal: bool = False

    class VinculoActualizar(BaseModel):
        parentesco: str | None = Field(default=None, max_length=30)
        es_principal: bool | None = None

    class VinculoSalida(Auditoria):
        id: int
        acudiente_id: int
        estudiante_id: int
        parentesco: str
        es_principal: bool
        acudiente_nombre: str | None = None
        estudiante_nombre: str | None = None
        grupo_nombre: str | None = None

    # ------------------------------------------------------------------ comunicados
    class ComunicadoCrear(BaseModel):
        titulo: str = Field(min_length=3, max_length=150, examples=["Reunión de padres"])
        contenido: str = Field(min_length=1, examples=["Se cita a reunión general el viernes..."])
        grupo_id: int | None = Field(default=None, description="Vacío = circular para todo el colegio")
        prioridad: Prioridad = "normal"
        requiere_confirmacion: bool = True

    class ComunicadoActualizar(BaseModel):
        titulo: str | None = Field(default=None, min_length=3, max_length=150)
        contenido: str | None = Field(default=None, min_length=1)
        prioridad: Prioridad | None = None
        requiere_confirmacion: bool | None = None

    class ComunicadoSalida(Auditoria):
        id: int
        titulo: str
        contenido: str
        grupo_id: int | None
        grupo_nombre: str | None = None
        autor_id: int
        autor_nombre: str | None = None
        prioridad: str
        requiere_confirmacion: bool
        fecha_publicacion: datetime
        confirmado_por_mi: bool | None = None
        total_confirmados: int | None = None

    class ConfirmacionSalida(Auditoria):
        id: int
        comunicado_id: int
        usuario_id: int
        fecha_confirmacion: datetime

    class EstadoLecturaItem(BaseModel):
        usuario_id: int
        nombre: str
        correo: str
        confirmado: bool
        fecha_confirmacion: datetime | None

    class EstadoLectura(BaseModel):
        comunicado_id: int
        destinatarios: int
        confirmados: int
        porcentaje: float
        detalle: list["Modelos.EstadoLecturaItem"]

    # ------------------------------------------------------------------ mensajes
    class MensajeCrear(BaseModel):
        grupo_id: int | None = Field(default=None, description="Para el chat del grupo")
        destinatario_id: int | None = Field(default=None, description="Para un mensaje directo")
        contenido: str = Field(min_length=1, max_length=2000)

        @model_validator(mode="after")
        def un_solo_destino(self):
            if (self.grupo_id is None) == (self.destinatario_id is None):
                raise ValueError("Indica grupo_id (chat del grupo) o destinatario_id (directo), solo uno.")
            return self

    class MensajeEditar(BaseModel):
        contenido: str = Field(min_length=1, max_length=2000)

    class MensajeSalida(Auditoria):
        id: int
        remitente_id: int
        remitente_nombre: str | None = None
        remitente_rol: str | None = None
        grupo_id: int | None
        destinatario_id: int | None
        contenido: str
        leido: bool
        fecha_envio: datetime

    class Conversacion(BaseModel):
        contraparte_id: int
        contraparte_nombre: str
        contraparte_rol: str
        ultimo_mensaje: str
        fecha_envio: datetime
        no_leidos: int

    # ------------------------------------------------------------------ citaciones
    class CitacionCrear(BaseModel):
        estudiante_id: int
        acudiente_id: int | None = Field(default=None, description="Vacío = todos los acudientes del estudiante")
        motivo: str = Field(min_length=3, max_length=255, examples=["Seguimiento académico"])
        fecha_hora: datetime = Field(examples=["2026-10-20T07:30:00"])
        lugar: str | None = Field(default=None, max_length=100, examples=["Sala de profesores"])
        docente_id: int | None = Field(default=None,
                                       description="Solo coordinación: citar a nombre de otro docente")

        @field_validator("fecha_hora")
        @classmethod
        def _hora_local(cls, v):
            return a_hora_local(v)

    class CitacionActualizar(BaseModel):
        motivo: str | None = Field(default=None, min_length=3, max_length=255)
        fecha_hora: datetime | None = None
        lugar: str | None = Field(default=None, max_length=100)
        acudiente_id: int | None = None

        @field_validator("fecha_hora")
        @classmethod
        def _hora_local(cls, v):
            return a_hora_local(v)

    class CambioEstadoCitacion(BaseModel):
        estado_citacion: EstadoCitacion

    class CitacionSalida(Auditoria):
        id: int
        estudiante_id: int
        estudiante_nombre: str | None = None
        grupo_nombre: str | None = None
        docente_id: int
        docente_nombre: str | None = None
        acudiente_id: int | None
        acudiente_nombre: str | None = None
        motivo: str
        fecha_hora: datetime
        lugar: str | None
        estado_citacion: str
        asistio: bool | None = None
        observaciones: str | None = None

    class AsistenciaCrear(BaseModel):
        asistio: bool
        observaciones: str | None = None

    class AsistenciaActualizar(BaseModel):
        asistio: bool | None = None
        observaciones: str | None = None

    class AsistenciaSalida(Auditoria):
        id: int
        citacion_id: int
        asistio: bool
        observaciones: str | None
        registrado_por: int

    # ------------------------------------------------------------------ notificaciones
    class NotificacionCrear(BaseModel):
        """Aviso manual (tipo 'sistema') que envía coordinación."""
        titulo: str = Field(min_length=3, max_length=150)
        contenido: str = Field(min_length=1, max_length=255)
        usuario_ids: list[int] | None = Field(default=None, description="Destinatarios puntuales")
        roles: list[NombreRol] | None = Field(default=None, description="O todos los usuarios de estos roles")

    class NotificacionSalida(Auditoria):
        id: int
        usuario_id: int
        tipo: str
        titulo: str
        contenido: str
        referencia_id: int | None
        leido: bool
        enviado_correo: bool
        fecha: datetime

    class ContadorNoLeidas(BaseModel):
        no_leidas: int

    # ------------------------------------------------------------------ configuración (módulos y permisos)
    class ModuloCrear(BaseModel):
        clave: str = Field(min_length=3, max_length=30, pattern=r"^[a-z_]+$", examples=["eventos"])
        nombre: str = Field(min_length=3, max_length=50)
        descripcion: str | None = Field(default=None, max_length=150)
        ruta: str = Field(min_length=2, max_length=80, pattern=r"^/", examples=["/eventos"])
        icono: str = Field(default="bi-grid", max_length=40)
        orden: int = Field(default=0, ge=0, le=99)

    class ModuloActualizar(BaseModel):
        nombre: str | None = Field(default=None, min_length=3, max_length=50)
        descripcion: str | None = Field(default=None, max_length=150)
        ruta: str | None = Field(default=None, min_length=2, max_length=80, pattern=r"^/")
        icono: str | None = Field(default=None, max_length=40)
        orden: int | None = Field(default=None, ge=0, le=99)

    class ModuloSalida(Auditoria):
        id: int
        clave: str
        nombre: str
        descripcion: str | None
        ruta: str
        icono: str
        orden: int

    class PermisoItem(BaseModel):
        rol_id: int
        rol: str
        modulo_id: int
        clave: str
        modulo: str
        icono: str
        orden: int
        permitido: bool

    class PermisoCambio(BaseModel):
        rol_id: int
        modulo_id: int
        permitido: bool


# Las definiciones que mencionan a otras (Token, EstadoLectura) se completan aquí,
# cuando la clase Modelos ya existe.
Modelos.Token.model_rebuild()
Modelos.EstadoLectura.model_rebuild()
