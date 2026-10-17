<!-- Pie de página. -->
<script>
	import { NOMBRE_APP, NOMBRE_COLEGIO } from '$lib/config.js';
	const anio = new Date().getFullYear();
</script>

<footer class="pie-pagina mt-auto">
	<div class="container-xl d-flex flex-column flex-md-row align-items-center justify-content-between gap-2 py-3">
		<div class="d-flex align-items-center gap-2">
			<img src="/favicon.svg" alt="" width="26" height="26" />
			<span class="fw-semibold">{NOMBRE_APP}</span>
			<span class="opacity-75 small">· {NOMBRE_COLEGIO} · © {anio}</span>
		</div>
		<div class="small opacity-75 d-flex gap-3">
			<span><i class="bi bi-shield-check me-1"></i>Canal oficial de comunicación</span>
			<span>v1.0</span>
		</div>
	</div>
</footer>
