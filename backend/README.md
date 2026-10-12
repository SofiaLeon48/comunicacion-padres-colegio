# Backend · API de Comunicación Padres-Colegio

API REST con **FastAPI + PostgreSQL (Neon)**. Hace cuatro cosas principales:
- Publica circulares digitales, con confirmación de lectura.
- Ofrece mensajería, tanto el chat de cada curso como mensajes directos.
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

# 4. Crear las 12 tablas (o pega database/schema.sql en el SQL Editor de Neon)
python -m scripts.init_db

# 5. Cargar datos de prueba
python -m scripts.seed

# 6. Encender la API
uvicorn main:app --reload
```

Cuando la API esté encendida, abre **http://127.0.0.1:8000/docs** para usar Swagger. Ahí haces clic en **Authorize**, inicias sesión con uno de los usuarios de prueba y ya puedes probar cualquier endpoint.

### Usuarios de prueba

Todos usan la contraseña `Colegio2026*`.

| Rol | Correo | Notas |
|---|---|---|
| admin | admin@colegio.edu.co | Acceso total |
| coordinacion | coordinacion@colegio.edu.co | Gestiona la plataforma |
| docente | lmartinez@colegio.edu.co | Director del 5A |
| docente | cgomez@colegio.edu.co | Directora del 6B |
| acudiente | maria.rodriguez@correo.com | Hijos en 5A y 6B |
| acudiente | jorge.perez@correo.com | Hijo en 5A |
| acudiente | laura.diaz@correo.com | Hijo en 5A (comparte con Jorge) |
| acudiente | ana.sanchez@correo.com | Hija en 6B |

---

## 2. Módulos y tablas

Son 5 módulos con 12 tablas en total. Las 12 tablas tienen los mismos campos de auditoría: `creado`, `modificado` y `estado`.

| Módulo | Tablas | Qué resuelve |
|---|---|---|
| **Usuarios y Roles** | `roles`, `usuarios` | Login, permisos por rol, perfil |
| **Administración** | `cursos`, `estudiantes`, `acudiente_estudiante` | Estructura académica y quién es acudiente de quién |
| **Comunicados y Mensajería** *(principal)* | `comunicados`, `confirmaciones_lectura`, `mensajes`, `citaciones`, `asistencia_citaciones` | Circulares, lectura, chat, calendario de citas |
| **Notificaciones** | `notificaciones` | Avisos en la plataforma, en tiempo real y opcionalmente por correo |
| **Reportes y Analítica** | `logs_actividad` + consultas SQL agregadas | Indicadores, % de lectura, asistencia, auditoría |

El diagrama entidad-relación está en [`../docs/diagrama_er.png`](../docs/diagrama_er.png). También hay versiones en PDF y Mermaid.

**Relaciones destacadas**
- **M:N** `usuarios ↔ estudiantes` mediante `acudiente_estudiante`. Un padre puede tener varios hijos y un hijo varios acudientes.
- **1:1** `citaciones ↔ asistencia_citaciones`. La restricción `UNIQUE (citacion_id)` es la que lo garantiza.
- **Opcionales con significado**:
  - `comunicados.curso_id = NULL` es una circular general.
  - `citaciones.acudiente_id = NULL` cita a todos los acudientes del estudiante.
  - En `mensajes` debe ir `curso_id` (chat del curso) **o** `destinatario_id` (mensaje directo), nunca los dos. Lo controla un `CHECK`.

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
├── database/schema.sql      → las 12 tablas, restricciones, triggers e índices
├── scripts/                 → init_db.py (crea tablas) · seed.py (datos de prueba)
├── tests/                   → 50 pruebas automatizadas contra PostgreSQL real
└── app/
    ├── core/                → Capa 1: configuración y conexión
    │   ├── config.py           variables del .env
    │   ├── database.py         pool de conexiones + get_cursor() (commit/rollback)
    │   ├── security.py         bcrypt + JWT
    │   ├── deps.py             usuario_actual, requiere_roles(...)
    │   └── errores.py          errores de PostgreSQL → HTTP 400/404/409/503
    ├── models/              → Capa 2: validación (Pydantic): Crear / Actualizar / Salida
    ├── repositories/        → Capa 3: SQL (patrón Repository)
    │   └── base.py             CRUD genérico heredado por los 12 repositories
    ├── services/            → Capa 4: lógica de negocio compartida
    │   ├── notificador.py      guarda la notificación + WebSocket + correo
    │   ├── tiempo_real.py      gestor de conexiones WebSocket
    │   ├── correo.py           SMTP opcional
    │   └── actividad.py        auditoría automática en logs_actividad
    └── api/                 → Capa 5: endpoints HTTP (un router por recurso)
```

