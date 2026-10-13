<script>
	import { onDestroy, onMount, tick } from 'svelte';
	import { api } from '$lib/api.js';
	import { error } from '$lib/avisos.svelte.js';
	import Cargando from '$lib/componentes/Cargando.svelte';
	import Modal from '$lib/componentes/Modal.svelte';
	import SelectorLista from '$lib/componentes/SelectorLista.svelte';
	import TituloPagina from '$lib/componentes/TituloPagina.svelte';
	import { fechaHora, haceCuanto, iniciales, ROLES } from '$lib/formato.js';
	import { sesion } from '$lib/sesion.svelte.js';
	import { alRecibir } from '$lib/tiempoReal.svelte.js';

	let pestana = $state('curso');

	// --- chat del curso
	let cursos = $state([]);
	let cursoId = $state(null);
	let chat = $state([]);
	let cargandoChat = $state(false);
	let textoCurso = $state('');
	let cajaCurso = $state();

	// --- directos
	let bandeja = $state([]);
	let contraparte = $state(null); // { id, nombre, rol }
	let conversacion = $state([]);
	let textoDirecto = $state('');
	let cajaDirecto = $state();
	let modalNuevo = $state(false);
	let nuevoContacto = $state(null);
	let infoContacto = $state(null);

	const noLeidosTotal = $derived(bandeja.reduce((s, b) => s + Number(b.no_leidos), 0));
	const yo = () => sesion.usuario?.id;

	async function bajar(caja) {
		await tick();
		if (caja) caja.scrollTop = caja.scrollHeight;
	}

	async function cargarCursos() {
		cursos = await api.get('/catalogos/cursos');
		// Un docente arranca en el curso que dirige; los demás, en el primero de su lista
		const propio = cursos.find((c) => c.director_id === sesion.usuario?.id);
		if (cursos.length && !cursoId) await elegirCurso((propio ?? cursos[0]).id);
	}

	async function elegirCurso(id) {
		cursoId = id;
		cargandoChat = true;
		try {
			chat = await api.get(`/mensajes/curso/${id}?limite=100`);
			bajar(cajaCurso);
		} catch (e) {
			error(e);
		} finally {
			cargandoChat = false;
		}
	}

	async function enviarCurso(e) {
		e.preventDefault();
		const contenido = textoCurso.trim();
		if (!contenido || !cursoId) return;
		textoCurso = '';
		try {
			const m = await api.post('/mensajes/', { curso_id: cursoId, contenido });
			if (!chat.some((x) => x.id === m.id)) chat = [...chat, m];
			bajar(cajaCurso);
		} catch (err) {
			error(err);
			textoCurso = contenido;
		}
	}

	async function cargarBandeja() {
		try {
			bandeja = await api.get('/mensajes/directos');
		} catch (e) {
			error(e);
		}
	}

	async function abrirConversacion(c) {
		contraparte = c;
		try {
			conversacion = await api.get(`/mensajes/directos/${c.id}?limite=100`);
			bajar(cajaDirecto);
			cargarBandeja();
		} catch (e) {
			error(e);
		}
	}

	async function enviarDirecto(e) {
		e.preventDefault();
		const contenido = textoDirecto.trim();
		if (!contenido || !contraparte) return;
		textoDirecto = '';
		try {
			const m = await api.post('/mensajes/', { destinatario_id: contraparte.id, contenido });
			if (!conversacion.some((x) => x.id === m.id)) conversacion = [...conversacion, m];
			bajar(cajaDirecto);
			cargarBandeja();
		} catch (err) {
			error(err);
			textoDirecto = contenido;
		}
	}

	function iniciarNueva() {
		if (!nuevoContacto || !infoContacto) return;
		modalNuevo = false;
		pestana = 'directos';
		abrirConversacion({ id: infoContacto.id, nombre: infoContacto.nombre, rol: infoContacto.rol });
		nuevoContacto = null;
	}

	onMount(async () => {
		try {
			await Promise.all([cargarCursos(), cargarBandeja()]);
		} catch (e) {
			error(e);
		}
	});

	// Mensajes en tiempo real
	const quitar = alRecibir((m) => {
		if (m.evento !== 'mensaje') return;
		const msg = m.datos;
		if (msg.curso_id) {
			if (msg.curso_id === cursoId && !chat.some((x) => x.id === msg.id)) {
				chat = [...chat, msg];
				bajar(cajaCurso);
			}
		} else {
			const otro = msg.remitente_id === yo() ? msg.destinatario_id : msg.remitente_id;
			if (contraparte && otro === contraparte.id && !conversacion.some((x) => x.id === msg.id)) {
				conversacion = [...conversacion, msg];
				bajar(cajaDirecto);
				if (msg.remitente_id !== yo()) api.get(`/mensajes/directos/${otro}?limite=1`).catch(() => {});
			}
			cargarBandeja();
		}
	});
	onDestroy(quitar);
