<script>
	import { onMount } from 'svelte';
	import { api } from '$lib/api.js';
	import { error } from '$lib/avisos.svelte.js';
	import Cargando from '$lib/componentes/Cargando.svelte';
	import Grafico from '$lib/componentes/Grafico.svelte';
	import TablaDatos from '$lib/componentes/TablaDatos.svelte';
	import TarjetaIndicador from '$lib/componentes/TarjetaIndicador.svelte';
	import TituloPagina from '$lib/componentes/TituloPagina.svelte';
	import { esc, ESTADO_CITACION, fechaHora, insignia, ROLES } from '$lib/formato.js';

	let resumen = $state(null);
	let lectura = $state([]);
	let pendientes = $state([]);
	let citas = $state(null);
	let porGrupo = $state([]);

	onMount(async () => {
		try {
			[resumen, lectura, pendientes, citas, porGrupo] = await Promise.all([api.get('/reportes/resumen'), api.get('/reportes/lectura-comunicados'), api.get('/reportes/acudientes-pendientes'),
				api.get('/reportes/citaciones'), api.get('/reportes/actividad-grupos')]);
		} catch (e) {
			error(e);
		}
	});

	const promedio = $derived(lectura.length ? (lectura.reduce((s, x) => s + Number(x.porcentaje_lectura), 0) / lectura.length).toFixed(1) : 0);

	const colLectura = [
		{ titulo: 'Comunicado', campo: 'titulo', render: (v, x) => `${x.prioridad === 'urgente' ? '<i class="bi bi-exclamation-circle-fill text-danger me-1"></i>' : ''}<span class="fw-semibold">${esc(v)}</span>` },
		{ titulo: 'Dirigido a', campo: 'grupo' },
		{ titulo: 'Publicado', campo: 'fecha_publicacion', clase: 'text-nowrap', render: (v) => fechaHora(v), orden: (x) => x.fecha_publicacion },
		{ titulo: 'Destinatarios', campo: 'destinatarios' },
		{ titulo: 'Confirmaron', campo: 'confirmados' },
		{
			titulo: '% de lectura',
			campo: 'porcentaje_lectura',
			orden: (x) => Number(x.porcentaje_lectura),
			render: (v) => {
				const n = Number(v);
				const color = n >= 75 ? 'success' : n >= 40 ? 'warning' : 'danger';
				return `<div class="d-flex align-items-center gap-2" style="min-width:140px"><div class="progress flex-grow-1" style="height:8px"><div class="progress-bar bg-${color}" style="width:${n}%"></div></div><span class="small fw-semibold">${n}%</span></div>`;
			}
		}
	];
	const colPendientes = [
		{ titulo: 'Acudiente', campo: 'nombre', render: (v) => `<span class="fw-semibold">${esc(v)}</span>` },
		{ titulo: 'Correo', campo: 'correo' },
		{ titulo: 'Teléfono', campo: 'telefono' },
		{ titulo: 'Circulares sin confirmar', campo: 'pendientes', render: (v) => insignia(v, v >= 3 ? 'danger' : 'warning') }
	];
</script>

<svelte:head><title>Reportes · Conecta Escolar</title></svelte:head>

<TituloPagina titulo="Reportes y analítica" icono="bi-bar-chart-line" descripcion="Indicadores de lectura de circulares, citaciones y actividad por grupo." />

<Cargando cargando={!resumen}>
	{#if resumen}
		<div class="row g-3 mb-4">
			<div class="col-6 col-xl-3"><TarjetaIndicador titulo="Comunicados publicados" valor={resumen.comunicados} icono="bi-megaphone" /></div>
			<div class="col-6 col-xl-3"><TarjetaIndicador titulo="Lectura promedio" valor="{promedio}%" icono="bi-check2-all" color="success" /></div>
			<div class="col-6 col-xl-3"><TarjetaIndicador titulo="Asistencia a citaciones" valor="{resumen.asistencia_citaciones.porcentaje_asistencia}%" icono="bi-clipboard-check" color="warning" detalle="{resumen.asistencia_citaciones.registradas} registradas" /></div>
			<div class="col-6 col-xl-3"><TarjetaIndicador titulo="Mensajes enviados" valor={resumen.mensajes} icono="bi-chat-dots" color="info" /></div>
		</div>

		<div class="row g-3 mb-4">
			<div class="col-lg-8">
				<div class="tarjeta tarjeta-cuerpo h-100">
					<h2 class="h6 fw-semibold mb-3">Actividad por grupo</h2>
					<Grafico tipo="bar" etiquetas={porGrupo.map((c) => c.grupo)} series={[
						{ nombre: 'Comunicados', datos: porGrupo.map((c) => c.comunicados) },
						{ nombre: 'Mensajes', datos: porGrupo.map((c) => c.mensajes) },
						{ nombre: 'Citaciones', datos: porGrupo.map((c) => c.citaciones) }
					]} alto={280} />
				</div>
			</div>
			<div class="col-lg-4">
				<div class="tarjeta tarjeta-cuerpo h-100">
					<h2 class="h6 fw-semibold mb-3">Citaciones por estado</h2>
					<Grafico tipo="doughnut" etiquetas={citas.por_estado.map((c) => ESTADO_CITACION[c.estado_citacion]?.[0] ?? c.estado_citacion)}
						series={[{ nombre: 'Citaciones', datos: citas.por_estado.map((c) => c.total) }]} alto={280} />
				</div>
			</div>
		</div>

		<div class="tarjeta tarjeta-cuerpo mb-4">
			<h2 class="h6 fw-semibold mb-3"><i class="bi bi-check2-all me-2 text-success"></i>Lectura de circulares</h2>
			<TablaDatos columnas={colLectura} datos={lectura} ordenInicial={[[2, 'desc']]} />
		</div>

		<div class="row g-3 mb-4">
			<div class="col-lg-7">
				<div class="tarjeta tarjeta-cuerpo h-100">
					<h2 class="h6 fw-semibold mb-3"><i class="bi bi-hourglass-split me-2 text-warning"></i>Acudientes con circulares sin confirmar</h2>
					<TablaDatos columnas={colPendientes} datos={pendientes} porPagina={5} ordenInicial={[[3, 'desc']]} />
				</div>
			</div>
			<div class="col-lg-5">
				<div class="tarjeta tarjeta-cuerpo h-100">
					<h2 class="h6 fw-semibold mb-3">Usuarios por rol</h2>
					<Grafico tipo="doughnut" etiquetas={resumen.usuarios_por_rol.map((x) => ROLES[x.rol] ?? x.rol)}
						series={[{ nombre: 'Usuarios', datos: resumen.usuarios_por_rol.map((x) => x.total) }]} alto={240} />
				</div>
			</div>
		</div>

	{/if}
</Cargando>
