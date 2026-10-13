-- =====================================================================
--  Comunicación Padres-Colegio en Tiempo Real
--  Esquema completo: 14 tablas · PostgreSQL (Neon)
--
--  Ejecutar en el SQL Editor de Neon, o con:  python -m scripts.init_db
--
--  Convenciones aplicadas a las 14 tablas (sin excepciones):
--    creado     -> fecha/hora de creación (la asigna la BD)
--    modificado -> fecha/hora de la última edición (la actualiza un TRIGGER)
--    estado     -> 'activo' / 'inactivo'  (borrado lógico)
--  Los estados "de negocio" usan otro nombre (p. ej. citaciones.estado_citacion)
--  para no mezclar su significado con el borrado lógico.
-- =====================================================================

DROP TABLE IF EXISTS rol_modulo             CASCADE;
DROP TABLE IF EXISTS modulos                CASCADE;
DROP TABLE IF EXISTS logs_actividad         CASCADE;
DROP TABLE IF EXISTS asistencia_citaciones  CASCADE;
DROP TABLE IF EXISTS citaciones             CASCADE;
DROP TABLE IF EXISTS notificaciones         CASCADE;
DROP TABLE IF EXISTS mensajes               CASCADE;
DROP TABLE IF EXISTS confirmaciones_lectura CASCADE;
DROP TABLE IF EXISTS comunicados            CASCADE;
DROP TABLE IF EXISTS acudiente_estudiante   CASCADE;
DROP TABLE IF EXISTS estudiantes            CASCADE;
DROP TABLE IF EXISTS cursos                 CASCADE;
DROP TABLE IF EXISTS usuarios               CASCADE;
DROP TABLE IF EXISTS roles                  CASCADE;
DROP FUNCTION IF EXISTS fn_actualizar_modificado() CASCADE;


-- ---------------------------------------------------------------------
-- Función de trigger: actualiza "modificado" en cada UPDATE
-- ---------------------------------------------------------------------
CREATE FUNCTION fn_actualizar_modificado() RETURNS TRIGGER AS $$
BEGIN
    NEW.modificado := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- =====================================================================
--  MÓDULO: USUARIOS Y ROLES
-- =====================================================================

-- 1. roles  — catálogo de tipos de usuario
CREATE TABLE roles (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(30)  NOT NULL UNIQUE,
    descripcion VARCHAR(150),
    creado      TIMESTAMP    NOT NULL DEFAULT NOW(),
    modificado  TIMESTAMP    NOT NULL DEFAULT NOW(),
    estado      VARCHAR(20)  NOT NULL DEFAULT 'activo'
                CONSTRAINT ck_roles_estado CHECK (estado IN ('activo', 'inactivo'))
);

-- 2. usuarios  — N:1 con roles
CREATE TABLE usuarios (
    id            SERIAL PRIMARY KEY,
    nombre        VARCHAR(100) NOT NULL,
    correo        VARCHAR(150) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,          -- bcrypt, nunca texto plano
    telefono      VARCHAR(20),
    rol_id        INTEGER      NOT NULL REFERENCES roles(id),
    ultimo_acceso TIMESTAMP,
    creado        TIMESTAMP    NOT NULL DEFAULT NOW(),
    modificado    TIMESTAMP    NOT NULL DEFAULT NOW(),
    estado        VARCHAR(20)  NOT NULL DEFAULT 'activo'
                  CONSTRAINT ck_usuarios_estado CHECK (estado IN ('activo', 'inactivo'))
);
-- Correo único sin importar mayúsculas/minúsculas
CREATE UNIQUE INDEX uq_usuarios_correo ON usuarios (LOWER(correo));

-- 13. modulos  — secciones del aplicativo web (alimentan el menú de navegación)
CREATE TABLE modulos (
    id          SERIAL PRIMARY KEY,
    clave       VARCHAR(30)  NOT NULL CONSTRAINT uq_modulos_clave UNIQUE,   -- identificador interno: 'comunicados'
    nombre      VARCHAR(50)  NOT NULL,                                       -- texto del menú: 'Comunicados'
    descripcion VARCHAR(150),
    ruta        VARCHAR(80)  NOT NULL,                                       -- ruta del frontend: '/comunicados'
    icono       VARCHAR(40)  NOT NULL DEFAULT 'bi-grid',                     -- Bootstrap Icons
    orden       SMALLINT     NOT NULL DEFAULT 0,
    creado      TIMESTAMP    NOT NULL DEFAULT NOW(),
    modificado  TIMESTAMP    NOT NULL DEFAULT NOW(),
    estado      VARCHAR(20)  NOT NULL DEFAULT 'activo'
                CONSTRAINT ck_modulos_estado CHECK (estado IN ('activo', 'inactivo'))
);

