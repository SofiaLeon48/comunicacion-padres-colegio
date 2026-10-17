// Utilidades de formato (fechas, nombres legibles e insignias) en español.
export const ROLES = { coordinacion: 'Coordinación', docente: 'Docente', acudiente: 'Acudiente' };
export const COLOR_ROL = { coordinacion: 'primary', docente: 'success', acudiente: 'info' };
export const JORNADAS = { manana: 'Mañana', tarde: 'Tarde', unica: 'Única' };
export const GRADOS = [
	[0, 'Transición'], [1, 'Primero'], [2, 'Segundo'], [3, 'Tercero'], [4, 'Cuarto'], [5, 'Quinto'],
	[6, 'Sexto'], [7, 'Séptimo'], [8, 'Octavo'], [9, 'Noveno'], [10, 'Décimo'], [11, 'Undécimo']
];
export const ESTADO_CITACION = {
	pendiente: ['Pendiente', 'warning'],
	confirmada: ['Confirmada', 'primary'],
	cancelada: ['Cancelada', 'secondary'],
	realizada: ['Realizada', 'success']
};
export const TIPO_NOTIFICACION = {
	comunicado: ['Comunicado', 'primary', 'bi-megaphone', '/comunicados'],
	mensaje: ['Mensaje', 'success', 'bi-chat-dots', '/mensajes'],
	citacion: ['Citación', 'warning', 'bi-calendar-event', '/citaciones'],
	sistema: ['Aviso', 'dark', 'bi-info-circle', '/notificaciones']
};

const fFecha = new Intl.DateTimeFormat('es-CO', { day: 'numeric', month: 'short', year: 'numeric' });
const fFechaHora = new Intl.DateTimeFormat('es-CO', {
	day: 'numeric', month: 'short', year: 'numeric', hour: 'numeric', minute: '2-digit'
});
const fHora = new Intl.DateTimeFormat('es-CO', { hour: 'numeric', minute: '2-digit' });
const fLarga = new Intl.DateTimeFormat('es-CO', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });

const aFecha = (v) => (v instanceof Date ? v : new Date(v));
export const fecha = (v) => (v ? fFecha.format(aFecha(v)) : '—');
export const fechaHora = (v) => (v ? fFechaHora.format(aFecha(v)) : '—');
export const hora = (v) => (v ? fHora.format(aFecha(v)) : '');
export const fechaLarga = (v = new Date()) => fLarga.format(aFecha(v));

export function haceCuanto(v) {
	if (!v) return '';
	const s = Math.round((Date.now() - aFecha(v).getTime()) / 1000);
	if (s < 60) return 'hace un momento';
	if (s < 3600) return `hace ${Math.floor(s / 60)} min`;
	if (s < 86400) return `hace ${Math.floor(s / 3600)} h`;
	if (s < 604800) return `hace ${Math.floor(s / 86400)} d`;
	return fecha(v);
}

/** Valor para <input type="datetime-local"> a partir de una fecha. */
export function aInputFecha(v) {
	const d = aFecha(v);
	const p = (n) => String(n).padStart(2, '0');
	return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
}

export function esc(v) {
	return String(v ?? '')
		.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
		.replaceAll('"', '&quot;').replaceAll("'", '&#39;');
}

/** Insignia en HTML (para celdas de DataTables). */
export const insignia = (texto, color = 'secondary', icono = '') =>
	`<span class="badge rounded-pill text-bg-${color}">${icono ? `<i class="bi ${icono} me-1"></i>` : ''}${esc(texto)}</span>`;

export function saludo() {
	const h = new Date().getHours();
	return h < 12 ? 'Buenos días' : h < 19 ? 'Buenas tardes' : 'Buenas noches';
}

export const iniciales = (nombre = '') =>
	nombre.split(' ').filter(Boolean).slice(0, 2).map((p) => p[0]).join('').toUpperCase();
