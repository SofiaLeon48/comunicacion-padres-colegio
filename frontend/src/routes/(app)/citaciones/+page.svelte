<script>
	import { onDestroy, onMount } from 'svelte';
	import { api } from '$lib/api.js';
	import { error, exito } from '$lib/avisos.svelte.js';
	import Calendario from '$lib/componentes/Calendario.svelte';
	import Cargando from '$lib/componentes/Cargando.svelte';
	import InsigniaEstado from '$lib/componentes/InsigniaEstado.svelte';
	import Modal from '$lib/componentes/Modal.svelte';
	import ModalConfirmar from '$lib/componentes/ModalConfirmar.svelte';
	import SelectorLista from '$lib/componentes/SelectorLista.svelte';
	import TablaDatos from '$lib/componentes/TablaDatos.svelte';
	import TarjetaIndicador from '$lib/componentes/TarjetaIndicador.svelte';
	import TituloPagina from '$lib/componentes/TituloPagina.svelte';
	import { aInputFecha, esc, ESTADO_CITACION, fechaHora, insignia } from '$lib/formato.js';
	import { esAcudiente, esCoordinacion, esPersonal, sesion } from '$lib/sesion.svelte.js';
	import { alRecibir } from '$lib/tiempoReal.svelte.js';

	let lista = $state([]);
	let cargando = $state(true);
	let vista = $state('calendario');
	let filtroEstado = $state('');

	let modalForm = $state(false);
	let modalVer = $state(false);
	let modalAsistencia = $state(false);
	let modalEliminar = $state(false);
	let editando = $state(null);
	let actual = $state(null);
	let guardando = $state(false);
	let form = $state(vacio());
	let asistencia = $state({ asistio: true, observaciones: '' });

	function vacio() {
		const manana = new Date(Date.now() + 86400000);
		manana.setHours(7, 0, 0, 0);
		return { estudiante_id: null, acudiente_id: null, docente_id: null, motivo: '', fecha_hora: aInputFecha(manana), lugar: '' };
	}

	const visibles = $derived(lista.filter((c) => !filtroEstado || c.estado_citacion === filtroEstado));
	const eventos = $derived(
		lista.map((c) => ({ fecha: c.fecha_hora, titulo: c.estudiante_nombre, color: ESTADO_CITACION[c.estado_citacion][1], dato: c }))
	);
	const cuenta = (e) => lista.filter((c) => c.estado_citacion === e).length;
	const esDueno = (c) => esCoordinacion() || c.docente_id === sesion.usuario?.id;
	const abierta = (c) => ['pendiente', 'confirmada'].includes(c.estado_citacion);

	async function cargar() {
		try {
			lista = await api.get('/citaciones/');
		} catch (e) {
			error(e);
		} finally {
			cargando = false;
		}
	}
	onMount(cargar);
	const quitar = alRecibir((m) => m.evento === 'notificacion' && m.datos.tipo === 'citacion' && cargar());
	onDestroy(quitar);

	const columnas = [
		{ titulo: 'Fecha y hora', campo: 'fecha_hora', clase: 'text-nowrap', render: (v) => `<span class="fw-semibold">${fechaHora(v)}</span>`, orden: (c) => c.fecha_hora },
		{ titulo: 'Estudiante', campo: 'estudiante_nombre', render: (v, c) => `${esc(v)}<div class="small text-muted">Curso ${esc(c.curso_nombre)}</div>` },
		{ titulo: 'Motivo', campo: 'motivo' },
		{ titulo: 'Citado(s)', campo: 'acudiente_nombre', render: (v) => esc(v ?? 'Todos los acudientes') },
		{ titulo: 'Docente', campo: 'docente_nombre' },
		{ titulo: 'Lugar', campo: 'lugar' },
		{ titulo: 'Estado', campo: 'estado_citacion', render: (v) => insignia(...ESTADO_CITACION[v]) }
	];
	const acciones = [
		{ icono: 'bi-eye', titulo: 'Ver', color: 'primary', accion: ver },
		{ icono: 'bi-pencil', titulo: 'Editar', color: 'warning', accion: editar, visible: (c) => esPersonal() && esDueno(c) && abierta(c) },
		{ icono: 'bi-trash', titulo: 'Eliminar', color: 'danger', accion: pedirEliminar, visible: (c) => esPersonal() && esDueno(c) }
	];

	function nuevo() {
		editando = null;
		form = vacio();
		modalForm = true;
	}
	function editar(c) {
		editando = c;
		form = { estudiante_id: c.estudiante_id, acudiente_id: c.acudiente_id, docente_id: c.docente_id, motivo: c.motivo, fecha_hora: aInputFecha(c.fecha_hora), lugar: c.lugar ?? '' };
		modalVer = false;
		modalForm = true;
	}
	function ver(c) {
		actual = c;
		modalVer = true;
	}
	function pedirEliminar(c) {
		actual = c;
		modalEliminar = true;
	}

	async function guardar(e) {
		e.preventDefault();
		if (!form.estudiante_id) return error('Selecciona el estudiante.');
		guardando = true;
		try {
			if (editando) {
				await api.patch(`/citaciones/${editando.id}`, { motivo: form.motivo, fecha_hora: form.fecha_hora, lugar: form.lugar || null, acudiente_id: form.acudiente_id });
				exito('Citación actualizada. Se notificó a los acudientes si cambió la fecha.');
			} else {
				const datos = { ...form, lugar: form.lugar || null };
				if (!esCoordinacion() || !datos.docente_id) delete datos.docente_id;
				await api.post('/citaciones/', datos);
				exito('Citación agendada y notificada a los acudientes.');
			}
			modalForm = false;
			await cargar();
		} catch (err) {
			error(err);
		} finally {
			guardando = false;
		}
	}

	async function cambiarEstado(estado, texto) {
		try {
			await api.patch(`/citaciones/${actual.id}/estado`, { estado_citacion: estado });
			exito(texto);
			await cargar();
			actual = lista.find((c) => c.id === actual.id) ?? null;
			if (!actual) modalVer = false;
		} catch (e) {
			error(e);
		}
	}

	function abrirAsistencia() {
		asistencia = { asistio: true, observaciones: '' };
		modalVer = false;
		modalAsistencia = true;
	}

	async function guardarAsistencia(e) {
		e.preventDefault();
		guardando = true;
		try {
			await api.post(`/citaciones/${actual.id}/asistencia`, { asistio: asistencia.asistio, observaciones: asistencia.observaciones || null });
			exito('Asistencia registrada. La citación quedó como realizada.');
			modalAsistencia = false;
			await cargar();
		} catch (err) {
			error(err);
		} finally {
			guardando = false;
		}
	}

	async function eliminar() {
		guardando = true;
		try {
			await api.del(`/citaciones/${actual.id}`);
			exito('Citación eliminada.');
			modalEliminar = false;
			await cargar();
		} catch (e) {
			error(e);
		} finally {
			guardando = false;
		}
	}
