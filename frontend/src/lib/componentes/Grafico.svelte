<!-- Gráfico reutilizable con Chart.js (barras, dona, líneas). -->
<script>
	import { onDestroy, onMount } from 'svelte';

	let { tipo = 'bar', etiquetas = [], series = [], alto = 260, opciones = {} } = $props();
	const PALETA = ['#1d6fd1', '#1fa37a', '#f2a93b', '#e5534b', '#7b61c9', '#2bb3c0', '#8a96a8'];

	let lienzo;
	let grafico = null;
	let Chart = null;

	function config() {
		const circular = tipo === 'doughnut' || tipo === 'pie';
		return {
			type: tipo,
			data: {
				labels: $state.snapshot(etiquetas),
				datasets: series.map((s, i) => ({
					label: s.nombre,
					data: $state.snapshot(s.datos),
					backgroundColor: circular ? PALETA : (s.color ?? PALETA[i % PALETA.length]),
					borderColor: circular ? '#fff' : (s.color ?? PALETA[i % PALETA.length]),
					borderWidth: circular ? 2 : 0,
					borderRadius: tipo === 'bar' ? 6 : 0,
					maxBarThickness: 38
				}))
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				plugins: { legend: { position: 'bottom', display: circular || series.length > 1 } },
				...(circular ? { cutout: tipo === 'doughnut' ? '62%' : 0 } : { scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } }),
				...opciones
			}
		};
	}

	onMount(async () => {
		const m = await import('chart.js/auto');
		Chart = m.default;
		grafico = new Chart(lienzo, config());
	});

	$effect(() => {
		config(); // registra dependencias
		if (grafico && Chart) {
			grafico.destroy();
			grafico = new Chart(lienzo, config());
		}
	});

	onDestroy(() => grafico?.destroy());
</script>

<div style="position: relative; height: {alto}px">
	<canvas bind:this={lienzo}></canvas>
</div>
