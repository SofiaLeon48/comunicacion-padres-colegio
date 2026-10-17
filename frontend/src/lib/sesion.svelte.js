// Estado global de la sesión: token, usuario y módulos permitidos (vienen de la tabla rol_modulo).
const CLAVE = 'conecta_escolar_sesion';

export const sesion = $state({ token: null, usuario: null, modulos: [] });

function guardar() {
	try {
		localStorage.setItem(CLAVE, JSON.stringify(sesion));
	} catch {
		/* almacenamiento no disponible */
	}
}

export function cargarSesion() {
	try {
		const datos = JSON.parse(localStorage.getItem(CLAVE));
		if (datos?.token) Object.assign(sesion, datos);
	} catch {
		/* sesión corrupta: se ignora */
	}
}

export function iniciarSesion(respuesta) {
	sesion.token = respuesta.access_token;
	sesion.usuario = respuesta.usuario;
	sesion.modulos = respuesta.modulos ?? [];
	guardar();
}

export function actualizarUsuario(usuario) {
	sesion.usuario = { ...sesion.usuario, ...usuario };
	guardar();
}

export function actualizarModulos(modulos) {
	sesion.modulos = modulos;
	guardar();
}

export function cerrarSesion() {
	sesion.token = null;
	sesion.usuario = null;
	sesion.modulos = [];
	try {
		localStorage.removeItem(CLAVE);
	} catch {
		/* nada */
	}
}

export function tieneModulo(clave) {
	return sesion.modulos.some((m) => m.clave === clave);
}

export const rol = () => sesion.usuario?.rol;
export const esCoordinacion = () => sesion.usuario?.rol === 'coordinacion';
export const esDocente = () => sesion.usuario?.rol === 'docente';
export const esAcudiente = () => sesion.usuario?.rol === 'acudiente';
export const esPersonal = () => ['coordinacion', 'docente'].includes(sesion.usuario?.rol);