-- 14. rol_modulo  — tabla puente M:N (roles ↔ modulos): QUÉ módulos ve cada rol
CREATE TABLE rol_modulo (
    id         SERIAL PRIMARY KEY,
    rol_id     INTEGER     NOT NULL REFERENCES roles(id),
    modulo_id  INTEGER     NOT NULL REFERENCES modulos(id),
    creado     TIMESTAMP   NOT NULL DEFAULT NOW(),
    modificado TIMESTAMP   NOT NULL DEFAULT NOW(),
    estado     VARCHAR(20) NOT NULL DEFAULT 'activo'
               CONSTRAINT ck_rol_modulo_estado CHECK (estado IN ('activo', 'inactivo')),
    CONSTRAINT uq_rol_modulo UNIQUE (rol_id, modulo_id)
);


-- =====================================================================
--  MÓDULO: ADMINISTRACIÓN (estructura académica)
-- =====================================================================

-- 3. cursos  — N:1 con usuarios (director de grupo)
CREATE TABLE cursos (
    id           SERIAL PRIMARY KEY,
    nombre       VARCHAR(20)  NOT NULL,           -- ej. "5A"
    grado        SMALLINT     NOT NULL CONSTRAINT ck_cursos_grado CHECK (grado BETWEEN 0 AND 11),
    jornada      VARCHAR(20)  NOT NULL DEFAULT 'manana'
                 CONSTRAINT ck_cursos_jornada CHECK (jornada IN ('manana', 'tarde', 'unica')),
    anio_lectivo SMALLINT     NOT NULL DEFAULT EXTRACT(YEAR FROM NOW()),
    director_id  INTEGER      REFERENCES usuarios(id),
    creado       TIMESTAMP    NOT NULL DEFAULT NOW(),
    modificado   TIMESTAMP    NOT NULL DEFAULT NOW(),
    estado       VARCHAR(20)  NOT NULL DEFAULT 'activo'
                 CONSTRAINT ck_cursos_estado CHECK (estado IN ('activo', 'inactivo')),
    CONSTRAINT uq_cursos_nombre_jornada_anio UNIQUE (nombre, jornada, anio_lectivo)
);

-- 4. estudiantes  — N:1 con cursos
CREATE TABLE estudiantes (
    id         SERIAL PRIMARY KEY,
    nombre     VARCHAR(100) NOT NULL,
    documento  VARCHAR(20)  NOT NULL CONSTRAINT uq_estudiantes_documento UNIQUE,
    curso_id   INTEGER      NOT NULL REFERENCES cursos(id),
    creado     TIMESTAMP    NOT NULL DEFAULT NOW(),
    modificado TIMESTAMP    NOT NULL DEFAULT NOW(),
    estado     VARCHAR(20)  NOT NULL DEFAULT 'activo'
               CONSTRAINT ck_estudiantes_estado CHECK (estado IN ('activo', 'inactivo'))
);

-- 5. acudiente_estudiante  — tabla puente M:N (usuarios ↔ estudiantes)
CREATE TABLE acudiente_estudiante (
    id            SERIAL PRIMARY KEY,
    acudiente_id  INTEGER     NOT NULL REFERENCES usuarios(id),
    estudiante_id INTEGER     NOT NULL REFERENCES estudiantes(id),
    parentesco    VARCHAR(30) NOT NULL DEFAULT 'acudiente',   -- madre, padre, abuelo...
    es_principal  BOOLEAN     NOT NULL DEFAULT FALSE,
    creado        TIMESTAMP   NOT NULL DEFAULT NOW(),
    modificado    TIMESTAMP   NOT NULL DEFAULT NOW(),
    estado        VARCHAR(20) NOT NULL DEFAULT 'activo'
                  CONSTRAINT ck_acudiente_estudiante_estado CHECK (estado IN ('activo', 'inactivo')),
    -- El mismo acudiente no se vincula dos veces al mismo estudiante
    CONSTRAINT uq_acudiente_estudiante UNIQUE (acudiente_id, estudiante_id)
);


