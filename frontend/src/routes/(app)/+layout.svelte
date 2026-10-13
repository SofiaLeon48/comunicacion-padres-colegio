<!--
  Plantilla de todas las páginas internas: Encabezado + Menú + contenido + Pie.
  Protege las rutas: sin sesión → login; módulo no permitido para el rol → inicio.
-->
<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { onDestroy, onMount, untrack } from 'svelte';
	import { api } from '$lib/api.js';
	import { avisar } from '$lib/avisos.svelte.js';
	import Avisos from '$lib/componentes/Avisos.svelte';
	import Encabezado from '$lib/componentes/Encabezado.svelte';
	import MenuNav from '$lib/componentes/MenuNav.svelte';
	import PiePagina from '$lib/componentes/PiePagina.svelte';
	import { actualizarModulos, sesion } from '$lib/sesion.svelte.js';
	import { conectar, desconectar, refrescarNotificaciones } from '$lib/tiempoReal.svelte.js';

	let { children } = $props();

	// Rutas de módulos conocidas: si la ruta pertenece a un módulo, el rol debe tenerlo asignado
	const RUTAS_LIBRES = ['/perfil', '/notificaciones'];
	let verificado = $state(false);
	const listo = $derived(!!sesion.token && verificado);

	onMount(async () => {
		if (!sesion.token) return goto('/login', { replaceState: true });
		conectar();
		refrescarNotificaciones();
		try {
			actualizarModulos(await api.get('/auth/mis-modulos')); // el menú siempre sale de la BD
		} catch {
			/* sin conexión: se usan los módulos guardados; si el token expiró, el cliente redirige */
		}
		verificado = true;
	});

	onDestroy(desconectar);

	const rutaPermitida = $derived.by(() => {
		const ruta = page.url.pathname;
		if (RUTAS_LIBRES.some((r) => ruta.startsWith(r))) return true;
		return sesion.modulos.some((m) => ruta === m.ruta || ruta.startsWith(m.ruta + '/'));
	});

	$effect(() => {
		if (!verificado || !sesion.token || !sesion.modulos.length) return;
		if (!rutaPermitida) {
			const destino = sesion.modulos[0]?.ruta ?? '/login';
			untrack(() => {
				avisar('Tu rol no tiene acceso a ese módulo.', 'warning', 'Acceso restringido');
				goto(destino, { replaceState: true });
			});
		}
	});
</script>

{#if listo}
	<div class="app-contenedor">
		<Encabezado />
		<MenuNav />
		<main class="contenido-principal">
			<div class="container-xl">
				{#if rutaPermitida}{@render children()}{/if}
			</div>
		</main>
		<PiePagina />
	</div>
	<Avisos />
{/if}
