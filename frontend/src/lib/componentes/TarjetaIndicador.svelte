<!-- Tarjeta con un número clave (KPI). -->
<script>
	let { titulo, valor, icono = 'bi-graph-up', color = 'primary', detalle = '', href = null } = $props();
</script>

<svelte:element this={href ? 'a' : 'div'} {href} class="card tarjeta-indicador h-100 border-0 shadow-sm text-decoration-none">
	<div class="card-body d-flex align-items-center gap-3">
		<div class="icono-indicador bg-{color}-subtle text-{color}"><i class="bi {icono}"></i></div>
		<div class="min-w-0">
			<div class="text-muted small text-truncate">{titulo}</div>
			<div class="fs-3 fw-bold lh-1 text-body">{valor ?? '—'}</div>
			{#if detalle}<div class="small text-muted mt-1">{detalle}</div>{/if}
		</div>
	</div>
</svelte:element>