-- =====================================================================
--  MÓDULO: COMUNICADOS Y MENSAJERÍA (principal)
-- =====================================================================

-- 6. comunicados  — circulares digitales
--    curso_id NULL  => circular general (todo el colegio)
CREATE TABLE comunicados (
    id                    SERIAL PRIMARY KEY,
    titulo                VARCHAR(150) NOT NULL,
    contenido             TEXT         NOT NULL,
    curso_id              INTEGER      REFERENCES cursos(id),
    autor_id              INTEGER      NOT NULL REFERENCES usuarios(id),
    prioridad             VARCHAR(10)  NOT NULL DEFAULT 'normal'
                          CONSTRAINT ck_comunicados_prioridad CHECK (prioridad IN ('normal', 'urgente')),
    requiere_confirmacion BOOLEAN      NOT NULL DEFAULT TRUE,
    fecha_publicacion     TIMESTAMP    NOT NULL DEFAULT NOW(),
    creado                TIMESTAMP    NOT NULL DEFAULT NOW(),
    modificado            TIMESTAMP    NOT NULL DEFAULT NOW(),
    estado                VARCHAR(20)  NOT NULL DEFAULT 'activo'
                          CONSTRAINT ck_comunicados_estado CHECK (estado IN ('activo', 'inactivo'))
);

-- 7. confirmaciones_lectura  — quién leyó qué
CREATE TABLE confirmaciones_lectura (
    id                 SERIAL PRIMARY KEY,
    comunicado_id      INTEGER     NOT NULL REFERENCES comunicados(id),
    usuario_id         INTEGER     NOT NULL REFERENCES usuarios(id),
    fecha_confirmacion TIMESTAMP   NOT NULL DEFAULT NOW(),
    creado             TIMESTAMP   NOT NULL DEFAULT NOW(),
    modificado         TIMESTAMP   NOT NULL DEFAULT NOW(),
    estado             VARCHAR(20) NOT NULL DEFAULT 'activo'
                       CONSTRAINT ck_confirmaciones_estado CHECK (estado IN ('activo', 'inactivo')),
    -- Un usuario confirma cada comunicado una sola vez
    CONSTRAINT uq_confirmacion_por_usuario UNIQUE (comunicado_id, usuario_id)
);

-- 8. mensajes  — chat por curso  O  mensaje directo entre dos usuarios
--    Exactamente uno de (curso_id, destinatario_id) debe tener valor.
CREATE TABLE mensajes (
    id              SERIAL PRIMARY KEY,
    remitente_id    INTEGER     NOT NULL REFERENCES usuarios(id),
    curso_id        INTEGER     REFERENCES cursos(id),
    destinatario_id INTEGER     REFERENCES usuarios(id),
    contenido       TEXT        NOT NULL,
    leido           BOOLEAN     NOT NULL DEFAULT FALSE,     -- aplica a mensajes directos
    fecha_envio     TIMESTAMP   NOT NULL DEFAULT NOW(),
    creado          TIMESTAMP   NOT NULL DEFAULT NOW(),
    modificado      TIMESTAMP   NOT NULL DEFAULT NOW(),
    estado          VARCHAR(20) NOT NULL DEFAULT 'activo'
                    CONSTRAINT ck_mensajes_estado CHECK (estado IN ('activo', 'inactivo')),
    CONSTRAINT ck_mensajes_destino CHECK (
        (curso_id IS NOT NULL AND destinatario_id IS NULL) OR
        (curso_id IS NULL     AND destinatario_id IS NOT NULL)
    ),
    CONSTRAINT ck_mensajes_no_a_si_mismo CHECK (destinatario_id IS NULL OR destinatario_id <> remitente_id)
);

