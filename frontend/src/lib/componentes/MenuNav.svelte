<!--
  Menú de navegación. Las opciones NO están escritas en el código:
  salen de la base de datos (tabla rol_modulo) según el rol del usuario.
-->
<script>
	import { page } from '$app/state';
	import { sesion } from '$lib/sesion.svelte.js';

	let abiertoMovil = $state(false);
	const activo = (ruta) => page.url.pathname === ruta || page.url.pathname.startsWith(ruta + '/');
	const actual = $derived(sesion.modulos.find((m) => activo(m.ruta)));
</script>

<nav class="menu-nav border-bottom bg-white" aria-label="Menú principal">
	<div class="container-xl">
		<button class="btn w-100 d-lg-none d-flex align-items-center justify-content-between py-2"
			aria-expanded={abiertoMovil} onclick={() => (abiertoMovil = !abiertoMovil)}>
			<span><i class="bi {actual?.icono ?? 'bi-list'} me-2"></i>{actual?.nombre ?? 'Menú'}</span>
			<i class="bi {abiertoMovil ? 'bi-x-lg' : 'bi-list'} fs-5"></i>
		</button>
		<ul class="nav-modulos" class:abierto={abiertoMovil}>
			{#each sesion.modulos as m (m.clave)}
				<li>
					<a href={m.ruta} class:activo={activo(m.ruta)} title={m.descripcion}
						onclick={() => (abiertoMovil = false)}>
						<i class="bi {m.icono}"></i><span>{m.nombre}</span>
					</a>
				</li>
			{/each}
		</ul>
	</div>
</nav>
