<script>
	import 'bootstrap/dist/css/bootstrap.min.css';
	import 'bootstrap-icons/font/bootstrap-icons.min.css';
	import '../app.css';
	import { onMount } from 'svelte';
	import { Capacitor } from '@capacitor/core';
	import { cargarSesion } from '$lib/sesion.svelte.js';

	let { children } = $props();
	cargarSesion();

	// En la app móvil: barra de estado con el azul institucional y texto claro
	onMount(async () => {
		if (!Capacitor.isNativePlatform()) return;
		try {
			const { StatusBar, Style } = await import('@capacitor/status-bar');
			await StatusBar.setStyle({ style: Style.Dark });
			await StatusBar.setBackgroundColor({ color: '#123b6d' });
		} catch {
			/* algunas versiones de Android no permiten cambiar el color: no es un error */
		}
	});
</script>

{@render children()}
