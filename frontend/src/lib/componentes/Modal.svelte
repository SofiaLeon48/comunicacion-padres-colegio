<!--
  Ventana modal reutilizable. Variantes de color según la acción (como CRUD del ejemplo):
  crear (verde) · ver (azul) · editar (naranja) · eliminar (rojo) · neutro
-->
<script>
	let {
		abierto = $bindable(false),
		titulo = '',
		icono = '',
		variante = 'neutro',
		tamano = '',
		children,
		pie,
		alCerrar = () => {}
	} = $props();

	const COLORES = {
		crear: 'bg-success text-white',
		ver: 'bg-primary text-white',
		editar: 'bg-warning text-dark',
		eliminar: 'bg-danger text-white',
		neutro: 'bg-light'
	};
	const ICONOS = { crear: 'bi-plus-circle', ver: 'bi-eye', editar: 'bi-pencil-square', eliminar: 'bi-trash' };

	function cerrar() {
		abierto = false;
		alCerrar();
	}

	function teclado(e) {
		if (abierto && e.key === 'Escape') cerrar();
	}
</script>

<svelte:window onkeydown={teclado} />

{#if abierto}
	<div class="modal d-block" tabindex="-1" role="dialog" aria-modal="true" aria-label={titulo}>
		<div class="modal-dialog modal-dialog-centered modal-dialog-scrollable {tamano ? 'modal-' + tamano : ''}">
			<div class="modal-content shadow-lg border-0">
				<div class="modal-header {COLORES[variante]}">
					<h5 class="modal-title fw-semibold">
						<i class="bi {icono || ICONOS[variante] || 'bi-window'} me-2"></i>{titulo}
					</h5>
					<button
						type="button"
						class="btn-close {variante === 'editar' || variante === 'neutro' ? '' : 'btn-close-white'}"
						aria-label="Cerrar"
						onclick={cerrar}
					></button>
				</div>
				<div class="modal-body">
					{@render children?.()}
				</div>
				{#if pie}
					<div class="modal-footer">{@render pie()}</div>
				{/if}
			</div>
		</div>
	</div>
	<div class="modal-backdrop show"></div>
{/if}
