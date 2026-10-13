<script>
	import { onDestroy, onMount } from 'svelte';
	import { api } from '$lib/api.js';
	import { error } from '$lib/avisos.svelte.js';
	import Cargando from '$lib/componentes/Cargando.svelte';
	import Grafico from '$lib/componentes/Grafico.svelte';
	import InsigniaEstado from '$lib/componentes/InsigniaEstado.svelte';
	import TarjetaIndicador from '$lib/componentes/TarjetaIndicador.svelte';
	import { ESTADO_CITACION, fecha, fechaHora, fechaLarga, haceCuanto, JORNADAS, ROLES, saludo } from '$lib/formato.js';
	import { sesion, tieneModulo } from '$lib/sesion.svelte.js';
	import { alRecibir } from '$lib/tiempoReal.svelte.js';

	let d = $state(null);
	const nombre = $derived(sesion.usuario?.nombre?.split(' ')[0] ?? '');

	async function cargar() {
		try {
			d = await api.get('/inicio/resumen');
		} catch (e) {
			error(e);
		}
	}

	onMount(cargar);
	const quitar = alRecibir((m) => m.evento === 'notificacion' && cargar());
	onDestroy(quitar);
	const enlace = (clave, ruta) => (tieneModulo(clave) ? ruta : null);
</script>

<svelte:head><title>Inicio · Conecta Escolar</title></svelte:head>