-- 9. citaciones  — calendario de citas a padres
CREATE TABLE citaciones (
    id              SERIAL PRIMARY KEY,
    estudiante_id   INTEGER      NOT NULL REFERENCES estudiantes(id),
    docente_id      INTEGER      NOT NULL REFERENCES usuarios(id),
    acudiente_id    INTEGER      REFERENCES usuarios(id),     -- NULL = todos los acudientes del estudiante
    motivo          VARCHAR(255) NOT NULL,
    fecha_hora      TIMESTAMP    NOT NULL,
    lugar           VARCHAR(100),
    estado_citacion VARCHAR(20)  NOT NULL DEFAULT 'pendiente'
                    CONSTRAINT ck_citaciones_estado_citacion
                    CHECK (estado_citacion IN ('pendiente', 'confirmada', 'cancelada', 'realizada')),
    creado          TIMESTAMP    NOT NULL DEFAULT NOW(),
    modificado      TIMESTAMP    NOT NULL DEFAULT NOW(),
    estado          VARCHAR(20)  NOT NULL DEFAULT 'activo'
                    CONSTRAINT ck_citaciones_estado CHECK (estado IN ('activo', 'inactivo'))
);

-- 10. asistencia_citaciones  — resultado de la cita (relación 1:1)
CREATE TABLE asistencia_citaciones (
    id             SERIAL PRIMARY KEY,
    citacion_id    INTEGER     NOT NULL REFERENCES citaciones(id),
    asistio        BOOLEAN     NOT NULL,
    observaciones  TEXT,
    registrado_por INTEGER     NOT NULL REFERENCES usuarios(id),
    creado         TIMESTAMP   NOT NULL DEFAULT NOW(),
    modificado     TIMESTAMP   NOT NULL DEFAULT NOW(),
    estado         VARCHAR(20) NOT NULL DEFAULT 'activo'
                   CONSTRAINT ck_asistencia_estado CHECK (estado IN ('activo', 'inactivo')),
    -- UNIQUE es lo que convierte la relación en 1:1 real
    CONSTRAINT uq_asistencia_por_citacion UNIQUE (citacion_id)
);


-- =====================================================================
--  MÓDULO: NOTIFICACIONES
-- =====================================================================

-- 11. notificaciones  — avisos dentro de la plataforma (+ correo opcional)
CREATE TABLE notificaciones (
    id             SERIAL PRIMARY KEY,
    usuario_id     INTEGER      NOT NULL REFERENCES usuarios(id),
    tipo           VARCHAR(20)  NOT NULL
                   CONSTRAINT ck_notificaciones_tipo CHECK (tipo IN ('comunicado', 'mensaje', 'citacion', 'sistema')),
    titulo         VARCHAR(150) NOT NULL,
    contenido      VARCHAR(255) NOT NULL,
    referencia_id  INTEGER,                         -- id del comunicado/mensaje/citación de origen
    leido          BOOLEAN      NOT NULL DEFAULT FALSE,
    enviado_correo BOOLEAN      NOT NULL DEFAULT FALSE,
    fecha          TIMESTAMP    NOT NULL DEFAULT NOW(),
    creado         TIMESTAMP    NOT NULL DEFAULT NOW(),
    modificado     TIMESTAMP    NOT NULL DEFAULT NOW(),
    estado         VARCHAR(20)  NOT NULL DEFAULT 'activo'
                   CONSTRAINT ck_notificaciones_estado CHECK (estado IN ('activo', 'inactivo'))
);


-- =====================================================================
--  MÓDULO: REPORTES Y ANALÍTICA
-- =====================================================================

-- 12. logs_actividad  — auditoría de acciones (la API la llena sola)
CREATE TABLE logs_actividad (
    id         SERIAL PRIMARY KEY,
    usuario_id INTEGER      REFERENCES usuarios(id),   -- NULL = acción del sistema
    accion     VARCHAR(50)  NOT NULL,                  -- crear, actualizar, eliminar, login...
    entidad    VARCHAR(50)  NOT NULL,                  -- tabla afectada
    entidad_id INTEGER,
    detalle    VARCHAR(255),
    fecha      TIMESTAMP    NOT NULL DEFAULT NOW(),
    creado     TIMESTAMP    NOT NULL DEFAULT NOW(),
    modificado TIMESTAMP    NOT NULL DEFAULT NOW(),
    estado     VARCHAR(20)  NOT NULL DEFAULT 'activo'
               CONSTRAINT ck_logs_estado CHECK (estado IN ('activo', 'inactivo'))
);


