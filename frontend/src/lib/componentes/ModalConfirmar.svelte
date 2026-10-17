<!-- Confirmación antes de eliminar o desactivar algo. -->
<script>
	import Modal from './Modal.svelte';

	let {
		abierto = $bindable(false),
		titulo = 'Confirmar eliminación',
		mensaje = '¿Estás seguro?',
		detalle = '',
		textoBoton = 'Eliminar',
		cargando = false,
		alConfirmar
	} = $props();
</script>

<Modal bind:abierto {titulo} variante="eliminar">
	<div class="text-center py-2">
		<i class="bi bi-exclamation-triangle text-danger" style="font-size: 3rem"></i>
		<p class="fs-5 fw-semibold mt-2 mb-1">{mensaje}</p>
		<p class="text-muted small mb-3">Podrás reactivarlo más adelante si lo necesitas.</p>
		{#if detalle}
			<div class="alert alert-light border text-start mb-0"><i class="bi bi-info-circle me-2"></i>{detalle}</div>
		{/if}
	</div>
	{#snippet pie()}
		<button class="btn btn-light" onclick={() => (abierto = false)}>Cancelar</button>
		<button class="btn btn-danger" disabled={cargando} onclick={alConfirmar}>
			{#if cargando}<span class="spinner-border spinner-border-sm me-1"></span>{/if}{textoBoton}
		</button>
	{/snippet}
</Modal>
