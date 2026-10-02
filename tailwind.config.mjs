/** @type {import('tailwindcss').Config} */
// Estetica oscura de la web (`tars`: acento azul-500, `ink`: texto claro,
// tarjetas #181818) con la tipografia del dossier 2026-27: Poppins para el
// texto, Open Sans extrabold para titulos y Gruppo para los rotulos.
export default {
	content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
	theme: {
		extend: {
			colors: {
				tars: {
					DEFAULT: '#3b82f6', // acento (text-blue-500 de la antigua)
					900: '#1e3a8a',
					700: '#2563eb',
					500: '#60a5fa',
					200: '#3f3f46',     // bordes (zinc-700)
					100: '#27272a',     // separadores (zinc-800)
					50: '#181818',      // tarjetas
				},
				ink: '#f4f4f5',
			},
			fontFamily: {
				sans: ['Poppins', 'system-ui', 'sans-serif'],
				display: ['"Open Sans"', 'Poppins', 'system-ui', 'sans-serif'],
				wide: ['Gruppo', 'Poppins', 'system-ui', 'sans-serif'],
			},
		},
	},
	plugins: [],
}
