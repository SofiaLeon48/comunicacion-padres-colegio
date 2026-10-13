<!-- Encabezado: marca, notificaciones en tiempo real y menú del usuario. -->
<script>
	import { goto } from '$app/navigation';
	import { NOMBRE_APP } from '$lib/config.js';
	import { iniciales, ROLES } from '$lib/formato.js';
	import { cerrarSesion, sesion } from '$lib/sesion.svelte.js';
	import { desconectar, tiempoReal } from '$lib/tiempoReal.svelte.js';
	import CampanaNotificaciones from './CampanaNotificaciones.svelte';

	let menuUsuario = $state(false);

	function salir() {
		desconectar();
		cerrarSesion();
		goto('/login');
	}
</script>

<header class="encabezado">
	<div class="container-xl d-flex align-items-center gap-3 py-2">
		<a href="/inicio" class="marca d-flex align-items-center gap-2 text-decoration-none">
			<img src="/favicon.svg" alt="" width="40" height="40" />
			<span class="d-flex flex-column lh-sm">
				<span class="fw-bold fs-5 text-white">{NOMBRE_APP}</span>
				<span class="lema d-none d-sm-block">Colegio y familia, siempre conectados</span>
			</span>
		</a>

		<div class="ms-auto d-flex align-items-center gap-2 gap-md-3">
			<span class="estado-conexion d-none d-md-inline" class:en-linea={tiempoReal.conectado}
				title={tiempoReal.conectado ? 'Conectado en tiempo real' : 'Reconectando...'}>
				<i class="bi bi-circle-fill"></i> {tiempoReal.conectado ? 'En línea' : 'Sin conexión'}
			</span>
			<CampanaNotificaciones />

			<div class="position-relative">
				<button class="btn btn-usuario d-flex align-items-center gap-2" onclick={() => (menuUsuario = !menuUsuario)}>
					<span class="avatar">{iniciales(sesion.usuario?.nombre)}</span>
					<span class="d-none d-md-flex flex-column text-start lh-sm">
						<span class="fw-semibold small">{sesion.usuario?.nombre}</span>
						<span class="rol-usuario">{ROLES[sesion.usuario?.rol] ?? ''}</span>
					</span>
					<i class="bi bi-chevron-down small"></i>
				</button>
				{#if menuUsuario}
					<button class="capa-cierre" aria-label="Cerrar" onclick={() => (menuUsuario = false)}></button>
					<div class="menu-flotante shadow-lg" style="min-width: 220px">
						<div class="px-3 py-2 border-bottom">
							<div class="fw-semibold small">{sesion.usuario?.nombre}</div>
							<div class="text-muted small text-truncate">{sesion.usuario?.correo}</div>
						</div>
						<a class="item-menu" href="/perfil" onclick={() => (menuUsuario = false)}><i class="bi bi-person-circle"></i> Mi perfil</a>
						<a class="item-menu" href="/notificaciones" onclick={() => (menuUsuario = false)}><i class="bi bi-bell"></i> Notificaciones</a>
						<button class="item-menu text-danger" onclick={salir}><i class="bi bi-box-arrow-right"></i> Cerrar sesión</button>
					</div>
				{/if}
			</div>
		</div>
	</div>
</header>
