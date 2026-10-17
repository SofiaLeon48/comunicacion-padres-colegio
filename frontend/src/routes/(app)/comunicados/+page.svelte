<script>
	import { onDestroy, onMount } from 'svelte';
	import { api } from '$lib/api.js';
	import { error, exito } from '$lib/avisos.svelte.js';
	import Cargando from '$lib/componentes/Cargando.svelte';
	import InsigniaEstado from '$lib/componentes/InsigniaEstado.svelte';
	import Modal from '$lib/componentes/Modal.svelte';
	import ModalConfirmar from '$lib/componentes/ModalConfirmar.svelte';
	import SelectorLista from '$lib/componentes/SelectorLista.svelte';
	import TablaDatos from '$lib/componentes/TablaDatos.svelte';
	import TituloPagina from '$lib/componentes/TituloPagina.svelte';
	import { esc, fechaHora, insignia } from '$lib/formato.js';
	import { esAcudiente, esCoordinacion, esPersonal, sesion } from '$lib/sesion.svelte.js';
	import { alRecibir, refrescarNotificaciones } from '$lib/tiempoReal.svelte.js';

	let lista = $state([]);
	let cargando = $state(true);
	let filtroPrioridad = $state('');
	let filtroLectura = $state('');

	// modales
	let modalForm = $state(false);
	let modalVer = $state(false);
	let modalEliminar = $state(false);
	let editando = $state(null);
	let actual = $state(null);
	let lecturas = $state(null);
	let guardando = $state(false);
	let form = $state(vacio());

	function vacio() {
		return { titulo: '', contenido: '', grupo_id: null, prioridad: 'normal', requiere_confirmacion: true };
	}

	const visibles = $derived(
		lista.filter(
			(c) =>
				(!filtroPrioridad || c.prioridad === filtroPrioridad) &&
				(!filtroLectura ||
					(filtroLectura === 'pendiente' ? c.requiere_confirmacion && !c.confirmado_por_mi : c.confirmado_por_mi))
		)
	);
	const pendientes = $derived(lista.filter((c) => c.requiere_confirmacion && !c.confirmado_por_mi).length);
	const puedeEditar = (c) => esCoordinacion() || c.autor_id === sesion.usuario?.id;

	async function cargar() {
		try {
			lista = await api.get('/comunicados/');
		} catch (e) {
			error(e);
		} finally {
			cargando = false;
		}
	}
	onMount(cargar);
	const quitar = alRecibir((m) => m.evento === 'notificacion' && m.datos.tipo === 'comunicado' && cargar());
	onDestroy(quitar);

	const columnas = [
		{
			titulo: 'Comunicado',
			campo: 'titulo',
			render: (v, c) =>
				`<div class="fw-semibold">${c.prioridad === 'urgente' ? '<i class="bi bi-exclamation-circle-fill text-danger me-1"></i>' : ''}${esc(v)}</div>
				 <div class="small text-muted texto-2-lineas">${esc(c.contenido)}</div>`
		},
		{
			titulo: 'Dirigido a',
			campo: 'grupo_nombre',
			render: (v) => (v ? insignia(`Grupo ${v}`, 'light') : insignia('Todo el colegio', 'info', 'bi-buildings'))
		},
		{ titulo: 'Publicado por', campo: 'autor_nombre' },
		{
			titulo: 'Prioridad',
			campo: 'prioridad',
			render: (v) => (v === 'urgente' ? insignia('Urgente', 'danger') : insignia('Normal', 'secondary'))
		},
		{ titulo: 'Fecha', campo: 'fecha_publicacion', clase: 'text-nowrap', render: (v) => fechaHora(v), orden: (c) => c.fecha_publicacion },
		{
			titulo: esAcudiente() ? 'Mi lectura' : 'Confirmaciones',
			campo: 'confirmado_por_mi',
			render: (v, c) => {
				if (!c.requiere_confirmacion) return insignia('No requiere', 'light');
				if (esAcudiente()) return v ? insignia('Confirmado', 'success', 'bi-check2') : insignia('Por confirmar', 'warning', 'bi-hourglass-split');
				return `<span class="fw-semibold">${c.total_confirmados}</span> <span class="small text-muted">confirmaciones</span>`;
			}
		}
	];

	const acciones = [
		{ icono: 'bi-eye', titulo: 'Ver', color: 'primary', accion: ver },
		{ icono: 'bi-pencil', titulo: 'Editar', color: 'warning', accion: editar, visible: puedeEditar },
		{ icono: 'bi-trash', titulo: 'Eliminar', color: 'danger', accion: pedirEliminar, visible: puedeEditar }
	];

	function nuevo() {
		editando = null;
		form = vacio();
		modalForm = true;
	}
	function editar(c) {
		editando = c;
		form = { titulo: c.titulo, contenido: c.contenido, grupo_id: c.grupo_id, prioridad: c.prioridad, requiere_confirmacion: c.requiere_confirmacion };
		modalForm = true;
	}
	async function ver(c) {
		actual = c;
		lecturas = null;
		modalVer = true;
		if (esPersonal() && c.requiere_confirmacion) {
			try {
				lecturas = await api.get(`/comunicados/${c.id}/lecturas`);
			} catch (e) {
				error(e);
			}
		}
	}
	function pedirEliminar(c) {
		actual = c;
		modalEliminar = true;
	}

	async function guardar(e) {
		e.preventDefault();
		if (!esCoordinacion() && !form.grupo_id) return error('Selecciona el grupo al que va dirigido.');
		guardando = true;
		try {
			if (editando) {
				const { grupo_id, ...cambios } = form;
				await api.patch(`/comunicados/${editando.id}`, cambios);
				exito('Comunicado actualizado.');
			} else {
				await api.post('/comunicados/', form);
				exito('Comunicado publicado. Se notificó a los acudientes.');
			}
			modalForm = false;
			await cargar();
		} catch (err) {
			error(err);
		} finally {
			guardando = false;
		}
	}

	async function confirmar() {
		try {
			await api.post(`/comunicados/${actual.id}/confirmar`);
			exito('¡Gracias! Confirmaste la lectura del comunicado.');
			actual = { ...actual, confirmado_por_mi: true };
			await cargar();
			refrescarNotificaciones();
		} catch (e) {
			error(e);
		}
	}

	async function eliminar() {
		guardando = true;
		try {
			await api.del(`/comunicados/${actual.id}`);
			exito('Comunicado archivado.');
			modalEliminar = false;
			await cargar();
		} catch (e) {
			error(e);
		} finally {
			guardando = false;
		}
	}

	const colLecturas = [
		{ titulo: 'Acudiente', campo: 'nombre' },
		{ titulo: 'Correo', campo: 'correo' },
		{ titulo: 'Estado', campo: 'confirmado', render: (v) => (v ? insignia('Confirmó', 'success') : insignia('Pendiente', 'warning')) },
		{ titulo: 'Fecha de lectura', campo: 'fecha_confirmacion', render: (v) => (v ? fechaHora(v) : '—') }
	];
