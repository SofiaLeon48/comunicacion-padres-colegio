<!-- Calendario mensual reutilizable. eventos: [{ fecha: Date|string, titulo, color, dato }] -->
<script>
	import { hora } from '$lib/formato.js';

	let { eventos = [], alSeleccionar = () => {} } = $props();

	const DIAS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];
	const MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre',
		'Octubre', 'Noviembre', 'Diciembre'];

	const hoy = new Date();
	let mes = $state(hoy.getMonth());
	let anio = $state(hoy.getFullYear());

	const clave = (d) => `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;

	const porDia = $derived.by(() => {
		const mapa = {};
		for (const e of eventos) {
			const d = new Date(e.fecha);
			(mapa[clave(d)] ??= []).push(e);
		}
		Object.values(mapa).forEach((l) => l.sort((a, b) => new Date(a.fecha) - new Date(b.fecha)));
		return mapa;
	});

	const celdas = $derived.by(() => {
		const primero = new Date(anio, mes, 1);
		const inicio = new Date(primero);
		inicio.setDate(1 - ((primero.getDay() + 6) % 7)); // semana empieza el lunes
		return Array.from({ length: 42 }, (_, i) => {
			const d = new Date(inicio);
			d.setDate(inicio.getDate() + i);
			return d;
		});
	});

	function mover(delta) {
		const d = new Date(anio, mes + delta, 1);
		mes = d.getMonth();
		anio = d.getFullYear();
	}
	function irHoy() {
		mes = hoy.getMonth();
		anio = hoy.getFullYear();
	}
</script>

<div class="calendario">
	<div class="d-flex align-items-center justify-content-between mb-3 flex-wrap gap-2">
		<h2 class="h5 mb-0 fw-semibold">{MESES[mes]} {anio}</h2>
		<div class="btn-group">
			<button class="btn btn-outline-secondary btn-sm" aria-label="Mes anterior" onclick={() => mover(-1)}><i class="bi bi-chevron-left"></i></button>
			<button class="btn btn-outline-secondary btn-sm" onclick={irHoy}>Hoy</button>
			<button class="btn btn-outline-secondary btn-sm" aria-label="Mes siguiente" onclick={() => mover(1)}><i class="bi bi-chevron-right"></i></button>
		</div>
	</div>
	<div class="cuadricula">
		{#each DIAS as d}<div class="dia-semana">{d}</div>{/each}
		{#each celdas as d (d.getTime())}
			<div class="celda" class:fuera={d.getMonth() !== mes} class:hoy={clave(d) === clave(hoy)}>
				<div class="numero">{d.getDate()}</div>
				{#each porDia[clave(d)] ?? [] as e}
					<button class="evento bg-{e.color}-subtle text-{e.color}-emphasis border-{e.color}" title={e.titulo}
						onclick={() => alSeleccionar(e.dato)}>
						<span class="fw-semibold">{hora(e.fecha)}</span> {e.titulo}
					</button>
				{/each}
			</div>
		{/each}
	</div>
</div>
