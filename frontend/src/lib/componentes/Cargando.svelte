<!-- Indicador de carga y estado vacío. -->
<script>
	let { cargando = true, vacio = false, textoVacio = 'No hay información para mostrar.', icono = 'bi-inbox', children } = $props();
</script>

{#if cargando}
	<div class="text-center text-muted py-5">
		<div class="spinner-border text-primary mb-2" role="status"></div>
		<div class="small">Cargando información...</div>
	</div>
{:else if vacio}
	<div class="text-center text-muted py-5">
		<i class="bi {icono} d-block mb-2" style="font-size: 2.5rem; opacity: .5"></i>
		<div>{textoVacio}</div>
	</div>
{:else}
	{@render children?.()}
{/if}
