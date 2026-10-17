# Backend · API de Conecta Escolar

API REST con **FastAPI + PostgreSQL (Neon)**. Hace cuatro cosas principales:
- Publica circulares digitales, con confirmación de lectura.
- Ofrece mensajería, tanto el chat de cada grupo como mensajes directos.
- Lleva el calendario de citaciones a padres.
- Envía notificaciones en tiempo real (WebSocket) y genera reportes.

---

## 1. Puesta en marcha

### Requisitos
- Python 3.11 o superior.
- Una base de datos en [Neon](https://neon.tech) (gratis).

### Pasos

```bash
cd backend

# 1. Entorno virtual
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS / Linux

# 2. Dependencias
pip install -r requirements.txt

# 3. Variables de entorno
copy .env.example .env         # Windows   (cp en macOS/Linux)
#    → abre .env y pega tu DATABASE_URL de Neon y una JWT_SECRET

# 4. Crear las 13 tablas (o pega database/schema.sql en el SQL Editor de Neon)
python -m scripts.init_db

# 5. Cargar datos de prueba
python -m scripts.seed

# 6. Encender la API
uvicorn main:app --reload
```

Cuando la API esté encendida, abre **http://127.0.0.1:8000/docs** para usar Swagger. Ahí haces clic en **Authorize**, inicias sesión con uno de los usuarios de prueba y ya puedes probar cualquier endpoint.

### Usuarios de prueba

Todos usan la contraseña `Colegio2026*`. Al iniciar sesión se elige también el rol.

| Rol | Correo | Notas |
|---|---|---|
| coordinacion | coordinacion@colegio.edu.co | Administra la plataforma (9 módulos) |
| docente | lmartinez@colegio.edu.co | Director del 5A |
| docente | cgomez@colegio.edu.co | Directora del 6B |
| acudiente | maria.rodriguez@correo.com | Hijos en 5A y 6B |
| acudiente | jorge.perez@correo.com | Hijo en 5A |

Hay 16 usuarios, 5 grupos, 14 estudiantes, 9 circulares, mensajes y 9 citaciones de ejemplo (ver `scripts/seed.py`).

---

## 2. Módulos y tablas

Son 13 tablas. Todas tienen los mismos campos de auditoría: `creado`, `modificado` y `estado`.

| Módulo | Tablas | Qué resuelve |
|---|---|---|
| **Usuarios y Roles** | `roles`, `usuarios` | Login con rol, perfil |
| **Configuración** | `modulos`, `rol_modulo` | Qué módulos (menú) ve cada rol — se edita desde el frontend |
| **Administración** | `grupos`, `estudiantes`, `acudiente_estudiante` | Estructura académica y quién es acudiente de quién |
| **Comunicados y Mensajería** *(principal)* | `comunicados`, `confirmaciones_lectura`, `mensajes`, `citaciones`, `asistencia_citaciones` | Circulares, lectura, chat, calendario de citas |
| **Notificaciones** | `notificaciones` | Avisos en la plataforma, en tiempo real y opcionalmente por correo |
| **Reportes y Analítica** | consultas SQL agregadas sobre las tablas anteriores | Indicadores, % de lectura, asistencia, actividad por grupo |

El diagrama entidad-relación está en [`../docs/diagrama_er.dbml`](../docs/diagrama_er.dbml): se pega en [dbdiagram.io](https://dbdiagram.io/d) para verlo y exportarlo.

**Relaciones destacadas**
- **M:N** `roles ↔ modulos` mediante `rol_modulo`: el menú del frontend y los permisos de la API salen de esta tabla.
- **M:N** `usuarios ↔ estudiantes` mediante `acudiente_estudiante`. Un padre puede tener varios hijos y un hijo varios acudientes.
- **1:1** `citaciones ↔ asistencia_citaciones`. La restricción `UNIQUE (citacion_id)` es la que lo garantiza.
- **Opcionales con significado**:
  - `comunicados.grupo_id = NULL` es una circular general.
  - `citaciones.acudiente_id = NULL` cita a todos los acudientes del estudiante.
  - En `mensajes` debe ir `grupo_id` (chat del grupo) **o** `destinatario_id` (mensaje directo), nunca los dos. Lo controla un `CHECK`.

**Reglas que la propia base de datos obliga a cumplir**
- `UNIQUE`:
  - correo, sin importar mayúsculas;
  - documento del estudiante;
  - el mismo vínculo acudiente-estudiante;
  - una confirmación por usuario y comunicado;
  - una asistencia por citación.
- `CHECK` en jornada, grado, prioridad, tipo de notificación, estado de la citación y `estado`.
- Un **trigger** actualiza `modificado` en cada `UPDATE`, sin depender de la API.
- Índices en las llaves foráneas y en las fechas.
- La base queda configurada en hora de Colombia, porque Neon usa UTC por defecto.

---

## 3. Arquitectura por capas

```
backend/
├── main.py                  → crea la app, CORS, manejadores de error y monta los routers
├── database/schema.sql      → las 13 tablas, restricciones, triggers e índices
├── scripts/                 → init_db.py (crea tablas) · seed.py (datos de prueba)
├── tests/                   → 63 pruebas automatizadas contra PostgreSQL real
└── app/
    ├── core/                → Capa 1: configuración y conexión
    │   ├── config.py           variables del .env
    │   ├── database.py         pool de conexiones + get_cursor() (commit/rollback)
    │   ├── security.py         bcrypt + JWT
    │   ├── deps.py             usuario_actual, requiere_roles(...)
    │   └── errores.py          errores de PostgreSQL → HTTP 400/404/409/503
    ├── models/              → Capa 2: validación (Pydantic)
    │   └── modelos.py          UNA sola clase `Modelos` con todas las definiciones (Crear / Actualizar / Salida)
    ├── repositories/        → Capa 3: SQL (patrón Repository)
    │   └── base.py             CRUD genérico heredado por los 12 repositories
    ├── services/            → Capa 4: lógica de negocio compartida
    │   ├── notificador.py      guarda la notificación + WebSocket + correo
    │   ├── tiempo_real.py      gestor de conexiones WebSocket
    │   └── correo.py           SMTP opcional
    └── api/                 → Capa 5: endpoints HTTP (un router por recurso)
```

Así viaja una petición:

**Swagger/Svelte → `api/` (permisos) → `models/` (valida, o responde 422) → `repositories/` (SQL) → Neon**

Y de regreso: **`services/` notifica → respuesta JSON.**

Los datos automáticos (id, `creado`, `modificado`, `estado`, fechas de publicación o envío, autor, remitente) **nunca se piden**: los pone la base de datos o se toman del usuario que inició sesión. Si alguien los envía, la API los ignora. El `estado` solo cambia con los endpoints de desactivar (`DELETE`) y reactivar.

---

## 4. Endpoints principales

Hay más de 80 endpoints. Todos aparecen en `/docs`.

| Módulo | Endpoints destacados |
|---|---|
| Autenticación | `GET /auth/roles` · `POST /auth/login` (correo + contraseña + rol) · `GET /auth/mis-modulos` · `GET/PATCH /auth/me` · `PUT /auth/me/password` |
| Inicio | `GET /inicio/resumen` (tablero distinto por rol) |
| Catálogos | `/catalogos/grupos`, `/estudiantes`, `/acudientes`, `/docentes`, `/contactos`, `/roles` → listas desplegables (el usuario nunca escribe IDs) |
| Configuración | `GET/POST/PATCH /configuracion/modulos` · `GET/PUT /configuracion/permisos` (matriz rol × módulo) |
| Usuarios / Roles | CRUD `/usuarios` y `/roles` · `POST /usuarios/{id}/reactivar` |
| Administración | CRUD `/grupos`, `/estudiantes`, `/acudientes-estudiantes` · `GET /grupos/{id}/estudiantes` · `GET /estudiantes/{id}/acudientes` |
| Comunicados | CRUD `/comunicados` · `POST /comunicados/{id}/confirmar` · `GET /comunicados/{id}/lecturas` |
| Mensajería | `GET /mensajes/grupo/{id}` · `GET /mensajes/directos` · `GET /mensajes/directos/{usuario}` · `POST /mensajes` |
| Citaciones | CRUD `/citaciones` (con `?desde=&hasta=` para el calendario) · `PATCH /citaciones/{id}/estado` · `POST/GET/PATCH /citaciones/{id}/asistencia` |
| Notificaciones | `GET /notificaciones` · `GET /notificaciones/contador` · `PATCH .../leer` · `PATCH /notificaciones/leer-todas` · `POST /notificaciones` (aviso masivo) |
| Tiempo real | `WS /ws?token=<JWT>` → eventos `notificacion`, `mensaje`, `mensajes_leidos` |
| Reportes | `/reportes/resumen` · `/lectura-comunicados` · `/acudientes-pendientes` · `/citaciones` · `/actividad-grupos` |

**Convenciones**
- `POST` crea un registro.
- `PATCH` actualiza solo los campos enviados.
- `DELETE` hace **borrado lógico**: pasa el `estado` a `'inactivo'` y conserva el historial.
- Los listados aceptan `?incluir_inactivos=true`.

### Permisos por rol (tabla `rol_modulo`)

| Módulo | Coordinación | Docente | Acudiente |
|---|:-:|:-:|:-:|
| Inicio, Comunicados, Mensajería, Citaciones, Estudiantes | ✔ | ✔ | ✔ |
| Grupos, Reportes | ✔ | ✔ | — |
| Usuarios, Configuración | ✔ | — | — |

Cada router de la API valida con `requiere_modulo("clave")` que el rol tenga el módulo asignado en la base de datos. Dentro de cada módulo, la API además filtra la información: un acudiente solo ve lo de sus hijos y un docente solo gestiona lo suyo.

---

## 5. Notificaciones y tiempo real

Algunas acciones notifican automáticamente:

| Acción | A quién se notifica |
|---|---|
| Publicar un comunicado | Todos los acudientes destinatarios |
| Crear, reprogramar o cancelar una citación | Los acudientes citados |
| Que el acudiente confirme una citación | El docente |
| Enviar un mensaje directo | El destinatario |

Cada notificación pasa por tres pasos:
1. Se **guarda** en `notificaciones`, lo que alimenta la campanita.
2. Se **empuja por WebSocket** a quien esté conectado, sin recargar la página.
3. Si `SMTP_*` está configurado en el `.env`, también se **envía por correo** en segundo plano.

Los mensajes del chat de un grupo llegan en vivo a los acudientes de ese grupo y a su director.

---

## 6. Pruebas automatizadas

Las pruebas corren contra un **PostgreSQL real** separado del de producción. Puede ser local o una rama de Neon. Antes de cada prueba se recrean las tablas y se cargan los datos demo.

```bash
# Windows (PowerShell)
$env:TEST_DATABASE_URL="postgresql://usuario:clave@host/colegio_test"
# macOS / Linux
export TEST_DATABASE_URL="postgresql://usuario:clave@host/colegio_test"

pytest -q          # → 59 passed
```

Las pruebas cubren:
- Login.
- Permisos de cada rol.
- Validaciones 422.
- Duplicados 409.
- Llaves foráneas 400.
- Borrado lógico y reactivación.
- Notificaciones a los destinatarios correctos.
- Confirmación de lectura única.
- La relación 1:1 de asistencia.
- El calendario.
- Los reportes.
- La entrega en tiempo real por WebSocket.

---

## 7. Cambios respecto a la versión del corte 1

| Antes | Ahora |
|---|---|
| `DELETE` borraba físicamente | Borrado lógico real (`estado = 'inactivo'`) |
| El cliente enviaba `password_hash` | Se envía `password` y se cifra con **bcrypt**; el hash nunca se devuelve |
| Sin login ni roles efectivos | **JWT** + permisos por rol + filtros por rol (cada quien ve lo suyo) |
| Sin CORS | CORS configurable, listo para Svelte |
| Se podía confirmar o vincular dos veces | Restricciones `UNIQUE` |
| `citaciones.estado` mezclaba dos significados | `estado_citacion` (negocio) separado de `estado` (borrado lógico) |
| Redundancia `citaciones.estado` vs `asistencia.confirmado` | Asistencia guarda `asistio` + `observaciones` |
| Comunicados solo por grupo | Circulares generales (`grupo_id = NULL`) y prioridad urgente |
| Solo chat grupal | Chat por grupo **y** mensajes directos |
| Notificaciones manuales | Automáticas + WebSocket + correo opcional |
| Sin reportes | 5 endpoints de analítica |
| `modificado` lo ponía la API | Lo pone un **trigger** de PostgreSQL |
| 12 repositories con el mismo SQL copiado | `BaseRepository` con herencia |
| try/except repetido en cada ruta | Manejadores globales de errores |
| Sin pruebas en el repositorio | 63 pruebas automatizadas |
| 4 roles, menú fijo | 3 roles y menú cargado desde `rol_modulo` |

## 8. Correcciones tras la sustentación (oct. 2026)

| Corrección | Cómo quedó |
|---|---|
| "Curso" debe llamarse "Grupo" | Tabla `grupos`, columnas `grupo_id`, rutas `/grupos`, módulo y menú "Grupos" |
| Una sola clase en `models/` | `app/models/modelos.py` → clase `Modelos`; las rutas usan `Modelos.GrupoCrear`, `Modelos.GrupoSalida`, etc. |
| Eliminar la tabla de logs | Se retiró `logs_actividad` con su repositorio, rutas, servicio y la bitácora de Reportes (quedan 13 tablas) |
| No pedir datos automáticos | Verificado con pruebas (`tests/test_campos_automaticos.py`); además se quitó `estado` de los formularios de edición |
