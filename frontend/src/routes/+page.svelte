<script>
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { sesion } from '$lib/sesion.svelte.js';

	onMount(() => goto(sesion.token ? '/inicio' : '/login', { replaceState: true }));
</script>
