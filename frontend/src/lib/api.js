// Cliente HTTP: todas las vistas hablan con la API a través de estas funciones.
import { goto } from '$app/navigation';
import { API_URL } from './config.js';
import { cerrarSesion, sesion } from './sesion.svelte.js';

const CAMPOS = {
	nombre: 'Nombre', correo: 'Correo', password: 'Contraseña', telefono: 'Teléfono', titulo: 'Título',
	contenido: 'Contenido', motivo: 'Motivo', fecha_hora: 'Fecha y hora', documento: 'Documento',
	grado: 'Grado', curso_id: 'Curso', estudiante_id: 'Estudiante', rol_id: 'Rol', lugar: 'Lugar',
	password_nueva: 'Nueva contraseña', descripcion: 'Descripción', parentesco: 'Parentesco'
};

function traducir(e) {
	const campo = CAMPOS[e.loc?.[e.loc.length - 1]] ?? e.loc?.[e.loc.length - 1] ?? 'Dato';
	const ctx = e.ctx ?? {};
	switch (e.type) {
		case 'missing': return `${campo}: es obligatorio`;
		case 'string_too_short': return `${campo}: mínimo ${ctx.min_length} caracteres`;
		case 'string_too_long': return `${campo}: máximo ${ctx.max_length} caracteres`;
		case 'value_error': return `${campo}: valor inválido${e.msg?.includes('email') ? ' (correo)' : ''}`;
		case 'greater_than_equal': return `${campo}: debe ser mayor o igual a ${ctx.ge}`;
		case 'less_than_equal': return `${campo}: debe ser menor o igual a ${ctx.le}`;
		default: return `${campo}: ${e.msg}`;
	}
}

function mensajeError(datos, status) {
	if (!datos) return `Error ${status} en el servidor.`;
	if (typeof datos.detail === 'string') return datos.detail;
	if (Array.isArray(datos.detail)) return datos.detail.map(traducir).join(' · ');
	return `Error ${status}.`;
}

export async function solicitud(metodo, ruta, cuerpo) {
	const headers = { 'Content-Type': 'application/json' };
	if (sesion.token) headers.Authorization = `Bearer ${sesion.token}`;
	let r;
	try {
		r = await fetch(API_URL + ruta, {
			method: metodo,
			headers,
			body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo)
		});
	} catch {
		throw new Error('No se pudo conectar con el servidor. Verifica que la API esté encendida.');
	}
	if (r.status === 401 && sesion.token) {
		cerrarSesion();
		goto('/login');
		throw new Error('Tu sesión expiró. Inicia sesión de nuevo.');
	}
	const datos = await r.json().catch(() => null);
	if (!r.ok) throw new Error(mensajeError(datos, r.status));
	return datos;
}

export const api = {
	get: (ruta) => solicitud('GET', ruta),
	post: (ruta, cuerpo = {}) => solicitud('POST', ruta, cuerpo),
	put: (ruta, cuerpo = {}) => solicitud('PUT', ruta, cuerpo),
	patch: (ruta, cuerpo = {}) => solicitud('PATCH', ruta, cuerpo),
	del: (ruta) => solicitud('DELETE', ruta)
};

/** Construye "?a=1&b=2" ignorando valores vacíos. */
export function qs(params) {
	const p = Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '');
	return p.length ? '?' + new URLSearchParams(p).toString() : '';
}