Así viaja una petición:

**Swagger/Svelte → `api/` (permisos) → `models/` (valida, o responde 422) → `repositories/` (SQL) → Neon**

Y de regreso: **`services/` notifica y registra en el log → respuesta JSON.**

---

## 4. Endpoints principales

Hay unos 70 endpoints en total. Todos aparecen en `/docs`.

| Módulo | Endpoints destacados |
|---|---|
| Autenticación | `POST /auth/login` · `GET/PATCH /auth/me` · `PUT /auth/me/password` |
| Usuarios / Roles | CRUD `/usuarios` y `/roles` · `POST /usuarios/{id}/reactivar` |
| Administración | CRUD `/cursos`, `/estudiantes`, `/acudientes-estudiantes` · `GET /cursos/{id}/estudiantes` · `GET /estudiantes/{id}/acudientes` |
| Comunicados | CRUD `/comunicados` · `POST /comunicados/{id}/confirmar` · `GET /comunicados/{id}/lecturas` |
| Mensajería | `GET /mensajes/curso/{id}` · `GET /mensajes/directos` · `GET /mensajes/directos/{usuario}` · `POST /mensajes` |
| Citaciones | CRUD `/citaciones` (con `?desde=&hasta=` para el calendario) · `PATCH /citaciones/{id}/estado` · `POST/GET/PATCH /citaciones/{id}/asistencia` |
| Notificaciones | `GET /notificaciones` · `GET /notificaciones/contador` · `PATCH .../leer` · `PATCH /notificaciones/leer-todas` · `POST /notificaciones` (aviso masivo) |
| Tiempo real | `WS /ws?token=<JWT>` → eventos `notificacion`, `mensaje`, `mensajes_leidos` |
| Reportes | `/reportes/resumen` · `/lectura-comunicados` · `/acudientes-pendientes` · `/citaciones` · `/actividad-cursos` · `/actividad-reciente` · `/logs` |

**Convenciones**
- `POST` crea un registro.
- `PATCH` actualiza solo los campos enviados.
- `DELETE` hace **borrado lógico**: pasa el `estado` a `'inactivo'` y conserva el historial.
- Los listados aceptan `?incluir_inactivos=true`.

### Permisos por rol

| Acción | admin | coordinación | docente | acudiente |
|---|:-:|:-:|:-:|:-:|
| Gestionar usuarios, cursos, estudiantes | ✔ | ✔ (excepto admins) | — | — |
| Publicar circular de curso | ✔ | ✔ | ✔ | — |
| Publicar circular general | ✔ | ✔ | — | — |
| Ver comunicados | todos | todos | todos | generales + cursos de sus hijos |
| Confirmar lectura | — | — | — | ✔ |
| Chat de curso | ✔ | ✔ | ✔ | solo cursos de sus hijos |
| Mensaje directo | ✔ | ✔ | ✔ | solo al personal del colegio |
| Agendar citaciones | ✔ | ✔ | ✔ (las suyas) | confirmar asistencia |
| Reportes | ✔ | ✔ | ✔ | — |
| Logs de auditoría | ✔ | ✔ | — | — |

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

Los mensajes del chat de un curso llegan en vivo a los acudientes de ese curso y a su director.

---

## 6. Pruebas automatizadas

Las pruebas corren contra un **PostgreSQL real** separado del de producción. Puede ser local o una rama de Neon. Antes de cada prueba se recrean las tablas y se cargan los datos demo.

```bash
# Windows (PowerShell)
$env:TEST_DATABASE_URL="postgresql://usuario:clave@host/colegio_test"
# macOS / Linux
export TEST_DATABASE_URL="postgresql://usuario:clave@host/colegio_test"

pytest -q          # → 50 passed
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
| Comunicados solo por curso | Circulares generales (`curso_id = NULL`) y prioridad urgente |
| Solo chat grupal | Chat por curso **y** mensajes directos |
| Notificaciones manuales | Automáticas + WebSocket + correo opcional |
| Sin reportes | 6 endpoints de analítica |
| `modificado` lo ponía la API | Lo pone un **trigger** de PostgreSQL |
| 12 repositories con el mismo SQL copiado | `BaseRepository` con herencia |
| try/except repetido en cada ruta | Manejadores globales de errores |
| Sin pruebas en el repositorio | 50 pruebas automatizadas |
