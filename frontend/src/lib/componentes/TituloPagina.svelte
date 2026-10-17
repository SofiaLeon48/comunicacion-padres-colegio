<!-- Encabezado de cada módulo: icono, título, descripción y botones de acción. -->
<script>
	let { titulo, descripcion = '', icono = 'bi-grid', children } = $props();
</script>

<div class="titulo-pagina d-flex flex-wrap align-items-center gap-3 mb-4">
	<div class="icono-titulo"><i class="bi {icono}"></i></div>
	<div class="flex-grow-1">
		<h1 class="h4 fw-bold mb-0">{titulo}</h1>
		{#if descripcion}<p class="text-muted mb-0 small">{descripcion}</p>{/if}
	</div>
	{#if children}<div class="d-flex flex-wrap gap-2">{@render children()}</div>{/if}
</div>
