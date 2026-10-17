<script>
	import { onMount } from 'svelte';
	import { api, qs } from '$lib/api.js';
	import { error, exito } from '$lib/avisos.svelte.js';
	import Cargando from '$lib/componentes/Cargando.svelte';
	import Modal from '$lib/componentes/Modal.svelte';
	import ModalConfirmar from '$lib/componentes/ModalConfirmar.svelte';
	import SelectorLista from '$lib/componentes/SelectorLista.svelte';
	import TablaDatos from '$lib/componentes/TablaDatos.svelte';
	import TarjetaIndicador from '$lib/componentes/TarjetaIndicador.svelte';
	import TituloPagina from '$lib/componentes/TituloPagina.svelte';
	import { COLOR_ROL, esc, fechaHora, haceCuanto, insignia, ROLES } from '$lib/formato.js';
	import { sesion } from '$lib/sesion.svelte.js';

	let lista = $state([]);
	let cargando = $state(true);
	let filtroRol = $state('');
	let verInactivos = $state(false);
	let modalForm = $state(false);
	let modalVer = $state(false);
	let modalEliminar = $state(false);
	let editando = $state(null);
	let actual = $state(null);
	let guardando = $state(false);
	let form = $state(vacio());

	function vacio() {
		return { nombre: '', correo: '', telefono: '', rol_id: null, password: '' };
	}
	const cuenta = (r) => lista.filter((u) => u.rol === r && u.estado === 'activo').length;

	async function cargar() {
		cargando = true;
		try {
			lista = await api.get('/usuarios/' + qs({ rol: filtroRol, incluir_inactivos: verInactivos || null }));
		} catch (e) {
			error(e);
		} finally {
			cargando = false;
		}
	}
	onMount(cargar);

	const columnas = [
		{ titulo: 'Nombre', campo: 'nombre', render: (v) => `<span class="fw-semibold">${esc(v)}</span>` },
		{ titulo: 'Correo', campo: 'correo' },
		{ titulo: 'Teléfono', campo: 'telefono' },
		{ titulo: 'Rol', campo: 'rol', render: (v) => insignia(ROLES[v] ?? v, COLOR_ROL[v] ?? 'secondary') },
		{ titulo: 'Último acceso', campo: 'ultimo_acceso', render: (v) => (v ? haceCuanto(v) : '<span class="text-muted">Nunca</span>'), orden: (u) => u.ultimo_acceso ?? '' },
		{ titulo: 'Estado', campo: 'estado', render: (v) => insignia(v === 'activo' ? 'Activo' : 'Inactivo', v === 'activo' ? 'success' : 'secondary') }
	];
	const acciones = [
		{ icono: 'bi-eye', titulo: 'Ver', color: 'primary', accion: (u) => { actual = u; modalVer = true; } },
		{ icono: 'bi-pencil', titulo: 'Editar', color: 'warning', accion: editar },
		{ icono: 'bi-person-x', titulo: 'Desactivar', color: 'danger', accion: (u) => { actual = u; modalEliminar = true; }, visible: (u) => u.estado === 'activo' && u.id !== sesion.usuario?.id },
		{ icono: 'bi-arrow-counterclockwise', titulo: 'Reactivar', color: 'success', accion: reactivar, visible: (u) => u.estado === 'inactivo' }
	];

	function nuevo() {
		editando = null;
		form = vacio();
		modalForm = true;
	}
	function editar(u) {
		editando = u;
		form = { nombre: u.nombre, correo: u.correo, telefono: u.telefono ?? '', rol_id: u.rol_id, password: '' };
		modalForm = true;
	}

	async function guardar(e) {
		e.preventDefault();
		if (!form.rol_id) return error('Selecciona el rol.');
		guardando = true;
		const datos = { ...form, telefono: form.telefono || null };
		if (editando && !datos.password) delete datos.password;
		try {
			if (editando) await api.patch(`/usuarios/${editando.id}`, datos);
			else await api.post('/usuarios/', datos);
			exito(editando ? 'Usuario actualizado.' : 'Usuario creado. Ya puede iniciar sesión.');
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
			await api.del(`/usuarios/${actual.id}`);
			exito('Usuario desactivado. Ya no podrá iniciar sesión.');
			modalEliminar = false;
			await cargar();
		} catch (e) {
			error(e);
		} finally {
			guardando = false;
		}
	}
	async function reactivar(u) {
		try {
			await api.post(`/usuarios/${u.id}/reactivar`);
			exito('Usuario reactivado.');
			await cargar();
		} catch (e) {
			error(e);
		}
	}
</script>

<svelte:head><title>Usuarios · Conecta Escolar</title></svelte:head>

<TituloPagina titulo="Usuarios" icono="bi-people" descripcion="Cuentas de coordinación, docentes y acudientes.">
	<button class="btn btn-primary" onclick={nuevo}><i class="bi bi-person-plus me-1"></i>Nuevo usuario</button>
</TituloPagina>

