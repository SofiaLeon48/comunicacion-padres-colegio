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
	import { esc, GRADOS, insignia, JORNADAS } from '$lib/formato.js';
	import { esCoordinacion } from '$lib/sesion.svelte.js';

	let lista = $state([]);
	let cargando = $state(true);
	let verInactivos = $state(false);
	let modalForm = $state(false);
	let modalVer = $state(false);
	let modalEliminar = $state(false);
	let editando = $state(null);
	let actual = $state(null);
	let alumnos = $state([]);
	let guardando = $state(false);
	const anioActual = new Date().getFullYear();
	let form = $state(vacio());

	function vacio() {
		return { nombre: '', grado: 1, jornada: 'manana', anio_lectivo: anioActual, director_id: null };
	}
	const nombreGrado = (g) => GRADOS.find(([n]) => n === g)?.[1] ?? g;

	async function cargar() {
		cargando = true;
		try {
			lista = await api.get('/grupos/' + qs({ incluir_inactivos: verInactivos || null }));
		} catch (e) {
			error(e);
		} finally {
			cargando = false;
		}
	}
	onMount(cargar);

	const columnas = [
		{ titulo: 'Grupo', campo: 'nombre', render: (v) => `<span class="fw-bold">${esc(v)}</span>` },
		{ titulo: 'Grado', campo: 'grado', render: (v) => esc(nombreGrado(v)), orden: (c) => c.grado },
		{ titulo: 'Jornada', campo: 'jornada', render: (v) => esc(JORNADAS[v]) },
		{ titulo: 'Año lectivo', campo: 'anio_lectivo' },
		{ titulo: 'Director de grupo', campo: 'director_nombre', render: (v) => (v ? esc(v) : insignia('Sin asignar', 'warning')) },
		{ titulo: 'Estudiantes', campo: 'total_estudiantes', render: (v) => `<span class="badge text-bg-light fs-6">${v}</span>` },
		{ titulo: 'Estado', campo: 'estado', render: (v) => insignia(v === 'activo' ? 'Activo' : 'Inactivo', v === 'activo' ? 'success' : 'secondary') }
	];
	const acciones = [
		{ icono: 'bi-eye', titulo: 'Ver', color: 'primary', accion: ver },
		{ icono: 'bi-pencil', titulo: 'Editar', color: 'warning', accion: editar, visible: () => esCoordinacion() },
		{ icono: 'bi-trash', titulo: 'Desactivar', color: 'danger', accion: (c) => { actual = c; modalEliminar = true; }, visible: (c) => esCoordinacion() && c.estado === 'activo' },
		{ icono: 'bi-arrow-counterclockwise', titulo: 'Reactivar', color: 'success', accion: reactivar, visible: (c) => esCoordinacion() && c.estado === 'inactivo' }
	];

	function nuevo() {
		editando = null;
		form = vacio();
		modalForm = true;
	}
	function editar(c) {
		editando = c;
		form = { nombre: c.nombre, grado: c.grado, jornada: c.jornada, anio_lectivo: c.anio_lectivo, director_id: c.director_id };
		modalForm = true;
	}
	async function ver(c) {
		actual = c;
		alumnos = [];
		modalVer = true;
		try {
			alumnos = await api.get(`/grupos/${c.id}/estudiantes`);
		} catch (e) {
			error(e);
		}
	}

	async function guardar(e) {
		e.preventDefault();
		guardando = true;
		try {
			if (editando) await api.patch(`/grupos/${editando.id}`, form);
			else await api.post('/grupos/', form);
			exito(editando ? 'Grupo actualizado.' : 'Grupo creado.');
			modalForm = false;
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
			await api.del(`/grupos/${actual.id}`);
			exito('Grupo desactivado.');
			modalEliminar = false;
			await cargar();
		} catch (e) {
			error(e);
		} finally {
			guardando = false;
		}
	}
	async function reactivar(c) {
		try {
			await api.post(`/grupos/${c.id}/reactivar`);
			exito('Grupo reactivado.');
			await cargar();
		} catch (e) {
			error(e);
		}
	}

	const colAlumnos = [
		{ titulo: 'Estudiante', campo: 'nombre' },
		{ titulo: 'Documento', campo: 'documento' },
		{ titulo: 'Acudientes', campo: 'acudientes', render: (v) => esc(v ?? 'Sin acudiente') }
	];
