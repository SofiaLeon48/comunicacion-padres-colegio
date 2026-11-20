<!--
	Módulo Reporte: el usuario elige el tipo de reporte y los criterios (rango de fechas,
	grupo y estado/prioridad), ve la vista previa y lo exporta en PDF o Excel, o lo envía
	por correo. Opcionalmente agrega un análisis escrito por IA (Gemini).
-->
<script>
	import { onMount } from 'svelte';
	import { api, descargar, qs } from '$lib/api.js';
	import { error, exito } from '$lib/avisos.svelte.js';
	import { guardarArchivo } from '$lib/archivos.js';
	import Cargando from '$lib/componentes/Cargando.svelte';
	import Modal from '$lib/componentes/Modal.svelte';
	import SelectorLista from '$lib/componentes/SelectorLista.svelte';
	import TablaDatos from '$lib/componentes/TablaDatos.svelte';
	import TituloPagina from '$lib/componentes/TituloPagina.svelte';
	import { esc, fechaHora, insignia } from '$lib/formato.js';
	import { sesion } from '$lib/sesion.svelte.js';

	let opciones = $state(null);
	let criterios = $state({ tipo: 'comunicados', desde: '', hasta: '', grupo_id: null, estado: '' });
	let reporte = $state(null);
	let consultando = $state(false);
	let exportando = $state('');
	let analisis = $state('');
	let analizando = $state(false);
	let incluirAnalisis = $state(false);
	let modalCorreo = $state(false);
	let envio = $state({ correo: '', formato: 'pdf', mensaje: '' });
	let enviando = $state(false);

	const tipoActual = $derived(opciones?.tipos.find((t) => t.valor === criterios.tipo));
	const params = () => ({ ...criterios, grupo_id: criterios.grupo_id ?? '' });

	const COLORES_ESTADO = {
		Pendiente: 'warning', Confirmada: 'info', Realizada: 'success', Cancelada: 'secondary',
		Urgente: 'danger', Normal: 'secondary', Asistió: 'success', 'No asistió': 'danger', 'Sin registrar': 'light'
	};

	const columnas = $derived(
		(reporte?.columnas ?? []).map((c) => ({
			titulo: c.titulo,
			campo: c.clave,
			clase: c.tipo === 'fechahora' ? 'text-nowrap' : '',
			orden: c.tipo === 'fechahora' ? (f) => f[c.clave] : c.tipo === 'porcentaje' ? (f) => Number(f[c.clave] ?? -1) : undefined,
			render: (v) => {
				if (c.tipo === 'fechahora') return fechaHora(v);
				if (c.tipo === 'porcentaje') {
					if (v === null) return '<span class="text-muted small">No aplica</span>';
					const n = Number(v), color = n >= 75 ? 'success' : n >= 40 ? 'warning' : 'danger';
					return `<div class="d-flex align-items-center gap-2" style="min-width:120px"><div class="progress flex-grow-1" style="height:7px"><div class="progress-bar bg-${color}" style="width:${n}%"></div></div><span class="small fw-semibold">${n}%</span></div>`;
				}
				if (['prioridad', 'estado', 'asistencia'].includes(c.clave)) return insignia(esc(v), COLORES_ESTADO[v] ?? 'secondary');
				return esc(v);
			}
		}))
	);

	onMount(async () => {
		try {
			opciones = await api.get('/reportes/opciones');
			envio.correo = sesion.usuario?.correo ?? '';
			await consultar();
		} catch (e) {
			error(e);
		}
	});

	async function consultar(e) {
		e?.preventDefault();
		if (criterios.desde && criterios.hasta && criterios.desde > criterios.hasta)
			return error('La fecha "desde" no puede ser posterior a la fecha "hasta".');
		consultando = true;
		analisis = '';
		try {
			reporte = await api.get('/reportes/datos' + qs(params()));
		} catch (err) {
			error(err);
		} finally {
			consultando = false;
		}
	}

	function cambiarTipo() {
		criterios.estado = '';
		consultar();
	}

	function limpiar() {
		criterios = { tipo: criterios.tipo, desde: '', hasta: '', grupo_id: null, estado: '' };
		consultar();
	}

	function rapido(dias) {
		const hoy = new Date(), ini = new Date();
		ini.setDate(hoy.getDate() - dias);
		const iso = (d) => new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
		criterios.desde = iso(ini);
		criterios.hasta = iso(hoy);
		consultar();
	}

	async function exportar(formato) {
		exportando = formato;
		try {
			const { blob, nombre } = await descargar('/reportes/exportar' + qs({ ...params(), formato, analisis: incluirAnalisis && opciones.ia_habilitada }),
				`reporte.${formato === 'pdf' ? 'pdf' : 'xlsx'}`);
			await guardarArchivo(blob, nombre);
			exito(`Reporte ${formato === 'pdf' ? 'PDF' : 'Excel'} generado.`);
		} catch (err) {
			error(err);
		} finally {
			exportando = '';
		}
	}

	async function analizar() {
		analizando = true;
		try {
			analisis = (await api.get('/reportes/analisis' + qs(params()))).analisis;
		} catch (err) {
			error(err);
		} finally {
			analizando = false;
		}
	}

	async function enviarCorreo(e) {
		e.preventDefault();
		enviando = true;
		try {
			const r = await api.post('/reportes/enviar', {
				...criterios, grupo_id: criterios.grupo_id || null, desde: criterios.desde || null, hasta: criterios.hasta || null,
				estado: criterios.estado || null, formato: envio.formato, correo: envio.correo,
				mensaje: envio.mensaje || null, incluir_analisis: incluirAnalisis && opciones.ia_habilitada
			});
			exito(r.mensaje);
			modalCorreo = false;
		} catch (err) {
			error(err);
		} finally {
			enviando = false;
		}
	}