</script>

<svelte:head><title>Comunicados · Conecta Escolar</title></svelte:head>

<TituloPagina titulo="Comunicados" icono="bi-megaphone"
	descripcion={esAcudiente() ? 'Circulares del colegio y de los grupos de tus hijos.' : 'Publica circulares y consulta quién las ha leído.'}>
	{#if esPersonal()}
		<button class="btn btn-primary" onclick={nuevo}><i class="bi bi-plus-lg me-1"></i>Nuevo comunicado</button>
	{/if}
</TituloPagina>

{#if esAcudiente() && pendientes > 0}
	<div class="alert alert-warning d-flex align-items-center gap-2">
		<i class="bi bi-exclamation-triangle-fill"></i>
		<div>Tienes <strong>{pendientes}</strong> {pendientes === 1 ? 'circular pendiente' : 'circulares pendientes'} por confirmar.</div>
		<button class="btn btn-sm btn-warning ms-auto" onclick={() => (filtroLectura = 'pendiente')}>Ver pendientes</button>
	</div>
{/if}

<div class="tarjeta tarjeta-cuerpo">
	<div class="filtros">
		<div>
			<label class="form-label small text-muted" for="f-prioridad">Prioridad</label>
			<select id="f-prioridad" class="form-select" bind:value={filtroPrioridad}>
				<option value="">Todas</option><option value="urgente">Urgente</option><option value="normal">Normal</option>
			</select>
		</div>
		{#if esAcudiente()}
			<div>
				<label class="form-label small text-muted" for="f-lectura">Mi lectura</label>
				<select id="f-lectura" class="form-select" bind:value={filtroLectura}>
					<option value="">Todas</option><option value="pendiente">Por confirmar</option><option value="confirmado">Confirmadas</option>
				</select>
			</div>
		{/if}
	</div>
	<Cargando {cargando}>
		<TablaDatos {columnas} datos={visibles} {acciones} ordenInicial={[[4, 'desc']]} />
	</Cargando>
</div>

<!-- Crear / editar -->
<Modal bind:abierto={modalForm} variante={editando ? 'editar' : 'crear'} tamano="lg"
	titulo={editando ? 'Editar comunicado' : 'Nuevo comunicado'}>
	<form id="form-comunicado" onsubmit={guardar} class="row g-3">
		<div class="col-12">
			<label class="form-label" for="c-titulo">Título <span class="text-danger">*</span></label>
			<input id="c-titulo" class="form-control" bind:value={form.titulo} required minlength="3" maxlength="150"
				placeholder="Ej. Reunión de padres del tercer periodo" />
		</div>
		<div class="col-md-7">
			{#if editando}
				<label class="form-label" for="c-dest">Dirigido a</label>
				<input id="c-dest" class="form-control" disabled value={editando.grupo_nombre ? `Grupo ${editando.grupo_nombre}` : 'Todo el colegio'} />
			{:else}
				<SelectorLista bind:valor={form.grupo_id} url="/catalogos/grupos" etiqueta="Dirigido a"
					requerido={!esCoordinacion()} placeholder="Selecciona el grupo"
					opcionVacia={esCoordinacion() ? 'Todo el colegio (circular general)' : null} />
			{/if}
		</div>
		<div class="col-md-5">
			<span class="form-label d-block">Prioridad</span>
			<div class="btn-group w-100" role="group">
				<input type="radio" class="btn-check" id="p-normal" value="normal" bind:group={form.prioridad} />
				<label class="btn btn-outline-secondary" for="p-normal">Normal</label>
				<input type="radio" class="btn-check" id="p-urgente" value="urgente" bind:group={form.prioridad} />
				<label class="btn btn-outline-danger" for="p-urgente"><i class="bi bi-exclamation-circle me-1"></i>Urgente</label>
			</div>
		</div>
		<div class="col-12">
			<label class="form-label" for="c-contenido">Contenido <span class="text-danger">*</span></label>
			<textarea id="c-contenido" class="form-control" rows="6" bind:value={form.contenido} required
				placeholder="Escribe el mensaje completo de la circular..."></textarea>
		</div>
		<div class="col-12">
			<div class="form-check form-switch">
				<input class="form-check-input" type="checkbox" id="c-req" bind:checked={form.requiere_confirmacion} />
				<label class="form-check-label" for="c-req">Solicitar confirmación de lectura a los acudientes</label>
			</div>
		</div>
		{#if !editando}
			<div class="col-12"><div class="alert alert-info small mb-0"><i class="bi bi-bell me-2"></i>Al publicar, los acudientes destinatarios recibirán una notificación en tiempo real.</div></div>
		{/if}
	</form>
	{#snippet pie()}
		<button class="btn btn-light" onclick={() => (modalForm = false)}>Cancelar</button>
		<button class="btn {editando ? 'btn-warning' : 'btn-success'}" form="form-comunicado" disabled={guardando}>
			{#if guardando}<span class="spinner-border spinner-border-sm me-1"></span>{/if}{editando ? 'Actualizar' : 'Publicar'}
		</button>
	{/snippet}
</Modal>

<!-- Ver -->
<Modal bind:abierto={modalVer} variante="ver" tamano="lg" titulo="Detalle del comunicado">
	{#if actual}
		<div class="d-flex flex-wrap gap-2 mb-2">
			<InsigniaEstado estado={actual.prioridad} />
			<span class="badge text-bg-light">{actual.grupo_nombre ? `Grupo ${actual.grupo_nombre}` : 'Todo el colegio'}</span>
		</div>
		<h3 class="h4 fw-bold">{actual.titulo}</h3>
		<div class="text-muted small mb-3"><i class="bi bi-person me-1"></i>{actual.autor_nombre} · <i class="bi bi-clock me-1"></i>{fechaHora(actual.fecha_publicacion)}</div>
		<div class="p-3 bg-light rounded-3 mb-3" style="white-space: pre-line">{actual.contenido}</div>

		{#if esAcudiente() && actual.requiere_confirmacion}
			{#if actual.confirmado_por_mi}
				<div class="alert alert-success mb-0"><i class="bi bi-check-circle-fill me-2"></i>Ya confirmaste la lectura de este comunicado.</div>
			{:else}
				<div class="alert alert-warning d-flex align-items-center gap-2 mb-0">
					<i class="bi bi-hourglass-split"></i> El colegio solicita que confirmes la lectura.
					<button class="btn btn-success btn-sm ms-auto" onclick={confirmar}><i class="bi bi-check2-all me-1"></i>Confirmar lectura</button>
				</div>
			{/if}
		{/if}

		{#if esPersonal() && actual.requiere_confirmacion}
			<h4 class="h6 fw-semibold mt-4">Estado de lectura</h4>
			{#if lecturas}
				<div class="d-flex justify-content-between small mb-1">
					<span>{lecturas.confirmados} de {lecturas.destinatarios} acudientes confirmaron</span><strong>{lecturas.porcentaje}%</strong>
				</div>
				<div class="progress mb-3" style="height: 10px"><div class="progress-bar bg-success" style="width: {lecturas.porcentaje}%"></div></div>
				<TablaDatos columnas={colLecturas} datos={lecturas.detalle} porPagina={5} compacta />
			{:else}
				<Cargando />
			{/if}
		{/if}
	{/if}
	{#snippet pie()}
		<button class="btn btn-light" onclick={() => (modalVer = false)}>Volver</button>
		{#if actual && puedeEditar(actual)}
			<button class="btn btn-warning" onclick={() => { modalVer = false; editar(actual); }}><i class="bi bi-pencil me-1"></i>Editar</button>
		{/if}
	{/snippet}
</Modal>

<ModalConfirmar bind:abierto={modalEliminar} cargando={guardando} alConfirmar={eliminar}
	titulo="Archivar comunicado" mensaje="¿Archivar este comunicado?" textoBoton="Archivar"
	detalle={actual ? `Comunicado: ${actual.titulo}` : ''} />
