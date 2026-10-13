import adapter from '@sveltejs/adapter-static';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	kit: {
		// Aplicación de una sola página (SPA): se publica como archivos estáticos en Vercel/Netlify.
		adapter: adapter({ fallback: 'index.html' })
	}
};

export default config;
