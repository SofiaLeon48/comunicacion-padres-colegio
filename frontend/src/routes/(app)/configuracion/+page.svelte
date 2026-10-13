<script>
	import { onMount } from 'svelte';
	import { api } from '$lib/api.js';
	import { error, exito } from '$lib/avisos.svelte.js';
	import Cargando from '$lib/componentes/Cargando.svelte';
	import Modal from '$lib/componentes/Modal.svelte';
	import TablaDatos from '$lib/componentes/TablaDatos.svelte';
	import TituloPagina from '$lib/componentes/TituloPagina.svelte';
	import { esc, insignia, ROLES } from '$lib/formato.js';
	import { actualizarModulos } from '$lib/sesion.svelte.js';

	let pestana = $state('permisos');
	let matriz = $state([]);
	let modulos = $state([]);
	let roles = $state([]);
	let cargando = $state(true);

	let modalModulo = $state(false);
	let modalRol = $state(false);
	let actual = $state(null);
	let formModulo = $state({});
	let formRol = $state({});
	let aviso = $state({ titulo: '', contenido: '', roles: [] });
	let enviando = $state(false);

	const rolesMatriz = $derived([...new Map(matriz.map((p) => [p.rol_id, p.rol])).entries()]);
	const modulosMatriz = $derived([...new Map(matriz.map((p) => [p.modulo_id, p])).values()].sort((a, b) => a.orden - b.orden));
	const celda = (rol_id, modulo_id) => matriz.find((p) => p.rol_id === rol_id && p.modulo_id === modulo_id);

	async function cargar() {
		try {
			[matriz, modulos, roles] = await Promise.all([
				api.get('/configuracion/permisos'),
				api.get('/configuracion/modulos?incluir_inactivos=true'),
				api.get('/roles/?incluir_inactivos=true')
			]);
		} catch (e) {
			error(e);
		} finally {
			cargando = false;
		}
	}
	onMount(cargar);

	async function alternar(p) {
		const nuevo = !p.permitido;
		try {
			const r = await api.put('/configuracion/permisos', { rol_id: p.rol_id, modulo_id: p.modulo_id, permitido: nuevo });
			p.permitido = nuevo;
			exito(r.mensaje);
			actualizarModulos(await api.get('/auth/mis-modulos'));
		} catch (e) {
			error(e);
		}
	}

	const colModulos = [
		{ titulo: 'Orden', campo: 'orden' },
		{ titulo: 'Módulo', campo: 'nombre', render: (v, m) => `<i class="bi ${esc(m.icono)} me-2 text-primary"></i><span class="fw-semibold">${esc(v)}</span>` },
		{ titulo: 'Ruta', campo: 'ruta', render: (v) => `<code>${esc(v)}</code>` },
		{ titulo: 'Descripción', campo: 'descripcion' },
		{ titulo: 'Estado', campo: 'estado', render: (v) => insignia(v === 'activo' ? 'Activo' : 'Inactivo', v === 'activo' ? 'success' : 'secondary') }
	];
	const accModulos = [{ icono: 'bi-pencil', titulo: 'Editar', color: 'warning', accion: (m) => {
		actual = m;
		formModulo = { nombre: m.nombre, descripcion: m.descripcion ?? '', icono: m.icono, orden: m.orden, activo: m.estado === 'activo' };
		modalModulo = true;
	} }];

	const colRoles = [
		{ titulo: 'Rol', campo: 'nombre', render: (v) => `<span class="fw-semibold">${esc(ROLES[v] ?? v)}</span>` },
		{ titulo: 'Descripción', campo: 'descripcion' },
		{ titulo: 'Módulos asignados', campo: 'nombre', render: (_, r) => String(matriz.filter((p) => p.rol_id === r.id && p.permitido).length), ordenable: false },
		{ titulo: 'Estado', campo: 'estado', render: (v) => insignia(v === 'activo' ? 'Activo' : 'Inactivo', v === 'activo' ? 'success' : 'secondary') }
	];
	const accRoles = [{ icono: 'bi-pencil', titulo: 'Editar', color: 'warning', accion: (r) => {
		actual = r;
		formRol = { descripcion: r.descripcion ?? '' };
		modalRol = true;
	} }];

	async function guardarModulo(e) {
		e.preventDefault();
		try {
			const { activo, ...datos } = formModulo;
			await api.patch(`/configuracion/modulos/${actual.id}`, { ...datos, estado: activo ? 'activo' : 'inactivo' });
			exito('Módulo actualizado. El menú se actualiza para todos los usuarios.');
			modalModulo = false;
			await cargar();
			actualizarModulos(await api.get('/auth/mis-modulos'));
		} catch (err) {
			error(err);
		}
	}
	async function guardarRol(e) {
		e.preventDefault();
		try {
			await api.patch(`/roles/${actual.id}`, formRol);
			exito('Rol actualizado.');
			modalRol = false;
			await cargar();
		} catch (err) {
			error(err);
		}
	}
	async function enviarAviso(e) {
		e.preventDefault();
		if (!aviso.roles.length) return error('Selecciona al menos un rol destinatario.');
		enviando = true;
		try {
			const r = await api.post('/notificaciones/', aviso);
			exito(r.mensaje);
			aviso = { titulo: '', contenido: '', roles: [] };
		} catch (err) {
			error(err);
		} finally {
			enviando = false;
		}
	}
