# Frontend · Conecta Escolar

Aplicativo web con **SvelteKit + Bootstrap 5**. Toda la información sale de la API (FastAPI + Neon).

## Puesta en marcha (local)

Requisitos: Node.js 20 o superior y la API encendida (`uvicorn main:app --reload` en `backend/`).

```
cd frontend
npm install
copy .env.example .env        # (cp en macOS/Linux) → VITE_API_URL=http://127.0.0.1:8000
npm run dev                   # → http://localhost:5173
```

Usuarios de prueba (contraseña `Colegio2026*`): `coordinacion@colegio.edu.co` (Coordinación), `lmartinez@colegio.edu.co` (Docente), `maria.rodriguez@correo.com` (Acudiente). En el login también hay un botón **"Cuentas de demostración"**.

## Cómo cumple el taller

| Requisito | Dónde |
|---|---|
| Login con opción de rol | `src/routes/login` — el rol se valida en la API |
| Menú cargado desde la BD (`rol_modulo`) | `MenuNav.svelte` usa `GET /auth/mis-modulos`; `(app)/+layout.svelte` bloquea rutas no permitidas |
| 3 roles funcionando | Coordinación (9 módulos), Docente (7), Acudiente (5) |
| Mínimo 6 componentes reutilizados | 15 componentes en `src/lib/componentes` (ver abajo) |
| Todas las tablas con DataTables | `TablaDatos.svelte` (DataTables + Bootstrap 5 + Responsive, en español) |
| Nunca se ven ni se digitan IDs | Las tablas no tienen columna ID; los formularios usan `SelectorLista.svelte` (nombres → id interno) |
| Responsive y Bootstrap | Bootstrap 5.3 + menú colapsable en celular |
| Comunicación real con la API | `src/lib/api.js` (token JWT) y `src/lib/tiempoReal.svelte.js` (WebSocket) |

## Estructura

```
src/
├── app.css                     → estilos globales
├── lib/
│   ├── api.js                  → cliente HTTP (fetch + token + errores en español)
│   ├── sesion.svelte.js        → usuario, rol y módulos permitidos
│   ├── tiempoReal.svelte.js    → WebSocket: notificaciones y mensajes en vivo
│   ├── avisos.svelte.js        → avisos emergentes (toasts)
│   ├── datatables.js           → carga de DataTables + idioma español
│   ├── formato.js              → fechas, roles, estados
│   └── componentes/            → 15 componentes reutilizables
└── routes/
    ├── login/                  → inicio de sesión con rol
    └── (app)/                  → plantilla: Encabezado + Menú + contenido + Pie
        ├── inicio/  comunicados/  mensajes/  citaciones/  estudiantes/
        ├── cursos/  usuarios/  reportes/  configuracion/
        └── perfil/  notificaciones/
```

## Componentes reutilizables

| Componente | Uso |
|---|---|
| `Encabezado` | Marca, estado de conexión, campana y menú del usuario |
| `MenuNav` | Menú horizontal generado desde la BD |
| `PiePagina` | Pie de página |
| `TituloPagina` | Título, descripción y botones de cada módulo |
| `TablaDatos` | Tabla con DataTables (buscar, ordenar, paginar, responsive) |
| `Modal` | Ventana de Crear (verde) / Ver (azul) / Editar (naranja) / Eliminar (rojo) |
| `ModalConfirmar` | Confirmación antes de eliminar o desactivar |
| `TarjetaIndicador` | Indicadores numéricos (KPI) |
| `InsigniaEstado` | Insignias de estado |
| `SelectorLista` | Listas desplegables desde la API (evita digitar IDs) |
| `Grafico` | Gráficos con Chart.js |
| `Calendario` | Calendario mensual de citaciones |
| `CampanaNotificaciones` | Notificaciones en tiempo real |
| `Avisos` | Mensajes emergentes |
| `Cargando` | Indicador de carga y estado vacío |

## Publicar en la nube

Ver [`../DESPLIEGUE.md`](../DESPLIEGUE.md). En Vercel solo hay que definir la variable `VITE_API_URL` con la URL de la API en Render.