<div class="row g-3 mb-4">
	<div class="col-md-4"><TarjetaIndicador titulo="Coordinación" valor={cuenta('coordinacion')} icono="bi-shield-check" /></div>
	<div class="col-md-4"><TarjetaIndicador titulo="Docentes" valor={cuenta('docente')} icono="bi-person-video3" color="success" /></div>
	<div class="col-md-4"><TarjetaIndicador titulo="Acudientes" valor={cuenta('acudiente')} icono="bi-house-heart" color="info" /></div>
</div>

<div class="tarjeta tarjeta-cuerpo">
	<div class="filtros">
		<div>
			<label class="form-label small text-muted" for="f-rol">Rol</label>
			<select id="f-rol" class="form-select" bind:value={filtroRol} onchange={cargar}>
				<option value="">Todos los roles</option>
				{#each Object.entries(ROLES) as [k, t]}<option value={k}>{t}</option>{/each}
			</select>
		</div>
		<div class="form-check form-switch mb-2">
			<input class="form-check-input" type="checkbox" id="inact" bind:checked={verInactivos} onchange={cargar} />
			<label class="form-check-label" for="inact">Mostrar inactivos</label>
		</div>
	</div>
	<Cargando {cargando}>
		<TablaDatos {columnas} datos={lista} {acciones} ordenInicial={[[0, 'asc']]} />
	</Cargando>
</div>

<Modal bind:abierto={modalVer} variante="ver" titulo="Detalle del usuario">
	{#if actual}
		<div class="text-center mb-3">
			<span class="avatar mx-auto mb-2" style="width: 64px; height: 64px; font-size: 1.3rem">{actual.nombre.split(' ').slice(0, 2).map((p) => p[0]).join('')}</span>
			<div class="fw-bold fs-5">{actual.nombre}</div>
			<div>{@html insignia(ROLES[actual.rol], COLOR_ROL[actual.rol])}</div>
		</div>
		<dl class="row mb-0">
			<dt class="col-5 text-muted fw-normal">Correo</dt><dd class="col-7">{actual.correo}</dd>
			<dt class="col-5 text-muted fw-normal">Teléfono</dt><dd class="col-7">{actual.telefono ?? '—'}</dd>
			<dt class="col-5 text-muted fw-normal">Último acceso</dt><dd class="col-7">{actual.ultimo_acceso ? fechaHora(actual.ultimo_acceso) : 'Nunca'}</dd>
			<dt class="col-5 text-muted fw-normal">Registrado</dt><dd class="col-7">{fechaHora(actual.creado)}</dd>
			<dt class="col-5 text-muted fw-normal">Estado</dt><dd class="col-7 text-capitalize">{actual.estado}</dd>
		</dl>
	{/if}
	{#snippet pie()}
		<button class="btn btn-light" onclick={() => (modalVer = false)}>Volver</button>
		<button class="btn btn-warning" onclick={() => { modalVer = false; editar(actual); }}>Editar</button>
	{/snippet}
</Modal>

<Modal bind:abierto={modalForm} variante={editando ? 'editar' : 'crear'} titulo={editando ? 'Editar usuario' : 'Nuevo usuario'}>
	<form id="form-usuario" onsubmit={guardar} class="row g-3">
		<div class="col-12">
			<label class="form-label" for="u-nombre">Nombre completo <span class="text-danger">*</span></label>
			<input id="u-nombre" class="form-control" bind:value={form.nombre} required minlength="3" maxlength="100" placeholder="Ej. Marta Lucía Herrera" />
		</div>
		<div class="col-md-7">
			<label class="form-label" for="u-correo">Correo <span class="text-danger">*</span></label>
			<input id="u-correo" type="email" class="form-control" bind:value={form.correo} required placeholder="nombre@correo.com" />
		</div>
		<div class="col-md-5">
			<label class="form-label" for="u-tel">Teléfono</label>
			<input id="u-tel" class="form-control" bind:value={form.telefono} maxlength="20" inputmode="tel" placeholder="3001234567" />
		</div>
		<div class="col-md-6">
			<SelectorLista bind:valor={form.rol_id} url="/catalogos/roles" etiqueta="Rol" requerido placeholder="Selecciona el rol" />
		</div>
		<div class="col-md-6">
			<label class="form-label" for="u-pass">Contraseña {#if !editando}<span class="text-danger">*</span>{/if}</label>
			<input id="u-pass" type="password" class="form-control" bind:value={form.password} required={!editando} minlength="8" maxlength="72"
				placeholder={editando ? 'Déjala vacía para no cambiarla' : 'Mínimo 8 caracteres'} autocomplete="new-password" />
		</div>
	</form>
	{#snippet pie()}
		<button class="btn btn-light" onclick={() => (modalForm = false)}>Cancelar</button>
		<button class="btn {editando ? 'btn-warning' : 'btn-success'}" form="form-usuario" disabled={guardando}>{editando ? 'Actualizar' : 'Crear usuario'}</button>
	{/snippet}
</Modal>

<ModalConfirmar bind:abierto={modalEliminar} cargando={guardando} alConfirmar={eliminar} titulo="Desactivar usuario"
	mensaje="¿Desactivar este usuario?" textoBoton="Desactivar" detalle={actual ? `${actual.nombre} · ${actual.correo}` : ''} />
