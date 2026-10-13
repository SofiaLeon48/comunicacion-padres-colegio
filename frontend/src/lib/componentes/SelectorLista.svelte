<!--
  Lista desplegable que se llena desde la API (/catalogos/...).
  El usuario ve NOMBRES; el componente guarda el id seleccionado sin mostrarlo.
-->
<script>
	import { api } from '$lib/api.js';

	let {
		valor = $bindable(null),
		url,
		etiqueta = '',
		placeholder = 'Selecciona una opción',
		opcionVacia = null,
		requerido = false,
		deshabilitado = false,
		id = 'sel-' + Math.random().toString(36).slice(2, 8),
		alCambiar = () => {}
	} = $props();

	let opciones = $state([]);
	let cargando = $state(false);

	$effect(() => {
		const u = url;
		if (!u) {
			opciones = [];
			return;
		}
		cargando = true;
		api.get(u)
			.then((r) => (opciones = r))
			.catch(() => (opciones = []))
			.finally(() => (cargando = false));
	});

	const texto = $derived(valor === null || valor === undefined ? '' : String(valor));

	function cambiar(e) {
		const v = e.target.value;
		valor = v === '' ? null : Number(v);
		alCambiar(valor, opciones.find((o) => o.id === valor));
	}
</script>

{#if etiqueta}<label class="form-label" for={id}>{etiqueta}{#if requerido}<span class="text-danger"> *</span>{/if}</label>{/if}
<select {id} class="form-select" value={texto} onchange={cambiar} required={requerido} disabled={deshabilitado || cargando}>
	{#if opcionVacia}
		<option value="">{opcionVacia}</option>
	{:else}
		<option value="" disabled>{cargando ? 'Cargando...' : placeholder}</option>
	{/if}
	{#each opciones as o (o.id)}
		<option value={String(o.id)}>{o.etiqueta ?? o.nombre}</option>
	{/each}
</select>
