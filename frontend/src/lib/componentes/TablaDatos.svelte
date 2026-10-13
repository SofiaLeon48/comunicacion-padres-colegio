<!--
  Tabla reutilizable con la librería DataTables (buscar, ordenar, paginar, responsive).
  columnas: [{ titulo, campo, render?(valor, fila) => html, orden?(fila), clase?, ordenable? }]
  acciones: [{ icono, titulo, color, accion(fila), visible?(fila) }]
  Los ID nunca se muestran: solo se usan internamente para las acciones.
-->
<script>
	import { onDestroy, onMount } from 'svelte';
	import { cargarDataTables, IDIOMA_ES } from '$lib/datatables.js';
	import { esc } from '$lib/formato.js';

	let { columnas, datos = [], acciones = [], porPagina = 10, ordenInicial = null, compacta = false } = $props();

	let tablaEl;
	let dt = null;

	function construirColumnas() {
		const cols = columnas.map((c) => ({
			title: c.titulo,
			data: null,
			orderable: c.ordenable !== false,
			className: c.clase ?? '',
			render: (_, tipo, fila) => {
				const valor = c.campo ? fila[c.campo] : null;
				if (tipo === 'sort' || tipo === 'type') return c.orden ? c.orden(fila) : (valor ?? '');
				return c.render ? c.render(valor, fila) : esc(valor ?? '—');
			}
		}));
		if (acciones.length) {
			cols.push({
				title: 'Acciones',
				data: null,
				orderable: false,
				searchable: false,
				className: 'text-end text-nowrap all',
				render: (_, tipo, fila, meta) =>
					acciones
						.map((a, i) =>
							!a.visible || a.visible(fila)
								? `<button type="button" class="btn btn-sm btn-${a.color ?? 'primary'} ms-1 btn-accion"
									data-accion="${i}" data-fila="${meta.row}" title="${esc(a.titulo)}" aria-label="${esc(a.titulo)}">
									<i class="bi ${a.icono}"></i></button>`
								: ''
						)
						.join('')
			});
		}
		return cols;
	}

	function alHacerClick(e) {
		const boton = e.target.closest('button[data-accion]');
		if (!boton || !dt) return;
		const fila = dt.row(Number(boton.dataset.fila)).data();
		acciones[Number(boton.dataset.accion)]?.accion(fila);
	}

	onMount(async () => {
		const DataTable = await cargarDataTables();
		if (!tablaEl) return;
		dt = new DataTable(tablaEl, {
			data: $state.snapshot(datos),
			columns: construirColumnas(),
			language: IDIOMA_ES,
			responsive: true,
			pageLength: porPagina,
			lengthMenu: [5, 10, 25, 50],
			order: ordenInicial ?? [],
			autoWidth: false
		});
		tablaEl.addEventListener('click', alHacerClick);
	});

	$effect(() => {
		const nuevos = $state.snapshot(datos);
		if (dt) {
			dt.clear();
			dt.rows.add(nuevos);
			dt.draw(false);
		}
	});

	onDestroy(() => {
		dt?.destroy();
		dt = null;
	});
</script>

<div class="tabla-datos" class:compacta>
	<table bind:this={tablaEl} class="table table-hover align-middle w-100"></table>
</div>
