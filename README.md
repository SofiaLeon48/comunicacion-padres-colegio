# Comunicación Padres-Colegio en Tiempo Real

Electiva Disciplinar II · Ingeniería de Sistemas, 5.º semestre.

**Problema:** la comunicación con los acudientes se hace por WhatsApp o con circulares en papel. Eso genera desinformación y hace que se pierdan mensajes importantes.

**Solución:** una plataforma oficial de comunicación con:
- circulares digitales con confirmación de lectura;
- mensajería por curso y directa;
- calendario de citaciones a padres;
- notificaciones en tiempo real;
- reportes.

**Usuarios:** padres/acudientes, docentes, coordinación y administración.

## Estructura del repositorio

```
comunicacion-colegio/
├── backend/     → API REST (FastAPI + PostgreSQL/Neon) — ver backend/README.md
├── frontend/    → Aplicación web (Svelte) — corte 2
└── docs/        → Diagrama entidad-relación (PNG, PDF, Mermaid)
```

## Tecnologías

| Capa | Tecnología |
|---|---|
| Base de datos | PostgreSQL en Neon |
| Backend | Python · FastAPI · Pydantic · psycopg2 · JWT · bcrypt · WebSockets |
| Frontend | Svelte (en desarrollo) |
| Pruebas | pytest (50 pruebas contra base de datos real) |

## Inicio rápido

```bash
cd backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # pega tu DATABASE_URL de Neon
python -m scripts.init_db
python -m scripts.seed
uvicorn main:app --reload   # → http://127.0.0.1:8000/docs
```

![Diagrama ER](docs/diagrama_er.png)
