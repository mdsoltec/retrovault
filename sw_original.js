/* ═══════════════════════════════════════════════════════════
   RETROVERSE — Service Worker (v9)
   O que mudou nesta versão:
   1. EmulatorJS (CDN) agora é cacheado com stale-while-revalidate:
      a 2ª abertura de um jogo usa o núcleo WASM do cache (quase
      instantânea) e o cache é atualizado em background quando há rede.
   2. Warmup não-bloqueante na ativação: loader.js + emulator.min.js
      já entram em cache no 1º acesso, sem atrasar a ativação do SW.
   3. STATIC_ASSETS agora inclui js/audio.js, js/overlay-parser.js e
      calibrate.html (faltavam → offline quebrava o player).
   4. Versão fixada do EmulatorJS (4.2.3) no warmup — veja play.html.
   ═══════════════════════════════════════════════════════════ */
const CACHE_NAME = 'retroverse-v10';
const CACHE_EJS = CACHE_NAME + '-ejs'; // núcleos/framework do EmulatorJS
const EJS_CDN = 'https://cdn.emulatorjs.org/4.2.3/data/';

const STATIC_ASSETS = [
  'index.html',
  'games.html',
  'play.html',
  'profile.html',
  'retroflix.html',
  'calibrate.html',
  'css/style.css',
  'assets/rv-icon.png',
  'manifest.json',
  'js/audio.js',
  'js/overlay-parser.js',
  // Base de cheats dinâmica do EmulatorJS
  'cheats/cheats.json',
  'cheats/nes.json',
  'cheats/snes.json',
  'cheats/gba.json',
  'cheats/gbc.json',
  'cheats/gb.json',
  'cheats/n64.json',
  'cheats/pcsx_rearmed.json',
  'cheats/segaMD.json',
  'cheats/segaCD.json',
  'cheats/segaGG.json',
  'cheats/nds.json',
  'cheats/fbneo.json'
];

// Install — cache static assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

// Activate — clean old caches + warmup do framework EJS (não-bloqueante)
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME && k !== CACHE_EJS).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );

  // Warmup: já deixa o motor do emulador em cache no 1º acesso.
  // Fora do waitUntil para nunca atrasar a ativação (offline incluso).
  caches.open(CACHE_EJS).then(cache => {
    [EJS_CDN + 'loader.js', EJS_CDN + 'emulator.min.js'].forEach(url => {
      fetch(url)
        .then(res => { if (res.ok) cache.put(url, res); })
        .catch(() => {});
    });
  });
});

// Fetch — network first, fallback to cache
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  // Skip non-GET requests
  if (event.request.method !== 'GET') return;

  // EmulatorJS (núcleos WASM): stale-while-revalidate.
  // 1º acesso baixa do CDN e guarda; 2º acesso (e offline) sai do cache;
  // em background o cache é atualizado quando há rede. URLs versionadas
  // (4.2.3, futuras) viram entradas separadas — nunca mistura versões.
  if (url.origin === 'https://cdn.emulatorjs.org') {
    event.respondWith(
      caches.open(CACHE_EJS).then(async cache => {
        const cached = await cache.match(event.request);
        const network = fetch(event.request)
          .then(res => {
            if (res && res.ok) cache.put(event.request, res.clone());
            return res;
          })
          .catch(() => cached);
        return cached || network;
      })
    );
    return;
  }

  // Skip external CDN and ROM requests (too large to cache)
  if (url.hostname !== self.location.hostname) return;

  // Skip overlay images and covers (too many, too large)
  if (url.pathname.includes('/overlays/') || url.pathname.includes('/covers/')) return;

  event.respondWith(
    fetch(event.request)
      .then(response => {
        // Clone and cache successful responses
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});