<div class="tarjeta tarjeta-cuerpo mb-4 d-flex flex-wrap align-items-center gap-3"
	style="background: linear-gradient(100deg, #ffffff 55%, #e6efff 100%)">
	<div class="flex-grow-1">
		<div class="text-muted small">{fechaLarga().charAt(0).toUpperCase() + fechaLarga().slice(1)}</div>
		<h1 class="h3 fw-bold mb-1">{saludo()}, {nombre} 👋</h1>
		<p class="mb-0 text-muted">
			{#if sesion.usuario?.rol === 'acudiente'}Aquí tienes lo más importante sobre tus hijos.
			{:else if sesion.usuario?.rol === 'docente'}Este es el resumen de tus cursos y comunicaciones.
			{:else}Este es el estado general de la comunicación institucional.{/if}
		</p>
	</div>
	<span class="badge text-bg-primary fs-6 px-3 py-2"><i class="bi bi-person-badge me-1"></i>{ROLES[sesion.usuario?.rol]}</span>
</div>

<Cargando cargando={!d}>
	{#if d}
		<!-- Indicadores -->
		<div class="row g-3 mb-4">
			{#if d.rol === 'coordinacion'}
				<div class="col-6 col-xl-3"><TarjetaIndicador titulo="Usuarios activos" valor={d.indicadores.usuarios_activos} icono="bi-people" href={enlace('usuarios', '/usuarios')} /></div>
				<div class="col-6 col-xl-3"><TarjetaIndicador titulo="Estudiantes" valor={d.indicadores.estudiantes} icono="bi-mortarboard" color="success" detalle="{d.indicadores.cursos} cursos" href={enlace('estudiantes', '/estudiantes')} /></div>
				<div class="col-6 col-xl-3"><TarjetaIndicador titulo="Lectura promedio de circulares" valor="{d.lectura_promedio}%" icono="bi-check2-all" color="info" href={enlace('reportes', '/reportes')} /></div>
				<div class="col-6 col-xl-3"><TarjetaIndicador titulo="Citaciones próximas" valor={d.total_citaciones_proximas} icono="bi-calendar-event" color="warning" href={enlace('citaciones', '/citaciones')} /></div>
			{:else if d.rol === 'docente'}
				<div class="col-6 col-xl-3"><TarjetaIndicador titulo="Comunicados publicados" valor={d.comunicados_publicados} icono="bi-megaphone" href={enlace('comunicados', '/comunicados')} /></div>
				<div class="col-6 col-xl-3"><TarjetaIndicador titulo="Lectura de mis circulares" valor="{d.lectura_promedio}%" icono="bi-check2-all" color="success" /></div>
				<div class="col-6 col-xl-3"><TarjetaIndicador titulo="Citaciones próximas" valor={d.total_citaciones_proximas} icono="bi-calendar-event" color="warning" href={enlace('citaciones', '/citaciones')} /></div>
				<div class="col-6 col-xl-3"><TarjetaIndicador titulo="Mensajes sin leer" valor={d.mensajes_no_leidos} icono="bi-chat-dots" color="info" href={enlace('mensajes', '/mensajes')} /></div>
			{:else}
				<div class="col-6 col-xl-3"><TarjetaIndicador titulo="Circulares por confirmar" valor={d.comunicados_pendientes} icono="bi-megaphone" color="danger" href={enlace('comunicados', '/comunicados')} /></div>
				<div class="col-6 col-xl-3"><TarjetaIndicador titulo="Citaciones próximas" valor={d.total_citaciones_proximas} icono="bi-calendar-event" color="warning" href={enlace('citaciones', '/citaciones')} /></div>
				<div class="col-6 col-xl-3"><TarjetaIndicador titulo="Mensajes sin leer" valor={d.mensajes_no_leidos} icono="bi-chat-dots" color="success" href={enlace('mensajes', '/mensajes')} /></div>
				<div class="col-6 col-xl-3"><TarjetaIndicador titulo="Notificaciones nuevas" valor={d.notificaciones_no_leidas} icono="bi-bell" color="info" href="/notificaciones" /></div>
			{/if}
		</div>

		<!-- Bloque específico del rol -->
		{#if d.rol === 'acudiente'}
			<h2 class="h5 fw-semibold mb-3"><i class="bi bi-people me-2 text-primary"></i>Mis hijos</h2>
			<div class="row g-3 mb-4">
				{#each d.hijos as h}
					<div class="col-md-6 col-xl-4">
						<div class="tarjeta tarjeta-cuerpo h-100 d-flex gap-3 align-items-center">
							<div class="icono-indicador bg-success-subtle text-success"><i class="bi bi-mortarboard"></i></div>
							<div>
								<div class="fw-semibold">{h.nombre}</div>
								<div class="small text-muted">Curso {h.curso_nombre} · Jornada {JORNADAS[h.curso_jornada]}</div>
								<div class="small text-muted">Director(a): {h.director_nombre ?? 'Sin asignar'}</div>
							</div>
						</div>
					</div>
				{/each}
			</div>
		{:else if d.rol === 'docente' && d.mis_cursos.length}
			<h2 class="h5 fw-semibold mb-3"><i class="bi bi-easel me-2 text-primary"></i>Cursos que diriges</h2>
			<div class="row g-3 mb-4">
				{#each d.mis_cursos as c}
					<div class="col-md-4">
						<div class="tarjeta tarjeta-cuerpo d-flex justify-content-between align-items-center">
							<div><div class="fw-bold fs-5">{c.nombre}</div><div class="small text-muted">Jornada {JORNADAS[c.jornada]}</div></div>
							<div class="text-end"><div class="fw-bold fs-4">{c.estudiantes}</div><div class="small text-muted">estudiantes</div></div>
						</div>
					</div>
				{/each}
			</div>
		{:else if d.rol === 'coordinacion'}
			<div class="row g-3 mb-4">
				<div class="col-lg-8">
					<div class="tarjeta tarjeta-cuerpo h-100">
						<h2 class="h6 fw-semibold mb-3">Porcentaje de lectura por circular</h2>
						<Grafico tipo="bar" etiquetas={d.lectura_comunicados.map((x) => x.titulo.length > 28 ? x.titulo.slice(0, 28) + '…' : x.titulo)}
							series={[{ nombre: '% de lectura', datos: d.lectura_comunicados.map((x) => Number(x.porcentaje_lectura)) }]}
							opciones={{ indexAxis: 'y', scales: { x: { min: 0, max: 100 } } }} />
					</div>
				</div>
				<div class="col-lg-4">
					<div class="tarjeta tarjeta-cuerpo h-100">
						<h2 class="h6 fw-semibold mb-3">Usuarios por rol</h2>
						<Grafico tipo="doughnut" etiquetas={d.usuarios_por_rol.map((x) => ROLES[x.rol] ?? x.rol)}
							series={[{ nombre: 'Usuarios', datos: d.usuarios_por_rol.map((x) => x.total) }]} />
					</div>
				</div>
			</div>
		{/if}

		<!-- Listas -->
		<div class="row g-3">
			<div class="col-lg-7">
				<div class="tarjeta h-100">
					<div class="d-flex justify-content-between align-items-center px-4 pt-3">
						<h2 class="h6 fw-semibold mb-0"><i class="bi bi-megaphone me-2 text-primary"></i>Últimos comunicados</h2>
						{#if tieneModulo('comunicados')}<a href="/comunicados" class="small">Ver todos</a>{/if}
					</div>
					<div class="list-group list-group-flush mt-2 mb-2">
						{#each d.ultimos_comunicados as c}
							<a href="/comunicados" class="list-group-item list-group-item-action px-4 py-3 border-0">
								<div class="d-flex justify-content-between gap-2">
									<div class="min-w-0">
										<div class="fw-semibold text-truncate">
											{#if c.prioridad === 'urgente'}<i class="bi bi-exclamation-circle-fill text-danger me-1"></i>{/if}{c.titulo}
										</div>
										<div class="small text-muted">{c.curso_nombre ? `Curso ${c.curso_nombre}` : 'Todo el colegio'} · {c.autor_nombre} · {haceCuanto(c.fecha_publicacion)}</div>
									</div>
									{#if d.rol === 'acudiente' && c.requiere_confirmacion}
										<span><InsigniaEstado estado={c.confirmado_por_mi ? 'leido' : 'sin_leer'} texto={c.confirmado_por_mi ? 'Confirmado' : 'Por confirmar'} /></span>
									{/if}
								</div>
							</a>
						{:else}
							<div class="text-muted small px-4 py-3">No hay comunicados recientes.</div>
						{/each}
					</div>
				</div>
			</div>
			<div class="col-lg-5">
				<div class="tarjeta h-100">
					<div class="d-flex justify-content-between align-items-center px-4 pt-3">
						<h2 class="h6 fw-semibold mb-0"><i class="bi bi-calendar-event me-2 text-warning"></i>Próximas citaciones</h2>
						{#if tieneModulo('citaciones')}<a href="/citaciones" class="small">Ver calendario</a>{/if}
					</div>
					<div class="list-group list-group-flush mt-2 mb-2">
						{#each d.proximas_citaciones as c}
							<a href="/citaciones" class="list-group-item list-group-item-action px-4 py-3 border-0 d-flex gap-3 align-items-center">
								<div class="text-center rounded-3 bg-warning-subtle px-2 py-1" style="min-width: 56px">
									<div class="small fw-semibold text-warning-emphasis">{fecha(c.fecha_hora).split(' ').slice(0, 2).join(' ')}</div>
								</div>
								<div class="min-w-0 flex-grow-1">
									<div class="fw-semibold text-truncate">{c.estudiante_nombre} <span class="text-muted fw-normal small">({c.curso_nombre})</span></div>
									<div class="small text-muted text-truncate">{c.motivo}</div>
									<div class="small text-muted">{fechaHora(c.fecha_hora)}</div>
								</div>
								<InsigniaEstado estado={c.estado_citacion} texto={ESTADO_CITACION[c.estado_citacion]?.[0]} />
							</a>
						{:else}
							<div class="text-muted small px-4 py-3">No hay citaciones próximas.</div>
						{/each}
					</div>
				</div>
			</div>
		</div>
	{/if}
</Cargando>
