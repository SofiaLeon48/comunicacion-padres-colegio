<!-- Contenedor de avisos emergentes (toasts). -->
<script>
	import { avisos, quitarAviso } from '$lib/avisos.svelte.js';
	const ICONOS = { success: 'bi-check-circle-fill', danger: 'bi-x-octagon-fill', primary: 'bi-bell-fill', warning: 'bi-exclamation-triangle-fill' };
</script>

<div class="toast-container position-fixed bottom-0 end-0 p-3" style="z-index: 2000">
	{#each avisos.lista as a (a.id)}
		<div class="toast show border-0 shadow aviso-{a.tipo}" role="alert">
			<div class="d-flex align-items-start p-3 gap-2">
				<i class="bi {ICONOS[a.tipo] ?? 'bi-info-circle-fill'} text-{a.tipo} fs-5"></i>
				<div class="flex-grow-1 small">
					{#if a.titulo}<div class="fw-semibold mb-1">{a.titulo}</div>{/if}
					<div>{a.texto}</div>
				</div>
				<button type="button" class="btn-close btn-sm" aria-label="Cerrar" onclick={() => quitarAviso(a.id)}></button>
			</div>
		</div>
	{/each}
</div>
