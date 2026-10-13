<script>
	import 'bootstrap/dist/css/bootstrap.min.css';
	import 'bootstrap-icons/font/bootstrap-icons.min.css';
	import '../app.css';
	import { cargarSesion } from '$lib/sesion.svelte.js';

	let { children } = $props();
	cargarSesion();
</script>

{@render children()}
