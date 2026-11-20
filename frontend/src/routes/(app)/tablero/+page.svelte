<!--
	Módulo Tablero: muestra el dashboard PUBLICADO por la API dentro de un <iframe>.
	La página publicada (/tablero/publico) tiene 4 indicadores, 6 gráficos (barras y circulares)
	y 2 filtros (grupo y periodo). El enlace se puede compartir o incrustar en otro sitio.
-->
<script>
	import { onDestroy, onMount } from 'svelte';
	import { api } from '$lib/api.js';
	import { error, exito } from '$lib/avisos.svelte.js';
	import Cargando from '$lib/componentes/Cargando.svelte';
	import Modal from '$lib/componentes/Modal.svelte';
	import TituloPagina from '$lib/componentes/TituloPagina.svelte';
	import { API_URL } from '$lib/config.js';

	let url = $state('');
	let alto = $state(900);
	let modalCompartir = $state(false);
	const codigo = $derived(`<iframe src="${url}" width="100%" height="900" style="border:0" title="Tablero Conecta Escolar"></iframe>`);

	onMount(async () => {
		try {
			const r = await api.get('/tablero/enlace');
			url = API_URL + r.ruta;
		} catch (e) {
			error(e);
		}
	});

	// La página del tablero avisa su altura para que el iframe no tenga barra de desplazamiento
	function alMensaje(e) {
		if (e.data?.tipo === 'tablero-altura' && e.origin === new URL(API_URL).origin) alto = Math.max(600, e.data.alto + 8);
	}
	onMount(() => window.addEventListener('message', alMensaje));
	onDestroy(() => typeof window !== 'undefined' && window.removeEventListener('message', alMensaje));

	async function copiar(texto, que) {
		try {
			await navigator.clipboard.writeText(texto);
			exito(`${que} copiado al portapapeles.`);
		} catch {
			error('No se pudo copiar. Selecciona el texto y cópialo manualmente.');
		}
	}
</script>

<svelte:head><title>Tablero · Conecta Escolar</title></svelte:head>

<TituloPagina titulo="Tablero" icono="bi-speedometer2"
	descripcion="Dashboard publicado: indicadores, gráficos y filtros por grupo y periodo, actualizado en tiempo real.">
	<button class="btn btn-outline-primary" onclick={() => (modalCompartir = true)} disabled={!url}>
		<i class="bi bi-share me-1"></i>Compartir
	</button>
	<a class="btn btn-primary" href={url} target="_blank" rel="noopener" class:disabled={!url}>
		<i class="bi bi-box-arrow-up-right me-1"></i>Abrir publicado
	</a>
</TituloPagina>

<Cargando cargando={!url}>
	<iframe src={url} title="Tablero de comunicación institucional" class="marco-tablero shadow-sm" style="height:{alto}px"
		loading="lazy"></iframe>
</Cargando>

<Modal bind:abierto={modalCompartir} variante="ver" tamano="lg" titulo="Compartir el tablero">
	<p class="text-muted small">El tablero está publicado en esta dirección. Cualquier persona con el enlace puede verlo (solo lectura).</p>
	<label class="form-label fw-semibold" for="t-url">Enlace publicado</label>
	<div class="input-group mb-3">
		<input id="t-url" class="form-control" readonly value={url} />
		<button class="btn btn-outline-primary" onclick={() => copiar(url, 'Enlace')}><i class="bi bi-clipboard"></i></button>
	</div>
	<label class="form-label fw-semibold" for="t-iframe">Código para incrustar (iframe)</label>
	<textarea id="t-iframe" class="form-control font-monospace small" rows="3" readonly>{codigo}</textarea>
	<button class="btn btn-sm btn-outline-primary mt-2" onclick={() => copiar(codigo, 'Código iframe')}><i class="bi bi-code-slash me-1"></i>Copiar código</button>
	{#snippet pie()}
		<button class="btn btn-light" onclick={() => (modalCompartir = false)}>Cerrar</button>
	{/snippet}
</Modal>