</script>

<svelte:head><title>Citaciones · Conecta Escolar</title></svelte:head>

<TituloPagina titulo="Citaciones" icono="bi-calendar-event"
	descripcion={esAcudiente() ? 'Citas programadas por el colegio con relación a tus hijos.' : 'Agenda citas con los acudientes y registra su asistencia.'}>
	{#if esPersonal()}
		<button class="btn btn-primary" onclick={nuevo}><i class="bi bi-plus-lg me-1"></i>Nueva citación</button>
	{/if}
</TituloPagina>

<div class="row g-3 mb-4">
	<div class="col-6 col-lg-3"><TarjetaIndicador titulo="Pendientes" valor={cuenta('pendiente')} icono="bi-hourglass-split" color="warning" /></div>
	<div class="col-6 col-lg-3"><TarjetaIndicador titulo="Confirmadas" valor={cuenta('confirmada')} icono="bi-check2-circle" color="primary" /></div>
	<div class="col-6 col-lg-3"><TarjetaIndicador titulo="Realizadas" valor={cuenta('realizada')} icono="bi-clipboard-check" color="success" /></div>
	<div class="col-6 col-lg-3"><TarjetaIndicador titulo="Canceladas" valor={cuenta('cancelada')} icono="bi-x-circle" color="secondary" /></div>
</div>

<div class="tarjeta tarjeta-cuerpo">
	<div class="d-flex flex-wrap justify-content-between align-items-end gap-2 mb-3">
		<div class="btn-group">
			<button class="btn btn-outline-primary" class:active={vista === 'calendario'} onclick={() => (vista = 'calendario')}><i class="bi bi-calendar3 me-1"></i>Calendario</button>
			<button class="btn btn-outline-primary" class:active={vista === 'lista'} onclick={() => (vista = 'lista')}><i class="bi bi-list-ul me-1"></i>Lista</button>
		</div>
		{#if vista === 'lista'}
			<div style="min-width: 200px">
				<label class="form-label small text-muted" for="f-est">Estado</label>
				<select id="f-est" class="form-select" bind:value={filtroEstado}>
					<option value="">Todos</option>
					{#each Object.entries(ESTADO_CITACION) as [k, [t]]}<option value={k}>{t}</option>{/each}
				</select>
			</div>
		{/if}
	</div>
	<Cargando {cargando}>
		{#if vista === 'calendario'}
			<Calendario {eventos} alSeleccionar={ver} />
			<div class="d-flex flex-wrap gap-3 small mt-3">
				{#each Object.values(ESTADO_CITACION) as [t, c]}<span><i class="bi bi-square-fill text-{c} me-1"></i>{t}</span>{/each}
			</div>
		{:else}
			<TablaDatos {columnas} datos={visibles} {acciones} ordenInicial={[[0, 'desc']]} />
		{/if}
	</Cargando>
</div>

<!-- Ver -->
<Modal bind:abierto={modalVer} variante="ver" titulo="Detalle de la citación" tamano="lg">
	{#if actual}
		<div class="d-flex justify-content-between align-items-start mb-3">
			<div>
				<h3 class="h5 fw-bold mb-1">{actual.motivo}</h3>
				<div class="text-muted"><i class="bi bi-clock me-1"></i>{fechaHora(actual.fecha_hora)}</div>
			</div>
			<InsigniaEstado estado={actual.estado_citacion} />
		</div>
		<dl class="row mb-0">
			<dt class="col-sm-4 text-muted fw-normal">Estudiante</dt><dd class="col-sm-8">{actual.estudiante_nombre} · Curso {actual.curso_nombre}</dd>
			<dt class="col-sm-4 text-muted fw-normal">Citado(s)</dt><dd class="col-sm-8">{actual.acudiente_nombre ?? 'Todos los acudientes del estudiante'}</dd>
			<dt class="col-sm-4 text-muted fw-normal">Docente</dt><dd class="col-sm-8">{actual.docente_nombre}</dd>
			<dt class="col-sm-4 text-muted fw-normal">Lugar</dt><dd class="col-sm-8">{actual.lugar ?? 'Por definir'}</dd>
		</dl>
		{#if actual.asistio !== null && actual.asistio !== undefined}
			<div class="alert {actual.asistio ? 'alert-success' : 'alert-danger'} mt-3 mb-0">
				<i class="bi {actual.asistio ? 'bi-check-circle-fill' : 'bi-x-circle-fill'} me-2"></i>
				<strong>{actual.asistio ? 'El acudiente asistió.' : 'El acudiente no asistió.'}</strong>
				{#if actual.observaciones}<div class="small mt-1">{actual.observaciones}</div>{/if}
			</div>
		{/if}
		{#if esAcudiente() && actual.estado_citacion === 'pendiente'}
			<div class="alert alert-warning d-flex align-items-center gap-2 mt-3 mb-0">
				<i class="bi bi-calendar-check"></i> Por favor confirma tu asistencia a esta cita.
				<button class="btn btn-success btn-sm ms-auto" onclick={() => cambiarEstado('confirmada', 'Asistencia confirmada. El docente fue notificado.')}>Confirmar asistencia</button>
			</div>
		{/if}
	{/if}
	{#snippet pie()}
		<button class="btn btn-light" onclick={() => (modalVer = false)}>Volver</button>
		{#if actual && esPersonal() && esDueno(actual)}
			{#if abierta(actual)}
				<button class="btn btn-outline-secondary" onclick={() => cambiarEstado('cancelada', 'Citación cancelada. Se notificó a los acudientes.')}><i class="bi bi-x-circle me-1"></i>Cancelar cita</button>
				<button class="btn btn-warning" onclick={() => editar(actual)}><i class="bi bi-pencil me-1"></i>Editar</button>
			{/if}
			{#if actual.estado_citacion !== 'cancelada' && (actual.asistio === null || actual.asistio === undefined)}
				<button class="btn btn-success" onclick={abrirAsistencia}><i class="bi bi-clipboard-check me-1"></i>Registrar asistencia</button>
			{/if}
		{/if}
	{/snippet}
</Modal>

<!-- Crear / editar -->
<Modal bind:abierto={modalForm} variante={editando ? 'editar' : 'crear'} titulo={editando ? 'Editar citación' : 'Nueva citación'} tamano="lg">
	<form id="form-citacion" onsubmit={guardar} class="row g-3">
		<div class="col-md-6">
			{#if editando}
				<label class="form-label" for="ci-est">Estudiante</label>
				<input id="ci-est" class="form-control" disabled value="{editando.estudiante_nombre} ({editando.curso_nombre})" />
			{:else}
				<SelectorLista bind:valor={form.estudiante_id} url="/catalogos/estudiantes" etiqueta="Estudiante" requerido
					placeholder="Selecciona el estudiante" alCambiar={() => (form.acudiente_id = null)} />
			{/if}
		</div>
		<div class="col-md-6">
			<SelectorLista bind:valor={form.acudiente_id} etiqueta="Acudiente citado"
				url={form.estudiante_id ? `/catalogos/acudientes?estudiante_id=${form.estudiante_id}` : null}
				opcionVacia="Todos los acudientes del estudiante" />
		</div>
		<div class="col-md-6">
			<label class="form-label" for="ci-fecha">Fecha y hora <span class="text-danger">*</span></label>
			<input id="ci-fecha" type="datetime-local" class="form-control" bind:value={form.fecha_hora} required min={aInputFecha(new Date())} />
		</div>
		<div class="col-md-6">
			<label class="form-label" for="ci-lugar">Lugar</label>
			<input id="ci-lugar" class="form-control" bind:value={form.lugar} maxlength="100" placeholder="Ej. Sala de profesores" />
		</div>
		{#if esCoordinacion() && !editando}
			<div class="col-md-6">
				<SelectorLista bind:valor={form.docente_id} url="/catalogos/docentes" etiqueta="Docente que cita" opcionVacia="Yo (coordinación)" />
			</div>
		{/if}
		<div class="col-12">
			<label class="form-label" for="ci-motivo">Motivo <span class="text-danger">*</span></label>
			<textarea id="ci-motivo" class="form-control" rows="3" bind:value={form.motivo} required minlength="3" maxlength="255"
				placeholder="Ej. Seguimiento académico del tercer periodo"></textarea>
		</div>
	</form>
	{#snippet pie()}
		<button class="btn btn-light" onclick={() => (modalForm = false)}>Cancelar</button>
		<button class="btn {editando ? 'btn-warning' : 'btn-success'}" form="form-citacion" disabled={guardando}>
			{#if guardando}<span class="spinner-border spinner-border-sm me-1"></span>{/if}{editando ? 'Actualizar' : 'Agendar'}
		</button>
	{/snippet}
</Modal>

<!-- Asistencia -->
<Modal bind:abierto={modalAsistencia} variante="crear" titulo="Registrar asistencia" icono="bi-clipboard-check">
	<form id="form-asistencia" onsubmit={guardarAsistencia}>
		<p class="mb-2">¿El acudiente asistió a la cita de <strong>{actual?.estudiante_nombre}</strong>?</p>
		<div class="btn-group w-100 mb-3">
			<input type="radio" class="btn-check" id="as-si" value={true} bind:group={asistencia.asistio} />
			<label class="btn btn-outline-success" for="as-si"><i class="bi bi-check-lg me-1"></i>Sí asistió</label>
			<input type="radio" class="btn-check" id="as-no" value={false} bind:group={asistencia.asistio} />
			<label class="btn btn-outline-danger" for="as-no"><i class="bi bi-x-lg me-1"></i>No asistió</label>
		</div>
		<label class="form-label" for="as-obs">Observaciones / compromisos</label>
		<textarea id="as-obs" class="form-control" rows="3" bind:value={asistencia.observaciones} placeholder="Acuerdos a los que se llegó en la reunión"></textarea>
	</form>
	{#snippet pie()}
		<button class="btn btn-light" onclick={() => (modalAsistencia = false)}>Cancelar</button>
		<button class="btn btn-success" form="form-asistencia" disabled={guardando}>Guardar</button>
	{/snippet}
</Modal>

<ModalConfirmar bind:abierto={modalEliminar} cargando={guardando} alConfirmar={eliminar}
	mensaje="¿Eliminar esta citación?" detalle={actual ? `${actual.estudiante_nombre} · ${fechaHora(actual.fecha_hora)}` : ''} />
