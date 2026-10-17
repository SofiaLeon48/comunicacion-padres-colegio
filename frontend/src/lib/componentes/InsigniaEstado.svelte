<!-- Insignia de color para estados (activo/inactivo, pendiente, confirmada...). -->
<script>
	const MAPA = {
		activo: ['Activo', 'success'],
		inactivo: ['Inactivo', 'secondary'],
		pendiente: ['Pendiente', 'warning'],
		confirmada: ['Confirmada', 'primary'],
		cancelada: ['Cancelada', 'secondary'],
		realizada: ['Realizada', 'success'],
		urgente: ['Urgente', 'danger'],
		normal: ['Normal', 'light'],
		leido: ['Leído', 'success'],
		sin_leer: ['Sin confirmar', 'warning']
	};
	let { estado, texto = null } = $props();
	let [etiqueta, color] = $derived(MAPA[estado] ?? [estado, 'secondary']);
</script>

<span class="badge rounded-pill text-bg-{color}">{texto ?? etiqueta}</span>
