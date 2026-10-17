<script>
	import { onMount } from 'svelte';
	import { api, qs } from '$lib/api.js';
	import { error, exito } from '$lib/avisos.svelte.js';
	import Cargando from '$lib/componentes/Cargando.svelte';
	import Modal from '$lib/componentes/Modal.svelte';
	import ModalConfirmar from '$lib/componentes/ModalConfirmar.svelte';
	import SelectorLista from '$lib/componentes/SelectorLista.svelte';
	import TablaDatos from '$lib/componentes/TablaDatos.svelte';
	import TituloPagina from '$lib/componentes/TituloPagina.svelte';
	import { esc, insignia, JORNADAS } from '$lib/formato.js';
	import { esAcudiente, esCoordinacion } from '$lib/sesion.svelte.js';

	let lista = $state([]);
	let cargando = $state(true);
	let filtroGrupo = $state(null);
	let verInactivos = $state(false);

	let modalForm = $state(false);
	let modalVer = $state(false);
	let modalAcudientes = $state(false);
	let modalEliminar = $state(false);
	let editando = $state(null);
	let actual = $state(null);
	let acudientes = $state([]);
	let vinculos = $state([]);
	let guardando = $state(false);
	let form = $state({ nombre: '', documento: '', grupo_id: null });
	let nuevoVinculo = $state({ acudiente_id: null, parentesco: 'madre', es_principal: false });

	async function cargar() {
		cargando = true;
		try {
			lista = await api.get('/estudiantes/' + qs({ grupo_id: filtroGrupo, incluir_inactivos: verInactivos || null }));
		} catch (e) {
			error(e);
		} finally {
			cargando = false;
		}
	}
	onMount(cargar);

	const columnas = [
		{ titulo: 'Estudiante', campo: 'nombre', render: (v) => `<span class="fw-semibold">${esc(v)}</span>` },
		{ titulo: 'Documento', campo: 'documento' },
		{ titulo: 'Grupo', campo: 'grupo_nombre', render: (v, e) => `${esc(v)} <span class="small text-muted">· ${JORNADAS[e.grupo_jornada] ?? ''}</span>` },
		{ titulo: 'Director de grupo', campo: 'director_nombre' },
		{ titulo: 'Acudientes', campo: 'acudientes', render: (v) => (v ? esc(v) : insignia('Sin acudiente', 'warning')) },
		{ titulo: 'Estado', campo: 'estado', render: (v) => insignia(v === 'activo' ? 'Activo' : 'Inactivo', v === 'activo' ? 'success' : 'secondary') }
	];
	const acciones = [
		{ icono: 'bi-eye', titulo: 'Ver', color: 'primary', accion: ver },
		{ icono: 'bi-people', titulo: 'Acudientes', color: 'info', accion: gestionarAcudientes, visible: () => esCoordinacion() },
		{ icono: 'bi-pencil', titulo: 'Editar', color: 'warning', accion: editar, visible: () => esCoordinacion() },
		{ icono: 'bi-trash', titulo: 'Desactivar', color: 'danger', accion: pedirEliminar, visible: (e) => esCoordinacion() && e.estado === 'activo' },
		{ icono: 'bi-arrow-counterclockwise', titulo: 'Reactivar', color: 'success', accion: reactivar, visible: (e) => esCoordinacion() && e.estado === 'inactivo' }
	];

	function nuevo() {
		editando = null;
		form = { nombre: '', documento: '', grupo_id: null };
		modalForm = true;
	}
	function editar(e) {
		editando = e;
		form = { nombre: e.nombre, documento: e.documento, grupo_id: e.grupo_id };
		modalForm = true;
	}
	async function ver(e) {
		actual = e;
		acudientes = [];
		modalVer = true;
		try {
			acudientes = await api.get(`/estudiantes/${e.id}/acudientes`);
		} catch (err) {
			error(err);
		}
	}
	async function gestionarAcudientes(e) {
		actual = e;
		nuevoVinculo = { acudiente_id: null, parentesco: 'madre', es_principal: false };
		modalAcudientes = true;
		await cargarVinculos();
	}
	async function cargarVinculos() {
		try {
			vinculos = await api.get(`/acudientes-estudiantes/?estudiante_id=${actual.id}`);
		} catch (err) {
			error(err);
		}
	}
	function pedirEliminar(e) {
		actual = e;
		modalEliminar = true;
	}

	async function guardar(ev) {
		ev.preventDefault();
		if (!form.grupo_id) return error('Selecciona el grupo.');
		guardando = true;
		try {
			if (editando) await api.patch(`/estudiantes/${editando.id}`, form);
			else await api.post('/estudiantes/', form);
			exito(editando ? 'Estudiante actualizado.' : 'Estudiante matriculado.');
			modalForm = false;
			await cargar();
		} catch (err) {
			error(err);
		} finally {
			guardando = false;
		}
	}

	async function vincular(ev) {
		ev.preventDefault();
		if (!nuevoVinculo.acudiente_id) return error('Selecciona el acudiente.');
		try {
			await api.post('/acudientes-estudiantes/', { ...nuevoVinculo, estudiante_id: actual.id });
			exito('Acudiente vinculado.');
			nuevoVinculo = { acudiente_id: null, parentesco: 'madre', es_principal: false };
			await cargarVinculos();
			cargar();
		} catch (err) {
			error(err);
		}
	}
	async function desvincular(v) {
		try {
			await api.del(`/acudientes-estudiantes/${v.id}`);
			exito('Vínculo retirado.');
			await cargarVinculos();
			cargar();
		} catch (err) {
			error(err);
		}
	}

	async function eliminar() {
		guardando = true;
		try {
			await api.del(`/estudiantes/${actual.id}`);
			exito('Estudiante desactivado.');
			modalEliminar = false;
			await cargar();
		} catch (e) {
			error(e);
		} finally {
			guardando = false;
		}
	}
	async function reactivar(e) {
		try {
			await api.post(`/estudiantes/${e.id}/reactivar`);
			exito('Estudiante reactivado.');
			await cargar();
		} catch (err) {
			error(err);
		}
	}