</script>

<svelte:head><title>Configuración · Conecta Escolar</title></svelte:head>

<TituloPagina titulo="Configuración" icono="bi-gear" descripcion="Define qué módulos ve cada rol, administra los módulos y envía avisos del sistema." />

<ul class="nav nav-tabs nav-pestanas mb-3">
	<li class="nav-item"><button class="nav-link" class:active={pestana === 'permisos'} onclick={() => (pestana = 'permisos')}><i class="bi bi-shield-lock me-1"></i>Permisos por rol</button></li>
	<li class="nav-item"><button class="nav-link" class:active={pestana === 'modulos'} onclick={() => (pestana = 'modulos')}><i class="bi bi-grid me-1"></i>Módulos</button></li>
	<li class="nav-item"><button class="nav-link" class:active={pestana === 'roles'} onclick={() => (pestana = 'roles')}><i class="bi bi-person-badge me-1"></i>Roles</button></li>
	<li class="nav-item"><button class="nav-link" class:active={pestana === 'avisos'} onclick={() => (pestana = 'avisos')}><i class="bi bi-broadcast me-1"></i>Avisos del sistema</button></li>
</ul>

<Cargando {cargando}>
	{#if pestana === 'permisos'}
		<div class="tarjeta tarjeta-cuerpo">
			<p class="text-muted small"><i class="bi bi-info-circle me-1"></i>Cada interruptor corresponde a un registro de la tabla <strong>rol_modulo</strong>. Al cambiarlo, el menú y los permisos de la API se actualizan de inmediato.</p>
			<div class="table-responsive">
				<table class="table align-middle">
					<thead class="table-light">
						<tr><th>Módulo</th>{#each rolesMatriz as [rid, rnombre]}<th class="text-center">{ROLES[rnombre] ?? rnombre}</th>{/each}</tr>
					</thead>
					<tbody>
						{#each modulosMatriz as m (m.modulo_id)}
							<tr>
								<td><i class="bi {m.icono} me-2 text-primary"></i><span class="fw-semibold">{m.modulo}</span></td>
								{#each rolesMatriz as [rid, rnombre]}
									{@const p = celda(rid, m.modulo_id)}
									<td class="text-center">
										<div class="form-check form-switch d-inline-block">
											<input class="form-check-input" type="checkbox" role="switch" checked={p?.permitido}
												disabled={rnombre === 'coordinacion' && m.clave === 'configuracion'}
												aria-label="{m.modulo} para {ROLES[rnombre]}" onchange={() => alternar(p)} />
										</div>
									</td>
								{/each}
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	{:else if pestana === 'modulos'}
		<div class="tarjeta tarjeta-cuerpo"><TablaDatos columnas={colModulos} datos={modulos} acciones={accModulos} ordenInicial={[[0, 'asc']]} /></div>
	{:else if pestana === 'roles'}
		<div class="tarjeta tarjeta-cuerpo"><TablaDatos columnas={colRoles} datos={roles} acciones={accRoles} /></div>
	{:else}
		<div class="tarjeta tarjeta-cuerpo" style="max-width: 720px">
			<p class="text-muted small">El aviso llega en tiempo real a la campana de notificaciones de los usuarios seleccionados.</p>
			<form onsubmit={enviarAviso} class="row g-3">
				<div class="col-12">
					<label class="form-label" for="a-tit">Título <span class="text-danger">*</span></label>
					<input id="a-tit" class="form-control" bind:value={aviso.titulo} required minlength="3" maxlength="150" placeholder="Ej. Simulacro de evacuación" />
				</div>
				<div class="col-12">
					<label class="form-label" for="a-cont">Mensaje <span class="text-danger">*</span></label>
					<textarea id="a-cont" class="form-control" rows="3" bind:value={aviso.contenido} required maxlength="255" placeholder="Máximo 255 caracteres"></textarea>
				</div>
				<div class="col-12">
					<span class="form-label d-block">Destinatarios</span>
					{#each Object.entries(ROLES) as [k, t]}
						<div class="form-check form-check-inline">
							<input class="form-check-input" type="checkbox" id="r-{k}" value={k} bind:group={aviso.roles} />
							<label class="form-check-label" for="r-{k}">{t}</label>
						</div>
					{/each}
				</div>
				<div class="col-12"><button class="btn btn-primary" disabled={enviando}><i class="bi bi-send me-1"></i>Enviar aviso</button></div>
			</form>
		</div>
	{/if}
</Cargando>

<Modal bind:abierto={modalModulo} variante="editar" titulo="Editar módulo">
	<form id="form-mod" onsubmit={guardarModulo} class="row g-3">
		<div class="col-md-8">
			<label class="form-label" for="m-nom">Nombre en el menú</label>
			<input id="m-nom" class="form-control" bind:value={formModulo.nombre} required minlength="3" maxlength="50" />
		</div>
		<div class="col-md-4">
			<label class="form-label" for="m-ord">Orden</label>
			<input id="m-ord" type="number" class="form-control" bind:value={formModulo.orden} min="0" max="99" />
		</div>
		<div class="col-12">
			<label class="form-label" for="m-desc">Descripción</label>
			<input id="m-desc" class="form-control" bind:value={formModulo.descripcion} maxlength="150" />
		</div>
		<div class="col-md-8">
			<label class="form-label" for="m-ico">Icono (Bootstrap Icons)</label>
			<div class="input-group">
				<span class="input-group-text"><i class="bi {formModulo.icono}"></i></span>
				<input id="m-ico" class="form-control" bind:value={formModulo.icono} maxlength="40" />
			</div>
		</div>
		<div class="col-md-4 d-flex align-items-end">
			<div class="form-check form-switch mb-2">
				<input class="form-check-input" type="checkbox" id="m-act" bind:checked={formModulo.activo} disabled={actual?.clave === 'configuracion'} />
				<label class="form-check-label" for="m-act">Activo</label>
			</div>
		</div>
	</form>
	{#snippet pie()}
		<button class="btn btn-light" onclick={() => (modalModulo = false)}>Cancelar</button>
		<button class="btn btn-warning" form="form-mod">Actualizar</button>
	{/snippet}
</Modal>

<Modal bind:abierto={modalRol} variante="editar" titulo="Editar rol: {ROLES[actual?.nombre] ?? ''}">
	<form id="form-rol" onsubmit={guardarRol}>
		<label class="form-label" for="r-desc">Descripción</label>
		<input id="r-desc" class="form-control" bind:value={formRol.descripcion} maxlength="150" />
	</form>
	{#snippet pie()}
		<button class="btn btn-light" onclick={() => (modalRol = false)}>Cancelar</button>
		<button class="btn btn-warning" form="form-rol">Actualizar</button>
	{/snippet}
</Modal>
