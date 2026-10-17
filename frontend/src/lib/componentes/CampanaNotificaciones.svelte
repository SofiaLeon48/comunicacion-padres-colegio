<!-- Campana del encabezado: contador en tiempo real y últimas notificaciones. -->
<script>
	import { goto } from '$app/navigation';
	import { api } from '$lib/api.js';
	import { haceCuanto, TIPO_NOTIFICACION } from '$lib/formato.js';
	import { refrescarNotificaciones, tiempoReal } from '$lib/tiempoReal.svelte.js';

	let abierto = $state(false);

	async function abrir(n) {
		abierto = false;
		if (!n.leido) {
			await api.patch(`/notificaciones/${n.id}/leer`).catch(() => {});
			refrescarNotificaciones();
		}
		goto(TIPO_NOTIFICACION[n.tipo]?.[3] ?? '/notificaciones');
	}

	async function leerTodas() {
		await api.patch('/notificaciones/leer-todas').catch(() => {});
		refrescarNotificaciones();
	}
</script>

<div class="position-relative">
	<button class="btn btn-icono" aria-label="Notificaciones" onclick={() => (abierto = !abierto)}>
		<i class="bi bi-bell fs-5"></i>
		{#if tiempoReal.noLeidas > 0}
			<span class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger">
				{tiempoReal.noLeidas > 99 ? '99+' : tiempoReal.noLeidas}
			</span>
		{/if}
	</button>

	{#if abierto}
		<button class="capa-cierre" aria-label="Cerrar" onclick={() => (abierto = false)}></button>
		<div class="menu-flotante panel-notificaciones shadow-lg">
			<div class="d-flex justify-content-between align-items-center px-3 py-2 border-bottom">
				<strong>Notificaciones</strong>
				<button class="btn btn-link btn-sm p-0" onclick={leerTodas}>Marcar todas como leídas</button>
			</div>
			<div class="lista-notificaciones">
				{#each tiempoReal.ultimas as n (n.id)}
					{@const t = TIPO_NOTIFICACION[n.tipo] ?? TIPO_NOTIFICACION.sistema}
					<button class="item-notificacion" class:no-leida={!n.leido} onclick={() => abrir(n)}>
						<span class="icono-notif bg-{t[1]}-subtle text-{t[1]}"><i class="bi {t[2]}"></i></span>
						<span class="flex-grow-1 text-start min-w-0">
							<span class="d-block fw-semibold small text-truncate">{n.titulo}</span>
							<span class="d-block small text-muted texto-2-lineas">{n.contenido}</span>
							<span class="d-block text-muted" style="font-size: .72rem">{haceCuanto(n.fecha)}</span>
						</span>
					</button>
				{:else}
					<div class="text-center text-muted small py-4">No tienes notificaciones</div>
				{/each}
			</div>
			<a class="d-block text-center small py-2 border-top" href="/notificaciones" onclick={() => (abierto = false)}>
				Ver todas
			</a>
		</div>
	{/if}
</div>
