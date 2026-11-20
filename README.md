# Conecta Escolar · Comunicación Padres-Colegio en Tiempo Real

Electiva Disciplinar II · Ingeniería de Sistemas, 5.º semestre.

**Problema:** la comunicación con los acudientes se hace por WhatsApp o con circulares en papel, lo que genera desinformación y pérdida de mensajes importantes.

**Solución:** plataforma oficial con circulares digitales y confirmación de lectura, mensajería por grupo y directa, calendario de citaciones, notificaciones en tiempo real y reportes.

**Corte 3 (proyecto integrador):**
- **Tablero:** dashboard publicado por la API (4 indicadores, 6 gráficos de barras y circulares, filtros por grupo y periodo) y compartido con un `<iframe>` dentro del módulo Tablero.
- **Reportes:** PDF y Excel con encabezado, pie y colores institucionales, sin IDs, filtros por rango de fechas, grupo y estado/prioridad, datos de 5+ tablas relacionadas y envío por correo (Brevo).
- **Inteligencia artificial (Gemini):** redacta comunicados a partir de una idea y analiza los reportes.
- **App móvil:** Capacitor 8 → APK de Android compilada con GitHub Actions.

**Roles:** Coordinación · Docente · Acudiente. El menú de cada rol se carga desde la base de datos (tabla `rol_modulo`).

## Estructura del repositorio

```
comunicacion-colegio/
├── backend/        → API REST (FastAPI + PostgreSQL/Neon) — ver backend/README.md
├── frontend/       → Aplicativo web (SvelteKit + Bootstrap) — ver frontend/README.md
│   └── android/    → Proyecto Android generado por Capacitor (APK)
├── .github/workflows/apk.yml → Compila la APK en GitHub Actions
├── docs/           → Diagrama entidad-relación (diagrama_er.dbml para dbdiagram.io)
├── render.yaml     → Despliegue de la API en Render
└── DESPLIEGUE.md   → Paso a paso para publicar en la nube
```

## Tecnologías

| Capa | Tecnología | Nube |
|---|---|---|
| Base de datos | PostgreSQL (13 tablas) | Neon |
| Backend | Python · FastAPI · Pydantic · psycopg2 · JWT · bcrypt · WebSockets | Render |
| Frontend | SvelteKit · Bootstrap 5 · DataTables · Chart.js | Vercel |
| Reportes | reportlab (PDF) · openpyxl (Excel) · Brevo (correo) | Render |
| IA | Google Gemini (AI Studio) | Google |
| Móvil | Capacitor 8 (Android) | APK por GitHub Actions |
| Pruebas | pytest (75 pruebas contra base de datos real) | — |

## Inicio rápido (local)

```bash
# Terminal 1 — API
cd backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # pega tu DATABASE_URL de Neon
python -m scripts.init_db
python -m scripts.seed
uvicorn main:app --reload   # → http://127.0.0.1:8000/docs

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev                 # → http://localhost:5173
```

Usuarios de prueba (contraseña `Colegio2026*`): `coordinacion@colegio.edu.co`, `lmartinez@colegio.edu.co`, `maria.rodriguez@correo.com`.

## Diagrama entidad-relación

Abre [dbdiagram.io](https://dbdiagram.io/d), pega el contenido de `docs/diagrama_er.dbml` y la página dibuja las 13 tablas agrupadas por módulo. Para exportarlo: **Export → PNG o PDF**.
