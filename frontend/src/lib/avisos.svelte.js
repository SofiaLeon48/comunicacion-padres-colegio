// Avisos emergentes (toasts) para confirmar acciones o mostrar errores.
export const avisos = $state({ lista: [] });
let siguiente = 1;

export function avisar(texto, tipo = 'success', titulo = null, ms = 4500) {
	const id = siguiente++;
	avisos.lista.push({ id, texto, tipo, titulo });
	setTimeout(() => quitarAviso(id), ms);
}

export function quitarAviso(id) {
	avisos.lista = avisos.lista.filter((a) => a.id !== id);
}

export const exito = (t) => avisar(t, 'success');
export const error = (t) => avisar(t instanceof Error ? t.message : String(t), 'danger', 'Algo salió mal', 6500);
