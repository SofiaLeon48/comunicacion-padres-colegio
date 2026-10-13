<script>
	import { api } from '$lib/api.js';
	import { error, exito } from '$lib/avisos.svelte.js';
	import TituloPagina from '$lib/componentes/TituloPagina.svelte';
	import { fechaHora, iniciales, ROLES } from '$lib/formato.js';
	import { actualizarUsuario, sesion } from '$lib/sesion.svelte.js';

	let datos = $state({ nombre: sesion.usuario?.nombre ?? '', telefono: sesion.usuario?.telefono ?? '' });
	let claves = $state({ password_actual: '', password_nueva: '', confirmar: '' });

	async function guardarDatos(e) {
		e.preventDefault();
		try {
			actualizarUsuario(await api.patch('/auth/me', { nombre: datos.nombre, telefono: datos.telefono || null }));
			exito('Tus datos fueron actualizados.');
		} catch (err) {
			error(err);
		}
	}
	async function cambiarClave(e) {
		e.preventDefault();
		if (claves.password_nueva !== claves.confirmar) return error('Las contraseñas nuevas no coinciden.');
		try {
			const r = await api.put('/auth/me/password', { password_actual: claves.password_actual, password_nueva: claves.password_nueva });
			exito(r.mensaje);
			claves = { password_actual: '', password_nueva: '', confirmar: '' };
		} catch (err) {
			error(err);
		}
	}
</script>

<svelte:head><title>Mi perfil · Conecta Escolar</title></svelte:head>

<TituloPagina titulo="Mi perfil" icono="bi-person-circle" descripcion="Actualiza tus datos de contacto y tu contraseña." />

<div class="row g-4">
	<div class="col-lg-4">
		<div class="tarjeta tarjeta-cuerpo text-center">
			<span class="avatar mx-auto mb-3" style="width: 84px; height: 84px; font-size: 1.8rem">{iniciales(sesion.usuario?.nombre)}</span>
			<div class="fw-bold fs-5">{sesion.usuario?.nombre}</div>
			<div class="text-muted">{sesion.usuario?.correo}</div>
			<span class="badge text-bg-primary mt-2">{ROLES[sesion.usuario?.rol]}</span>
			<hr />
			<div class="small text-muted">Miembro desde {fechaHora(sesion.usuario?.creado)}</div>
		</div>
	</div>
	<div class="col-lg-8">
		<div class="tarjeta tarjeta-cuerpo mb-4">
			<h2 class="h6 fw-semibold mb-3">Datos personales</h2>
			<form class="row g-3" onsubmit={guardarDatos}>
				<div class="col-md-7">
					<label class="form-label" for="p-nom">Nombre completo</label>
					<input id="p-nom" class="form-control" bind:value={datos.nombre} required minlength="3" maxlength="100" />
				</div>
				<div class="col-md-5">
					<label class="form-label" for="p-tel">Teléfono</label>
					<input id="p-tel" class="form-control" bind:value={datos.telefono} maxlength="20" />
				</div>
				<div class="col-md-7">
					<label class="form-label" for="p-cor">Correo</label>
					<input id="p-cor" class="form-control" value={sesion.usuario?.correo} disabled />
				</div>
				<div class="col-md-5">
					<label class="form-label" for="p-rol">Rol</label>
					<input id="p-rol" class="form-control" value={ROLES[sesion.usuario?.rol]} disabled />
				</div>
				<div class="col-12"><button class="btn btn-primary">Guardar cambios</button></div>
			</form>
		</div>
		<div class="tarjeta tarjeta-cuerpo">
			<h2 class="h6 fw-semibold mb-3">Cambiar contraseña</h2>
			<form class="row g-3" onsubmit={cambiarClave}>
				<div class="col-md-4">
					<label class="form-label" for="p-act">Contraseña actual</label>
					<input id="p-act" type="password" class="form-control" bind:value={claves.password_actual} required autocomplete="current-password" />
				</div>
				<div class="col-md-4">
					<label class="form-label" for="p-new">Nueva contraseña</label>
					<input id="p-new" type="password" class="form-control" bind:value={claves.password_nueva} required minlength="8" autocomplete="new-password" />
				</div>
				<div class="col-md-4">
					<label class="form-label" for="p-conf">Confirmar</label>
					<input id="p-conf" type="password" class="form-control" bind:value={claves.confirmar} required minlength="8" autocomplete="new-password" />
				</div>
				<div class="col-12"><button class="btn btn-warning">Actualizar contraseña</button></div>
			</form>
		</div>
	</div>
</div>
