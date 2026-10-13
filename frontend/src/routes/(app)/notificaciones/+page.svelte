<script>
	import { goto } from '$app/navigation';
	import { onDestroy, onMount } from 'svelte';
	import { api } from '$lib/api.js';
	import { error, exito } from '$lib/avisos.svelte.js';
	import Cargando from '$lib/componentes/Cargando.svelte';
	import TablaDatos from '$lib/componentes/TablaDatos.svelte';
	import TituloPagina from '$lib/componentes/TituloPagina.svelte';
	import { esc, fechaHora, insignia, TIPO_NOTIFICACION } from '$lib/formato.js';
	import { alRecibir, refrescarNotificaciones } from '$lib/tiempoReal.svelte.js';

	let lista = $state([]);
	let cargando = $state(true);
	let soloNoLeidas = $state(false);

	async function cargar() {
		try {
			lista = await api.get(`/notificaciones/?limite=200${soloNoLeidas ? '&solo_no_leidas=true' : ''}`);
		} catch (e) {
			error(e);
		} finally {
			cargando = false;
		}
	}
	onMount(cargar);
	const quitar = alRecibir((m) => m.evento === 'notificacion' && cargar());
	onDestroy(quitar);

	const columnas = [
		{ titulo: 'Fecha', campo: 'fecha', clase: 'text-nowrap', render: (v) => fechaHora(v), orden: (n) => n.fecha },
		{ titulo: 'Tipo', campo: 'tipo', render: (v) => { const t = TIPO_NOTIFICACION[v] ?? TIPO_NOTIFICACION.sistema; return insignia(t[0], t[1], t[2]); } },
		{ titulo: 'Notificación', campo: 'titulo', render: (v, n) => `<div class="${n.leido ? '' : 'fw-bold'}">${esc(v)}</div><div class="small text-muted texto-2-lineas">${esc(n.contenido)}</div>` },
		{ titulo: 'Estado', campo: 'leido', render: (v) => (v ? insignia('Leída', 'light') : insignia('Nueva', 'primary')) }
	];
	const acciones = [
		{ icono: 'bi-box-arrow-up-right', titulo: 'Abrir', color: 'primary', accion: abrir },
		{ icono: 'bi-check2', titulo: 'Marcar como leída', color: 'success', accion: leer, visible: (n) => !n.leido },
		{ icono: 'bi-trash', titulo: 'Eliminar', color: 'danger', accion: eliminar }
	];

	async function leer(n) {
		try {
			await api.patch(`/notificaciones/${n.id}/leer`);
			await cargar();
			refrescarNotificaciones();
		} catch (e) {
			error(e);
		}
	}
	async function abrir(n) {
		if (!n.leido) await leer(n);
		goto(TIPO_NOTIFICACION[n.tipo]?.[3] ?? '/inicio');
	}
	async function eliminar(n) {
		try {
			await api.del(`/notificaciones/${n.id}`);
			exito('Notificación eliminada.');
			await cargar();
			refrescarNotificaciones();
		} catch (e) {
			error(e);
		}
	}
	async function leerTodas() {
		try {
			const r = await api.patch('/notificaciones/leer-todas');
			exito(r.mensaje);
			await cargar();
			refrescarNotificaciones();
		} catch (e) {
			error(e);
		}
	}
</script>

<svelte:head><title>Notificaciones · Conecta Escolar</title></svelte:head>

<TituloPagina titulo="Notificaciones" icono="bi-bell" descripcion="Avisos de comunicados, mensajes y citaciones.">
	<button class="btn btn-outline-primary" onclick={leerTodas}><i class="bi bi-check2-all me-1"></i>Marcar todas como leídas</button>
</TituloPagina>

<div class="tarjeta tarjeta-cuerpo">
	<div class="filtros">
		<div class="form-check form-switch">
			<input class="form-check-input" type="checkbox" id="nl" bind:checked={soloNoLeidas} onchange={cargar} />
			<label class="form-check-label" for="nl">Solo no leídas</label>
		</div>
	</div>
	<Cargando {cargando}>
		<TablaDatos {columnas} datos={lista} {acciones} ordenInicial={[[0, 'desc']]} />
	</Cargando>
</div>
