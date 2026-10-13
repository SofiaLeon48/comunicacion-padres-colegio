// Conexión WebSocket con la API: notificaciones y mensajes llegan sin recargar la página.
import { api } from './api.js';
import { avisar } from './avisos.svelte.js';
import { API_URL } from './config.js';
import { sesion } from './sesion.svelte.js';

export const tiempoReal = $state({ conectado: false, noLeidas: 0, ultimas: [] });

const oyentes = new Set();
let ws = null;
let reintento = null;
let latido = null;

/** Suscribe una vista a los eventos en vivo. Devuelve la función para desuscribirse. */
export function alRecibir(fn) {
	oyentes.add(fn);
	return () => oyentes.delete(fn);
}

export async function refrescarNotificaciones() {
	try {
		const [contador, ultimas] = await Promise.all([
			api.get('/notificaciones/contador'),
			api.get('/notificaciones/?limite=8')
		]);
		tiempoReal.noLeidas = contador.no_leidas;
		tiempoReal.ultimas = ultimas;
	} catch {
		/* silencioso */
	}
}

export function conectar() {
	desconectar();
	if (!sesion.token) return;
	ws = new WebSocket(`${API_URL.replace(/^http/, 'ws')}/ws?token=${sesion.token}`);
	ws.onopen = () => {
		tiempoReal.conectado = true;
		latido = setInterval(() => ws?.readyState === 1 && ws.send('ping'), 25000);
	};
	ws.onmessage = (e) => {
		const m = JSON.parse(e.data);
		if (m.evento === 'notificacion') {
			tiempoReal.noLeidas += 1;
			tiempoReal.ultimas = [m.datos, ...tiempoReal.ultimas].slice(0, 8);
			avisar(m.datos.contenido, 'primary', m.datos.titulo, 6000);
		}
		oyentes.forEach((fn) => fn(m));
	};
	ws.onclose = () => {
		tiempoReal.conectado = false;
		clearInterval(latido);
		if (sesion.token) reintento = setTimeout(conectar, 5000);
	};
}

export function desconectar() {
	clearTimeout(reintento);
	clearInterval(latido);
	if (ws) {
		ws.onclose = null;
		ws.close();
		ws = null;
	}
	tiempoReal.conectado = false;
}
