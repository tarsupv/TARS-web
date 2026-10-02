import { defineConfig } from 'astro/config';

import tailwind from '@astrojs/tailwind';

import partytown from '@astrojs/partytown';

// https://astro.build/config
export default defineConfig({
  integrations: [tailwind(), partytown()],
  // Paginas antiguas de patrocinadores unificadas en /partners: se redirigen para
  // no romper enlaces ya compartidos.
  redirects: {
    '/sponsors': '/partners#patrocinadores',
    '/partners/patrocinadores': '/partners#patrocinadores',
    '/partners/entidades': '/partners#entidades',
  },
  vite: {
    // Los modulos de three/examples resuelven su propio 'three' y Vite acababa
    // cargando dos copias (aviso "Multiple instances of Three.js").
    resolve: { dedupe: ['three'] },
  },
});