</script>

<svelte:head><title>Reportes · Conecta Escolar</title></svelte:head>

<TituloPagina titulo="Reportes" icono="bi-file-earmark-bar-graph"
	descripcion="Genera reportes en PDF o Excel con filtros por fecha, grupo y estado, y envíalos por correo." />

<Cargando cargando={!opciones}>
	{#if opciones}
		<!-- Criterios -->
		<form class="tarjeta tarjeta-cuerpo mb-3" onsubmit={consultar}>
			<div class="row g-3 align-items-end">
				<div class="col-lg-3 col-md-6">
					<label class="form-label fw-semibold" for="r-tipo">Tipo de reporte</label>
					<select id="r-tipo" class="form-select" bind:value={criterios.tipo} onchange={cambiarTipo}>
						{#each opciones.tipos as t}<option value={t.valor}>{t.titulo.replace('Reporte de ', '').replace(/^./, (l) => l.toUpperCase())}</option>{/each}
					</select>
				</div>
				<div class="col-lg-2 col-6">
					<label class="form-label fw-semibold" for="r-desde">Desde</label>
					<input id="r-desde" type="date" class="form-control" bind:value={criterios.desde} />
				</div>
				<div class="col-lg-2 col-6">
					<label class="form-label fw-semibold" for="r-hasta">Hasta</label>
					<input id="r-hasta" type="date" class="form-control" bind:value={criterios.hasta} />
				</div>
				<div class="col-lg-2 col-md-6">
					<SelectorLista bind:valor={criterios.grupo_id} url="/catalogos/grupos" etiqueta="Grupo" opcionVacia="Todos los grupos" />
				</div>
				<div class="col-lg-2 col-md-6">
					<label class="form-label fw-semibold" for="r-estado">{tipoActual?.estado_nombre}</label>
					<select id="r-estado" class="form-select" bind:value={criterios.estado}>
						<option value="">Todos</option>
						{#each tipoActual?.estados ?? [] as e}<option value={e}>{e[0].toUpperCase() + e.slice(1)}</option>{/each}
					</select>
				</div>
				<div class="col-lg-1 col-12 d-grid">
					<button class="btn btn-primary" disabled={consultando}><i class="bi bi-search"></i><span class="d-lg-none ms-1">Consultar</span></button>
				</div>
			</div>
			<div class="d-flex flex-wrap gap-2 mt-3 small align-items-center">
				<span class="text-muted">Rápido:</span>
				<button type="button" class="btn btn-sm btn-outline-secondary" onclick={() => rapido(7)}>Últimos 7 días</button>
				<button type="button" class="btn btn-sm btn-outline-secondary" onclick={() => rapido(30)}>Últimos 30 días</button>
				<button type="button" class="btn btn-sm btn-outline-secondary" onclick={() => rapido(90)}>Últimos 3 meses</button>
				<button type="button" class="btn btn-sm btn-link text-decoration-none" onclick={limpiar}>Quitar filtros</button>
			</div>
		</form>

		{#if reporte}
			<!-- Acciones -->
			<div class="tarjeta tarjeta-cuerpo mb-3">
				<div class="d-flex flex-wrap align-items-center gap-2">
					<div class="me-auto">
						<h2 class="h6 fw-bold mb-0">{reporte.titulo}</h2>
						<div class="small text-muted">{Object.entries(reporte.criterios).map(([k, v]) => `${k}: ${v}`).join(' · ')}</div>
					</div>
					{#if opciones.ia_habilitada}
						<div class="form-check form-switch me-2">
							<input class="form-check-input" type="checkbox" id="r-ia" bind:checked={incluirAnalisis} />
							<label class="form-check-label small" for="r-ia">Incluir análisis IA</label>
						</div>
					{/if}
					<button class="btn btn-danger" onclick={() => exportar('pdf')} disabled={!!exportando}>
						{#if exportando === 'pdf'}<span class="spinner-border spinner-border-sm me-1"></span>{:else}<i class="bi bi-file-earmark-pdf me-1"></i>{/if}PDF
					</button>
					<button class="btn btn-success" onclick={() => exportar('excel')} disabled={!!exportando}>
						{#if exportando === 'excel'}<span class="spinner-border spinner-border-sm me-1"></span>{:else}<i class="bi bi-file-earmark-excel me-1"></i>{/if}Excel
					</button>
					<button class="btn btn-outline-primary" onclick={() => (modalCorreo = true)}
						title={opciones.correo_habilitado ? '' : 'El servidor aún no tiene configurado el correo'}>
						<i class="bi bi-envelope me-1"></i>Enviar por correo
					</button>
				</div>

				<div class="row g-3 mt-1">
					{#each Object.entries(reporte.resumen) as [k, v]}
						<div class="col-6 col-lg-3">
							<div class="border rounded-3 p-2 text-center bg-light">
								<div class="fs-4 fw-bold text-primary">{v}</div>
								<div class="small text-muted">{k}</div>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Análisis con IA -->
			{#if opciones.ia_habilitada}
				<div class="tarjeta tarjeta-cuerpo mb-3 caja-ia">
					<div class="d-flex flex-wrap align-items-center gap-2">
						<div class="me-auto"><i class="bi bi-stars text-ia me-1"></i><span class="fw-semibold text-ia">Análisis con inteligencia artificial</span>
							<span class="small text-muted d-block">Gemini lee los datos filtrados y propone hallazgos y recomendaciones.</span></div>
						<button class="btn btn-sm btn-ia" onclick={analizar} disabled={analizando || !reporte.filas.length}>
							{#if analizando}<span class="spinner-border spinner-border-sm me-1"></span>Analizando…{:else}<i class="bi bi-magic me-1"></i>Analizar reporte{/if}
						</button>
					</div>
					{#if analisis}<div class="analisis-ia mt-3 small bg-white rounded-3 p-3 border">{analisis}</div>{/if}
				</div>
			{/if}

			<!-- Vista previa -->
			<div class="tarjeta tarjeta-cuerpo">
				<h2 class="h6 fw-semibold mb-3">Vista previa <span class="text-muted fw-normal">({reporte.filas.length} registros)</span></h2>
				{#key reporte}
					<TablaDatos {columnas} datos={reporte.filas} porPagina={10} />
				{/key}
			</div>
		{/if}
	{/if}
</Cargando>

<Modal bind:abierto={modalCorreo} variante="crear" titulo="Enviar reporte por correo">
	{#if opciones && !opciones.correo_habilitado}
		<div class="alert alert-warning small"><i class="bi bi-exclamation-triangle me-1"></i>El servidor aún no tiene configurado el servicio de correo (Brevo).</div>
	{/if}
	<form id="form-correo" onsubmit={enviarCorreo} class="row g-3">
		<div class="col-12">
			<label class="form-label" for="e-correo">Correo del destinatario <span class="text-danger">*</span></label>
			<input id="e-correo" type="email" class="form-control" bind:value={envio.correo} required placeholder="nombre@correo.com" />
		</div>
		<div class="col-12">
			<span class="form-label d-block">Formato del adjunto</span>
			<div class="btn-group w-100" role="group">
				<input type="radio" class="btn-check" id="f-pdf" value="pdf" bind:group={envio.formato} />
				<label class="btn btn-outline-danger" for="f-pdf"><i class="bi bi-file-earmark-pdf me-1"></i>PDF</label>
				<input type="radio" class="btn-check" id="f-xlsx" value="excel" bind:group={envio.formato} />
				<label class="btn btn-outline-success" for="f-xlsx"><i class="bi bi-file-earmark-excel me-1"></i>Excel</label>
			</div>
		</div>
		<div class="col-12">
			<label class="form-label" for="e-msj">Mensaje (opcional)</label>
			<textarea id="e-msj" class="form-control" rows="2" maxlength="500" bind:value={envio.mensaje}
				placeholder="Ej.: Adjunto el reporte para la reunión del consejo académico."></textarea>
		</div>
	</form>
	{#snippet pie()}
		<button class="btn btn-light" onclick={() => (modalCorreo = false)}>Cancelar</button>
		<button class="btn btn-primary" form="form-correo" disabled={enviando}>
			{#if enviando}<span class="spinner-border spinner-border-sm me-1"></span>Enviando…{:else}<i class="bi bi-send me-1"></i>Enviar{/if}
		</button>
	{/snippet}
</Modal>