</script>

<svelte:head><title>{esAcudiente() ? 'Mis hijos' : 'Estudiantes'} · Conecta Escolar</title></svelte:head>

{#if esAcudiente()}
	<TituloPagina titulo="Mis hijos" icono="bi-mortarboard" descripcion="Estudiantes vinculados a tu cuenta como acudiente." />
	<Cargando {cargando} vacio={!lista.length} textoVacio="No tienes estudiantes vinculados. Comunícate con coordinación.">
		<div class="row g-3">
			{#each lista as e (e.id)}
				<div class="col-md-6 col-xl-4">
					<div class="tarjeta tarjeta-cuerpo h-100">
						<div class="d-flex gap-3 align-items-center mb-3">
							<div class="icono-indicador bg-success-subtle text-success"><i class="bi bi-mortarboard"></i></div>
							<div><div class="fw-bold fs-5">{e.nombre}</div><div class="text-muted small">Documento {e.documento}</div></div>
						</div>
						<ul class="list-unstyled small mb-3">
							<li class="mb-1"><i class="bi bi-easel me-2 text-primary"></i>Grupo <strong>{e.grupo_nombre}</strong> · Jornada {JORNADAS[e.grupo_jornada]}</li>
							<li class="mb-1"><i class="bi bi-person-video3 me-2 text-primary"></i>Director(a): {e.director_nombre ?? 'Sin asignar'}</li>
							<li><i class="bi bi-people me-2 text-primary"></i>Acudientes: {e.acudientes}</li>
						</ul>
						<div class="d-flex gap-2">
							<a href="/comunicados" class="btn btn-sm btn-outline-primary"><i class="bi bi-megaphone me-1"></i>Comunicados</a>
							<a href="/citaciones" class="btn btn-sm btn-outline-warning"><i class="bi bi-calendar-event me-1"></i>Citaciones</a>
						</div>
					</div>
				</div>
			{/each}
		</div>
	</Cargando>
{:else}
	<TituloPagina titulo="Estudiantes" icono="bi-mortarboard"
		descripcion={esCoordinacion() ? 'Matrícula de estudiantes y vínculo con sus acudientes.' : 'Consulta los estudiantes y el contacto de sus acudientes.'}>
		{#if esCoordinacion()}<button class="btn btn-primary" onclick={nuevo}><i class="bi bi-plus-lg me-1"></i>Nuevo estudiante</button>{/if}
	</TituloPagina>

	<div class="tarjeta tarjeta-cuerpo">
		<div class="filtros">
			<div><SelectorLista bind:valor={filtroGrupo} url="/catalogos/grupos" etiqueta="Grupo" opcionVacia="Todos los grupos" alCambiar={cargar} /></div>
			{#if esCoordinacion()}
				<div class="form-check form-switch mb-2">
					<input class="form-check-input" type="checkbox" id="inact" bind:checked={verInactivos} onchange={cargar} />
					<label class="form-check-label" for="inact">Mostrar inactivos</label>
				</div>
			{/if}
		</div>
		<TablaDatos {columnas} datos={lista} {acciones} ordenInicial={[[0, 'asc']]} />
	</div>
{/if}

<!-- Ver -->
<Modal bind:abierto={modalVer} variante="ver" titulo="Ficha del estudiante">
	{#if actual}
		<div class="d-flex gap-3 align-items-center mb-3">
			<div class="icono-indicador bg-primary-subtle text-primary"><i class="bi bi-person"></i></div>
			<div><div class="fw-bold fs-5">{actual.nombre}</div><div class="text-muted small">Documento {actual.documento}</div></div>
		</div>
		<p class="mb-1"><strong>Grupo:</strong> {actual.grupo_nombre} · Jornada {JORNADAS[actual.grupo_jornada]}</p>
		<p><strong>Director de grupo:</strong> {actual.director_nombre ?? 'Sin asignar'}</p>
		<h4 class="h6 fw-semibold">Acudientes</h4>
		<div class="list-group">
			{#each acudientes as a}
				<div class="list-group-item">
					<div class="fw-semibold">{a.nombre} <span class="badge text-bg-light text-capitalize">{a.parentesco}</span>
						{#if a.es_principal}<span class="badge text-bg-primary">Principal</span>{/if}</div>
					<div class="small text-muted"><i class="bi bi-envelope me-1"></i>{a.correo} · <i class="bi bi-telephone me-1"></i>{a.telefono ?? '—'}</div>
				</div>
			{:else}
				<div class="text-muted small">Sin acudientes vinculados.</div>
			{/each}
		</div>
	{/if}
	{#snippet pie()}<button class="btn btn-light" onclick={() => (modalVer = false)}>Volver</button>{/snippet}
</Modal>

<!-- Crear / editar -->
<Modal bind:abierto={modalForm} variante={editando ? 'editar' : 'crear'} titulo={editando ? 'Editar estudiante' : 'Nuevo estudiante'}>
	<form id="form-est" onsubmit={guardar} class="row g-3">
		<div class="col-12">
			<label class="form-label" for="e-nombre">Nombre completo <span class="text-danger">*</span></label>
			<input id="e-nombre" class="form-control" bind:value={form.nombre} required minlength="3" maxlength="100" placeholder="Ej. Juan Pablo Gómez" />
		</div>
		<div class="col-md-6">
			<label class="form-label" for="e-doc">Documento (T.I.) <span class="text-danger">*</span></label>
			<input id="e-doc" class="form-control" bind:value={form.documento} required minlength="4" maxlength="20" inputmode="numeric" placeholder="Ej. 1043987015" />
		</div>
		<div class="col-md-6">
			<SelectorLista bind:valor={form.grupo_id} url="/catalogos/grupos" etiqueta="Grupo" requerido placeholder="Selecciona el grupo" />
		</div>
	</form>
	{#snippet pie()}
		<button class="btn btn-light" onclick={() => (modalForm = false)}>Cancelar</button>
		<button class="btn {editando ? 'btn-warning' : 'btn-success'}" form="form-est" disabled={guardando}>{editando ? 'Actualizar' : 'Guardar'}</button>
	{/snippet}
</Modal>

<!-- Acudientes del estudiante -->
<Modal bind:abierto={modalAcudientes} variante="neutro" icono="bi-people" titulo="Acudientes de {actual?.nombre ?? ''}" tamano="lg">
	<div class="list-group mb-4">
		{#each vinculos as v (v.id)}
			<div class="list-group-item d-flex align-items-center justify-content-between">
				<div>
					<span class="fw-semibold">{v.acudiente_nombre}</span>
					<span class="badge text-bg-light text-capitalize ms-1">{v.parentesco}</span>
					{#if v.es_principal}<span class="badge text-bg-primary ms-1">Principal</span>{/if}
				</div>
				<button class="btn btn-sm btn-outline-danger" onclick={() => desvincular(v)}><i class="bi bi-x-lg me-1"></i>Retirar</button>
			</div>
		{:else}
			<div class="text-muted small">Este estudiante aún no tiene acudientes vinculados.</div>
		{/each}
	</div>
	<h4 class="h6 fw-semibold">Vincular acudiente</h4>
	<form class="row g-2 align-items-end" onsubmit={vincular}>
		<div class="col-md-5"><SelectorLista bind:valor={nuevoVinculo.acudiente_id} url="/catalogos/acudientes" etiqueta="Acudiente" placeholder="Selecciona" /></div>
		<div class="col-md-3">
			<label class="form-label" for="v-par">Parentesco</label>
			<select id="v-par" class="form-select" bind:value={nuevoVinculo.parentesco}>
				{#each ['madre', 'padre', 'abuela', 'abuelo', 'tía', 'tío', 'hermano(a)', 'acudiente'] as p}<option value={p}>{p}</option>{/each}
			</select>
		</div>
		<div class="col-md-2">
			<div class="form-check form-switch mb-2">
				<input class="form-check-input" type="checkbox" id="v-prin" bind:checked={nuevoVinculo.es_principal} />
				<label class="form-check-label small" for="v-prin">Principal</label>
			</div>
		</div>
		<div class="col-md-2"><button class="btn btn-success w-100"><i class="bi bi-link-45deg"></i> Vincular</button></div>
	</form>
	{#snippet pie()}<button class="btn btn-light" onclick={() => (modalAcudientes = false)}>Cerrar</button>{/snippet}
</Modal>

<ModalConfirmar bind:abierto={modalEliminar} cargando={guardando} alConfirmar={eliminar} titulo="Desactivar estudiante"
	mensaje="¿Desactivar este estudiante?" textoBoton="Desactivar" detalle={actual ? `${actual.nombre} · ${actual.grupo_nombre}` : ''} />