</script>

<svelte:head><title>Grupos · Conecta Escolar</title></svelte:head>

<TituloPagina titulo="Grupos" icono="bi-easel" descripcion="Grupos del año lectivo, jornadas y directores de grupo.">
	{#if esCoordinacion()}<button class="btn btn-primary" onclick={nuevo}><i class="bi bi-plus-lg me-1"></i>Nuevo grupo</button>{/if}
</TituloPagina>

<div class="tarjeta tarjeta-cuerpo">
	{#if esCoordinacion()}
		<div class="filtros">
			<div class="form-check form-switch">
				<input class="form-check-input" type="checkbox" id="inact" bind:checked={verInactivos} onchange={cargar} />
				<label class="form-check-label" for="inact">Mostrar inactivos</label>
			</div>
		</div>
	{/if}
	<Cargando {cargando}>
		<TablaDatos {columnas} datos={lista} {acciones} ordenInicial={[[1, 'asc']]} />
	</Cargando>
</div>

<Modal bind:abierto={modalVer} variante="ver" titulo="Grupo {actual?.nombre ?? ''}" tamano="lg">
	{#if actual}
		<div class="row g-3 mb-3">
			<div class="col-sm-4"><div class="text-muted small">Grado</div><div class="fw-semibold">{nombreGrado(actual.grado)}</div></div>
			<div class="col-sm-4"><div class="text-muted small">Jornada</div><div class="fw-semibold">{JORNADAS[actual.jornada]}</div></div>
			<div class="col-sm-4"><div class="text-muted small">Director de grupo</div><div class="fw-semibold">{actual.director_nombre ?? 'Sin asignar'}</div></div>
		</div>
		<h4 class="h6 fw-semibold">Estudiantes ({alumnos.length})</h4>
		<TablaDatos columnas={colAlumnos} datos={alumnos} porPagina={5} compacta />
	{/if}
	{#snippet pie()}<button class="btn btn-light" onclick={() => (modalVer = false)}>Volver</button>{/snippet}
</Modal>

<Modal bind:abierto={modalForm} variante={editando ? 'editar' : 'crear'} titulo={editando ? 'Editar grupo' : 'Nuevo grupo'}>
	<form id="form-grupo" onsubmit={guardar} class="row g-3">
		<div class="col-md-4">
			<label class="form-label" for="cu-nombre">Nombre <span class="text-danger">*</span></label>
			<input id="cu-nombre" class="form-control" bind:value={form.nombre} required maxlength="20" placeholder="Ej. 7B" />
		</div>
		<div class="col-md-4">
			<label class="form-label" for="cu-grado">Grado</label>
			<select id="cu-grado" class="form-select" bind:value={form.grado}>
				{#each GRADOS as [n, t]}<option value={n}>{t}</option>{/each}
			</select>
		</div>
		<div class="col-md-4">
			<label class="form-label" for="cu-jor">Jornada</label>
			<select id="cu-jor" class="form-select" bind:value={form.jornada}>
				{#each Object.entries(JORNADAS) as [k, t]}<option value={k}>{t}</option>{/each}
			</select>
		</div>
		<div class="col-md-4">
			<label class="form-label" for="cu-anio">Año lectivo</label>
			<input id="cu-anio" type="number" class="form-control" bind:value={form.anio_lectivo} min="2020" max="2100" />
		</div>
		<div class="col-md-8">
			<SelectorLista bind:valor={form.director_id} url="/catalogos/docentes" etiqueta="Director de grupo" opcionVacia="Sin asignar" />
		</div>
	</form>
	{#snippet pie()}
		<button class="btn btn-light" onclick={() => (modalForm = false)}>Cancelar</button>
		<button class="btn {editando ? 'btn-warning' : 'btn-success'}" form="form-grupo" disabled={guardando}>{editando ? 'Actualizar' : 'Guardar'}</button>
	{/snippet}
</Modal>

<ModalConfirmar bind:abierto={modalEliminar} cargando={guardando} alConfirmar={eliminar} titulo="Desactivar grupo"
	mensaje="¿Desactivar este grupo?" textoBoton="Desactivar" detalle={actual ? `Grupo ${actual.nombre} · ${actual.total_estudiantes} estudiantes` : ''} />