-- =====================================================================
--  Triggers "modificado" para las 14 tablas
-- =====================================================================
DO $$
DECLARE t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'roles', 'usuarios', 'cursos', 'estudiantes', 'acudiente_estudiante',
        'comunicados', 'confirmaciones_lectura', 'mensajes', 'notificaciones',
        'citaciones', 'asistencia_citaciones', 'logs_actividad', 'modulos', 'rol_modulo'
    ] LOOP
        EXECUTE format(
            'CREATE TRIGGER trg_%1$s_modificado BEFORE UPDATE ON %1$I
             FOR EACH ROW EXECUTE FUNCTION fn_actualizar_modificado();', t);
    END LOOP;
END $$;


-- =====================================================================
--  Índices sobre llaves foráneas y columnas de búsqueda frecuente
-- =====================================================================
CREATE INDEX ix_usuarios_rol            ON usuarios (rol_id);
CREATE INDEX ix_estudiantes_curso       ON estudiantes (curso_id);
CREATE INDEX ix_acud_est_estudiante     ON acudiente_estudiante (estudiante_id);
CREATE INDEX ix_comunicados_curso       ON comunicados (curso_id);
CREATE INDEX ix_comunicados_fecha       ON comunicados (fecha_publicacion DESC);
CREATE INDEX ix_confirmaciones_usuario  ON confirmaciones_lectura (usuario_id);
CREATE INDEX ix_mensajes_curso          ON mensajes (curso_id, fecha_envio);
CREATE INDEX ix_mensajes_directos       ON mensajes (remitente_id, destinatario_id);
CREATE INDEX ix_notificaciones_usuario  ON notificaciones (usuario_id, leido);
CREATE INDEX ix_citaciones_fecha        ON citaciones (fecha_hora);
CREATE INDEX ix_citaciones_estudiante   ON citaciones (estudiante_id);
CREATE INDEX ix_logs_fecha              ON logs_actividad (fecha DESC);


-- =====================================================================
--  Datos base: 3 roles, 9 módulos y permisos (rol x módulo)
-- =====================================================================
INSERT INTO roles (nombre, descripcion) VALUES
    ('coordinacion', 'Coordinación: administra la plataforma y la comunicación institucional'),
    ('docente',      'Docente o director de grupo'),
    ('acudiente',    'Padre, madre o acudiente de un estudiante');

INSERT INTO modulos (clave, nombre, descripcion, ruta, icono, orden) VALUES
    ('inicio',        'Inicio',        'Resumen personalizado según el rol',            '/inicio',        'bi-house-door',     1),
    ('comunicados',   'Comunicados',   'Circulares digitales y confirmación de lectura','/comunicados',   'bi-megaphone',      2),
    ('mensajes',      'Mensajería',    'Chat por curso y mensajes directos',            '/mensajes',      'bi-chat-dots',      3),
    ('citaciones',    'Citaciones',    'Calendario de citaciones a padres',             '/citaciones',    'bi-calendar-event', 4),
    ('estudiantes',   'Estudiantes',   'Estudiantes y sus acudientes',                  '/estudiantes',   'bi-mortarboard',    5),
    ('cursos',        'Cursos',        'Grupos, jornadas y directores de grupo',        '/cursos',        'bi-easel',          6),
    ('usuarios',      'Usuarios',      'Cuentas de acceso a la plataforma',             '/usuarios',      'bi-people',         7),
    ('reportes',      'Reportes',      'Indicadores, lectura de circulares y auditoría','/reportes',      'bi-bar-chart-line', 8),
    ('configuracion', 'Configuración', 'Roles, módulos y permisos',                     '/configuracion', 'bi-gear',           9);

-- Matriz de permisos
INSERT INTO rol_modulo (rol_id, modulo_id)
SELECT r.id, m.id FROM roles r JOIN modulos m ON
    (r.nombre = 'coordinacion')
 OR (r.nombre = 'docente'   AND m.clave IN ('inicio','comunicados','mensajes','citaciones','estudiantes','cursos','reportes'))
 OR (r.nombre = 'acudiente' AND m.clave IN ('inicio','comunicados','mensajes','citaciones','estudiantes'));

-- =====================================================================
--  Zona horaria de la base de datos (Neon usa UTC por defecto).
--  Así NOW() y las fechas quedan en hora de Colombia.
-- =====================================================================
DO $$ BEGIN
    EXECUTE format('ALTER DATABASE %I SET timezone TO %L', current_database(), 'America/Bogota');
END $$;
SET timezone TO 'America/Bogota';

-- Verificación: deben aparecer las 14 tablas
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
ORDER BY table_name;