</script>

<svelte:head><title>Mensajería · Conecta Escolar</title></svelte:head>

<TituloPagina titulo="Mensajería" icono="bi-chat-dots" descripcion="Conversa con todo el curso o en privado con una persona.">
	<button class="btn btn-primary" onclick={() => (modalNuevo = true)}><i class="bi bi-pencil-square me-1"></i>Nuevo mensaje directo</button>
</TituloPagina>

<ul class="nav nav-tabs nav-pestanas mb-3">
	<li class="nav-item"><button class="nav-link" class:active={pestana === 'curso'} onclick={() => (pestana = 'curso')}><i class="bi bi-people me-1"></i>Chat de curso</button></li>
	<li class="nav-item">
		<button class="nav-link" class:active={pestana === 'directos'} onclick={() => (pestana = 'directos')}>
			<i class="bi bi-person-lines-fill me-1"></i>Mensajes directos
			{#if noLeidosTotal > 0}<span class="badge rounded-pill bg-danger ms-1">{noLeidosTotal}</span>{/if}
		</button>
	</li>
</ul>

{#if pestana === 'curso'}
	<div class="tarjeta tarjeta-cuerpo">
		<div class="row g-3 align-items-end mb-3">
			<div class="col-md-5">
				<label class="form-label small text-muted" for="sel-curso">Curso</label>
				<select id="sel-curso" class="form-select" value={cursoId ? String(cursoId) : ''} onchange={(e) => elegirCurso(Number(e.target.value))}>
					{#each cursos as c (c.id)}<option value={String(c.id)}>{c.etiqueta}</option>{/each}
				</select>
			</div>
			<div class="col-md-7 text-md-end small text-muted">
				<i class="bi bi-broadcast me-1 text-success"></i>Los mensajes llegan en tiempo real a los acudientes del curso y a su director de grupo.
			</div>
		</div>
		{#if !cursos.length}
			<div class="text-center text-muted py-5">No tienes cursos disponibles para chatear.</div>
		{:else}
			<div class="chat-caja" bind:this={cajaCurso}>
				<Cargando cargando={cargandoChat} vacio={!chat.length} textoVacio="Aún no hay mensajes. ¡Escribe el primero!" icono="bi-chat">
					{#each chat as m (m.id)}
						<div class="burbuja" class:mia={m.remitente_id === yo()}>
							{#if m.remitente_id !== yo()}
								<div class="fw-semibold small">{m.remitente_nombre} <span class="badge text-bg-light">{ROLES[m.remitente_rol]}</span></div>
							{/if}
							<div style="white-space: pre-line">{m.contenido}</div>
							<div class="meta text-end">{fechaHora(m.fecha_envio)}</div>
						</div>
					{/each}
				</Cargando>
			</div>
			<form class="d-flex gap-2 mt-3" onsubmit={enviarCurso}>
				<input class="form-control" placeholder="Escribe un mensaje para el curso..." bind:value={textoCurso} maxlength="2000" />
				<button class="btn btn-primary px-4" disabled={!textoCurso.trim()} aria-label="Enviar"><i class="bi bi-send"></i></button>
			</form>
		{/if}
	</div>
{:else}
	<div class="row g-3">
		<div class="col-lg-4">
			<div class="tarjeta p-2" style="max-height: 560px; overflow-y: auto">
				{#each bandeja as b (b.contraparte_id)}
					<button class="item-conversacion" class:activa={contraparte?.id === b.contraparte_id}
						onclick={() => abrirConversacion({ id: b.contraparte_id, nombre: b.contraparte_nombre, rol: b.contraparte_rol })}>
						<span class="avatar flex-shrink-0">{iniciales(b.contraparte_nombre)}</span>
						<span class="flex-grow-1 min-w-0">
							<span class="d-flex justify-content-between">
								<span class="fw-semibold text-truncate">{b.contraparte_nombre}</span>
								<span class="small text-muted ms-2 text-nowrap">{haceCuanto(b.fecha_envio)}</span>
							</span>
							<span class="d-flex justify-content-between">
								<span class="small text-muted text-truncate">{b.ultimo_mensaje}</span>
								{#if b.no_leidos > 0}<span class="badge rounded-pill bg-primary ms-2">{b.no_leidos}</span>{/if}
							</span>
						</span>
					</button>
				{:else}
					<div class="text-center text-muted small py-5 px-3">No tienes conversaciones. Usa <strong>Nuevo mensaje directo</strong>.</div>
				{/each}
			</div>
		</div>
		<div class="col-lg-8">
			<div class="tarjeta tarjeta-cuerpo">
				{#if contraparte}
					<div class="d-flex align-items-center gap-2 mb-3">
						<span class="avatar">{iniciales(contraparte.nombre)}</span>
						<div><div class="fw-semibold">{contraparte.nombre}</div><div class="small text-muted">{ROLES[contraparte.rol] ?? ''}</div></div>
					</div>
					<div class="chat-caja" bind:this={cajaDirecto}>
						{#each conversacion as m (m.id)}
							<div class="burbuja" class:mia={m.remitente_id === yo()}>
								<div style="white-space: pre-line">{m.contenido}</div>
								<div class="meta text-end">
									{fechaHora(m.fecha_envio)}
									{#if m.remitente_id === yo()}<i class="bi {m.leido ? 'bi-check2-all text-primary' : 'bi-check2'} ms-1"></i>{/if}
								</div>
							</div>
						{:else}
							<div class="text-center text-muted my-auto">Inicia la conversación con {contraparte.nombre}.</div>
						{/each}
					</div>
					<form class="d-flex gap-2 mt-3" onsubmit={enviarDirecto}>
						<input class="form-control" placeholder="Escribe tu mensaje..." bind:value={textoDirecto} maxlength="2000" />
						<button class="btn btn-primary px-4" disabled={!textoDirecto.trim()} aria-label="Enviar"><i class="bi bi-send"></i></button>
					</form>
				{:else}
					<div class="text-center text-muted py-5">
						<i class="bi bi-chat-square-text d-block mb-2" style="font-size: 2.5rem; opacity: .5"></i>
						Selecciona una conversación o inicia una nueva.
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}

<Modal bind:abierto={modalNuevo} variante="crear" titulo="Nuevo mensaje directo">
	<SelectorLista bind:valor={nuevoContacto} url="/catalogos/contactos" etiqueta="¿A quién quieres escribir?"
		placeholder="Busca a la persona" alCambiar={(_, o) => (infoContacto = o)} />
	<p class="small text-muted mt-2 mb-0">
		{sesion.usuario?.rol === 'acudiente' ? 'Puedes escribir a los docentes y a coordinación.' : 'Puedes escribir a cualquier usuario activo de la plataforma.'}
	</p>
	{#snippet pie()}
		<button class="btn btn-light" onclick={() => (modalNuevo = false)}>Cancelar</button>
		<button class="btn btn-success" disabled={!nuevoContacto} onclick={iniciarNueva}>Abrir conversación</button>
	{/snippet}
</Modal>
