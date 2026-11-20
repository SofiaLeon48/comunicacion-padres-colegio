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

---

# Corte 3: Tablero, Reportes, IA y app móvil (APK)

Haz estos pasos **una sola vez**, en este orden.

## A. Subir el código
En la carpeta del proyecto de tu computador:
```
git add .
git commit -m "Corte 3: tablero, reportes PDF/Excel, IA y app movil"
git push
```
Render (API) y Vercel (web) se actualizan solos con el push. GitHub empieza a compilar la APK.

## B. Actualizar la base de datos de Neon (sin borrar nada)
Con `backend/.env` apuntando a Neon:
```
cd backend
venv\Scripts\activate
pip install -r requirements.txt
python -m scripts.migrar_corte3
```
Debe decir `✔ Migración aplicada` y listar el módulo `tablero`. (Agrega el módulo Tablero y sus permisos.)

## C. Crear las llaves gratuitas
**Correo — Brevo**
1. Crea una cuenta en https://www.brevo.com (gratis, 300 correos al día).
2. **Senders, domains & dedicated IPs → Senders → Add a sender**: agrega tu correo (p. ej. tu Gmail) y confírmalo desde el enlace que te llega.
3. **SMTP & API → API Keys → Generate a new API key**. Copia la llave (empieza por `xkeysib-`).

**Inteligencia artificial — Gemini**
1. Entra a https://aistudio.google.com/apikey con tu cuenta de Google.
2. **Create API key** y cópiala.

## D. Variables en Render
Render → tu servicio → **Environment** → agrega o cambia:

| Variable | Valor |
|---|---|
| `BREVO_API_KEY` | la llave de Brevo |
| `CORREO_REMITENTE` | el correo que verificaste en Brevo |
| `GEMINI_API_KEY` | la llave de Google AI Studio |
| `CORS_ORIGIN_REGEX` | `(https://.*\.vercel\.app\|https?://localhost\|capacitor://localhost)` |

Clic en **Save, rebuild and deploy**. La última variable permite que la app del celular hable con la API.

## E. Descargar e instalar la APK
1. GitHub → tu repositorio → pestaña **Actions** → **APK Android** → la ejecución más reciente (verde, ~6 min).
   Si tu API no está en `https://conecta-escolar-api.onrender.com`, antes crea la variable
   **Settings → Secrets and variables → Actions → Variables → `VITE_API_URL`** con tu URL y vuelve a ejecutar (**Run workflow**).
2. Abajo, en **Artifacts**, descarga **ConectaEscolar-apk** (es un .zip con `ConectaEscolar.apk` adentro).
3. Pasa la `.apk` al celular (WhatsApp a ti misma, Drive o cable) y ábrela. Android pedirá permitir
   **instalar apps de origen desconocido** para esa app: acéptalo e instala.

## F. Verificar antes de presentar
- `https://TU-API.onrender.com/salud` → `"base_de_datos": "ok"` (despierta la API 5 minutos antes).
- Web: módulos **Tablero** y **Reportes** en el menú de Coordinación.
- Reportes → **Enviar por correo** llega a tu bandeja (revisa spam la primera vez).
- Comunicados → **Nuevo** → **Redactar con inteligencia artificial**.
- Celular: abrir la app, iniciar sesión, ver el Tablero y descargar un PDF.
