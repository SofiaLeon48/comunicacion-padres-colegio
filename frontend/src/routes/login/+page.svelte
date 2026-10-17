<script>
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { api } from '$lib/api.js';
	import { NOMBRE_APP, NOMBRE_COLEGIO } from '$lib/config.js';
	import { ROLES } from '$lib/formato.js';
	import { iniciarSesion, sesion } from '$lib/sesion.svelte.js';

	let correo = $state('');
	let password = $state('');
	let rol = $state('');
	let roles = $state([]);
	let verPassword = $state(false);
	let cargando = $state(false);
	let mensajeError = $state('');
	let demoAbierto = $state(false);

	const DEMO = [
		['coordinacion', 'coordinacion@colegio.edu.co', 'Patricia Herrera'],
		['docente', 'lmartinez@colegio.edu.co', 'Luis F. Martínez (5A)'],
		['acudiente', 'maria.rodriguez@correo.com', 'María Rodríguez']
	];

	onMount(async () => {
		if (sesion.token) return goto('/inicio');
		try {
			roles = await api.get('/auth/roles');
		} catch (e) {
			mensajeError = e.message;
		}
	});

	async function ingresar(e) {
		e.preventDefault();
		mensajeError = '';
		if (!rol) {
			mensajeError = 'Selecciona el rol con el que vas a ingresar.';
			return;
		}
		cargando = true;
		try {
			const r = await api.post('/auth/login', { correo, password, rol });
			iniciarSesion(r);
			goto(r.modulos[0]?.ruta ?? '/inicio');
		} catch (err) {
			mensajeError = err.message;
		} finally {
			cargando = false;
		}
	}

	function usarDemo([r, c]) {
		rol = r;
		correo = c;
		password = 'Colegio2026*';
		demoAbierto = false;
	}
</script>

<svelte:head><title>Iniciar sesión · {NOMBRE_APP}</title></svelte:head>

<div class="login-fondo container-fluid">
	<div class="row min-vh-100">
		<div class="col-lg-6 login-panel d-none d-lg-flex flex-column justify-content-between p-5">
			<div class="d-flex align-items-center gap-2">
				<img src="/favicon.svg" alt="" width="44" height="44" />
				<span class="fs-4 fw-bold">{NOMBRE_APP}</span>
			</div>
			<div style="max-width: 480px">
				<h1 class="display-6 fw-bold mb-3">La comunicación entre el colegio y la familia, en un solo lugar.</h1>
				<p class="opacity-75 mb-4">Adiós a los mensajes perdidos en WhatsApp y a las circulares en papel.</p>
				<div class="d-flex flex-column gap-3">
					<div class="beneficio d-flex align-items-center gap-3"><i class="bi bi-megaphone"></i> Circulares digitales con confirmación de lectura</div>
					<div class="beneficio d-flex align-items-center gap-3"><i class="bi bi-chat-dots"></i> Mensajería por grupo y directa con los docentes</div>
					<div class="beneficio d-flex align-items-center gap-3"><i class="bi bi-calendar-event"></i> Calendario de citaciones a padres</div>
					<div class="beneficio d-flex align-items-center gap-3"><i class="bi bi-bell"></i> Notificaciones en tiempo real</div>
				</div>
			</div>
			<div class="small opacity-75">{NOMBRE_COLEGIO} · Canal oficial de comunicación</div>
		</div>

		<div class="col-lg-6 d-flex align-items-center justify-content-center p-4">
			<div class="tarjeta-login">
				<div class="text-center mb-4 d-lg-none">
					<img src="/favicon.svg" alt="" width="56" height="56" />
					<div class="fs-4 fw-bold mt-2">{NOMBRE_APP}</div>
				</div>
				<div class="tarjeta p-4 p-md-5">
					<h2 class="h4 fw-bold mb-1">Iniciar sesión</h2>
					<p class="text-muted small mb-4">Ingresa con tu correo institucional o personal registrado.</p>

					{#if mensajeError}
						<div class="alert alert-danger small py-2"><i class="bi bi-exclamation-circle me-2"></i>{mensajeError}</div>
					{/if}

					<form onsubmit={ingresar}>
						<div class="mb-3">
							<label class="form-label" for="rol">Ingresar como</label>
							<div class="input-group">
								<span class="input-group-text"><i class="bi bi-person-badge"></i></span>
								<select id="rol" class="form-select" bind:value={rol} required>
									<option value="" disabled>Selecciona tu rol</option>
									{#each roles as r}
										<option value={r.nombre}>{ROLES[r.nombre] ?? r.nombre}</option>
									{/each}
								</select>
							</div>
						</div>
						<div class="mb-3">
							<label class="form-label" for="correo">Correo electrónico</label>
							<div class="input-group">
								<span class="input-group-text"><i class="bi bi-envelope"></i></span>
								<input id="correo" type="email" class="form-control" placeholder="nombre@correo.com"
									bind:value={correo} required autocomplete="username" />
							</div>
						</div>
						<div class="mb-4">
							<label class="form-label" for="password">Contraseña</label>
							<div class="input-group">
								<span class="input-group-text"><i class="bi bi-lock"></i></span>
								<input id="password" type={verPassword ? 'text' : 'password'} class="form-control"
									placeholder="Tu contraseña" bind:value={password} required autocomplete="current-password" />
								<button type="button" class="btn btn-outline-secondary" aria-label="Mostrar contraseña"
									onclick={() => (verPassword = !verPassword)}>
									<i class="bi {verPassword ? 'bi-eye-slash' : 'bi-eye'}"></i>
								</button>
							</div>
						</div>
						<button class="btn btn-primary w-100 py-2 fw-semibold" disabled={cargando}>
							{#if cargando}<span class="spinner-border spinner-border-sm me-2"></span>Ingresando...{:else}Ingresar{/if}
						</button>
					</form>

					<div class="mt-4 border-top pt-3">
						<button class="btn btn-link btn-sm p-0 text-decoration-none" onclick={() => (demoAbierto = !demoAbierto)}>
							<i class="bi bi-lightning-charge me-1"></i>Cuentas de demostración
						</button>
						{#if demoAbierto}
							<div class="list-group mt-2">
								{#each DEMO as d}
									<button type="button" class="list-group-item list-group-item-action small d-flex justify-content-between"
										onclick={() => usarDemo(d)}>
										<span>{d[2]}</span><span class="badge text-bg-light">{ROLES[d[0]]}</span>
									</button>
								{/each}
							</div>
						{/if}
					</div>
				</div>
			</div>
		</div>
	</div>
</div>
