# Publicar Conecta Escolar en la nube

Orden: **1. Neon** (base de datos) → **2. Render** (API) → **3. Vercel** (frontend) → **4. Ajuste final**.

## 1. Neon — base de datos

1. En Neon, copia la cadena de conexión (**Connect → Connection string**, con *pooling* activado).
2. En tu computador, en `backend/.env`, pon esa cadena en `DATABASE_URL`.
3. Crea las 13 tablas y los datos de prueba:
   ```
   cd backend
   venv\Scripts\activate
   python -m scripts.init_db
   python -m scripts.seed
   ```

## 2. Render — API

1. Entra a **render.com** e inicia sesión con GitHub.
2. **New → Blueprint** → elige el repositorio `comunicacion-padres-colegio`. Render lee el archivo `render.yaml`.
3. Te pedirá el valor de **DATABASE_URL**: pega la cadena de Neon. Clic en **Apply**.
4. Espera a que termine (3–5 min). Copia la URL del servicio, p. ej. `https://conecta-escolar-api.onrender.com`.
5. Prueba: abre `https://TU-API.onrender.com/salud` → debe decir `"base_de_datos": "ok"`.

> Plan gratis: la API se "duerme" tras 15 minutos sin uso y tarda ~50 s en despertar. **Ábrela unos minutos antes de la sustentación.**

## 3. Vercel — frontend

1. Entra a **vercel.com** e inicia sesión con GitHub.
2. **Add New → Project** → importa el repositorio.
3. En **Root Directory** elige `frontend`. (El resto se toma de `frontend/vercel.json`.)
4. En **Environment Variables** agrega:
   - `VITE_API_URL` = la URL de Render (sin `/` al final).
5. Clic en **Deploy**. Al terminar tendrás una URL como `https://conecta-escolar.vercel.app`.

## 4. Ajuste final (CORS)

La API ya acepta cualquier dominio `*.vercel.app` (variable `CORS_ORIGIN_REGEX`). Si usas otro dominio, agrégalo en Render → **Environment** → `CORS_ORIGINS`.

## Para la sustentación

| Qué mostrar | Dónde |
|---|---|
| Aplicativo web | URL de Vercel (y local con `npm run dev`) |
| API y documentación | `https://TU-API.onrender.com/docs` |
| Datos guardándose | Neon → **Tables** (p. ej. `comunicados`, `confirmaciones_lectura`, `rol_modulo`) |

Demostración sugerida (2 navegadores o una ventana de incógnito):
1. Docente publica un comunicado para el 5A → al acudiente le llega la notificación al instante.
2. Acudiente confirma la lectura → en Neon aparece la fila en `confirmaciones_lectura`.
3. Docente abre el comunicado y ve quién leyó y quién no.
4. Coordinación activa "Grupos" para el rol Acudiente en **Configuración** → el menú del acudiente cambia (tabla `rol_modulo`).
