# RETROVAULT OS — Enter The Classics

> Plataforma de emulação retro que roda **100% no navegador**. Sem instalar nada:
> escolha o console, aperte START e jogue — no PC ou no celular.

**13 consoles · ~200 jogos · PWA instalável · funciona offline**

---

## O que é

RetroVault OS é um front-end estático (HTML/CSS/JS puro, sem framework) que usa o
**EmulatorJS 4.2.3** como motor de emulação. O catálogo, as fichas, as capas, os
perfis e as configurações vivem no próprio site; as ROMs ficam em um servidor
próprio (Cloudflare Worker) e são baixadas sob demanda, só quando o jogador abre
o jogo.

- **Sem login obrigatório** — o perfil nasce local (nome, avatar, favoritos,
  histórico) e fica no `localStorage`, isolado por uid (`rv:<uid>:chave`).
- **Login opcional** — ao entrar com conta, o histórico e os saves são
  sincronizados no Firestore, com regra de dono-only (`users/{uid}/...`).
- **Mobile de verdade** — navegação inferior única (Início · Jogar · Ajustes ·
  Perfil), controle virtual na tela com overlays por jogo e suporte a gamepad.

> ⚠️ **ROMs não são distribuídas aqui.** O repositório contém apenas o front-end,
> catálogo e ferramentas. O player consome um servidor de ROMs configurável e
> cada operador deve ter o direito de usar os arquivos que servir.

---

## Arquitetura

```
┌──────────────────────── Navegador ────────────────────────┐
│  public/  (site estático multi-página + service worker)   │
│    ├─ js/catalog.js   → fonte única da verdade (jogos)    │
│    ├─ EmulatorJS 4.2.3 (CDN, cacheado com stale-while-    │
│    │   revalidate pelo service worker)                    │
│    └─ localStorage  → perfis, saves locais, cache capas   │
└──────────┬─────────────────────────┬──────────────────────┘
           │                         │
   ROMs sob demanda            sync opcional (login)
   servidor do operador        Firebase Firestore
   (endereço no player)        users/{uid} · saves em partes gzip
           │
   Deploy: Firebase Hosting (firebase.json → public/)
```

---

## Recursos por tela

| Página | O que faz |
|---|---|
| `index.html` | Hero + consoles + busca global (tecla `/`), jogo surpresa, "continuar jogando", favoritos e novidades da versão |
| `games.html` | Grade de jogos do console selecionado, com fichas e filtros |
| `play.html` | Player EmulatorJS: saves locais, cheats, screenshots, fast-forward, overlays de toque e mini-menu próprio |
| `profile.html` | Nome/avatar, 7 estatísticas, conquistas, heatmap de tempo de jogo, mural de favoritos clicável e consoles jogados |
| `config.html` | Central de ajustes: idioma, volume, tela cheia, auto-start, controle virtual, consoles liberados sem PIN, conta/sincronização |

Destaques transversais:

- **Capas automáticas** (ver pipeline abaixo) e **PIN por console** para
  controle parental simples.
- **"O que há de novo"** abre 1× por perfil a cada versão (`VERSION` em
  `js/rv-extras.js`); bump de versão reabre para todos.
- **Áudio de interface** sintetizado (`js/audio.js`), sem arquivos de som.
- **Ícones 100% SVG inline** no traço do sistema (viewBox 24, stroke ~2,
  `currentColor`) — zero emoji, zero biblioteca de ícones.

---

## Estrutura

```
retroverso/
├── public/                  # site (raiz do hosting)
│   ├── index|games|play|profile|config|login|404 .html
│   ├── sw.js                # service worker (app + EJS + capas + ROMs offline)
│   ├── manifest.json        # PWA ("RetroVault OS")
│   ├── js/
│   │   ├── catalog.js       # catálogo: 13 consoles, jogos, cores (FONTE ÚNICA)
│   │   ├── covers.js        # pipeline de capas + cache
│   │   ├── covers-map.js    # mapa gerado (jogo → URL de capa que funciona)
│   │   ├── fichas.js        # fichas dos jogos (ano, gênero, descrição)
│   │   ├── card-info.js     # enriquecimento de cards
│   │   ├── rv-account.js    # perfis por uid, login e merge de dados
│   │   ├── rv-config.js     # configuração global (login, PIN…)
│   │   ├── rv-extras.js     # stats, conquistas, tempo de jogo, novidades
│   │   ├── rv-ui.js         # navegação inferior (ativo automático)
│   │   ├── rv-input-mode.js # toque × gamepad
│   │   ├── audio.js         # sons de UI (WebAudio)
│   │   └── overlay-parser.js# overlays de controle virtual por jogo
│   ├── covers/<console>/    # capas locais (geradas por tools/)
│   ├── cheats/*.json        # base de cheats do EmulatorJS, por núcleo
│   └── assets/              # ícones, avatares, imagens do sistema
├── tools/
│   ├── gerar-capas.py       # gera js/covers-map.js (e baixa capas com --baixar)
│   └── gerar-fichas.py      # verifica/injeta fichas nos HTML (check | inject)
├── firebase.json            # hosting (public/, cleanUrls, headers do sw.js)
├── firestore.rules          # users/{uid} e saves: só o dono lê/escreve
└── package.json             # dependência: firebase (CLI/deploy)
```

---

## Sistema de capas

Para cada jogo, o `RVCovers.attach()` tenta nesta ordem (a que funcionar fica
em cache, incl. as que falharam, para não repetir tentativa):

1. `covers/<console>/<rom>.png|jpg` (local, gerada por `tools/gerar-capas.py`)
2. URL exata do mapa `js/covers-map.js`
3. `thumbnails.libretro.com` → `Named_Boxarts` → `Named_Covers` → `Named_Titles`
4. Placeholder "RV" estilizado

O cache (`rv_cover_cache` no `localStorage`) torna a 2ª visita instantânea.

---

## Dados locais (namespace `rv:<uid>:`)

| Chave | Conteúdo |
|---|---|
| `rv_player_name` / `rv_avatar` | nome e avatar do jogador |
| `rv_favorites` / `rv_recent` | favoritos e últimos jogados (alimentam mural e "continuar") |
| `rv_played_games` / `rv_sessions` | jogos abertos e contador de sessões |
| `rv_screenshots` / `rv_achievements` | screenshots tiradas e conquistas |
| `rv_cover_cache` | cache do pipeline de capas |
| `rv_pin_*` / configs do emulador | PIN de consoles e preferências (idioma, volume…) |

Login ativo → tudo vira `rv:<uid>:chave` e espelha no Firestore (merge por
`rv-account.js` ao entrar). Sem login → uid local do aparelho.

---

## Como adicionar um jogo

1. **Catálogo**: adicione a ROM em `js/catalog.js` (nome no padrão **No-Intro**,
   igual ao arquivo no servidor de ROMs).
2. **Capa** (opcional): rode `python3 tools/gerar-capas.py --baixar` — sem capa
   local, o pipeline libretro resolve sozinho.
3. **Ficha** (opcional): `python3 tools/gerar-fichas.py check` reporta lacunas.
4. O console novo precisa da entrada em `catalog.js` (core EmulatorJS + cor) —
   grids, busca, mural e estatísticas se adaptam sozinhos.

---

## Rodar e testar localmente

```bash
python3 -m http.server 8080 --directory public
# http://localhost:8080
```
- **Teste sempre nos dois modos** — são layouts distintos:
  - Mobile: **390×844** (nave inferior presente nas 4 páginas, zero overflow horizontal)
  - Desktop: **1280×800** (navbar completa, nave inferior oculta)
- Checagem mínima: itens/ativo da nave, engrenagem e Voltar do topo conforme o
  modo, e nenhum erro de página no console.

## Deploy

```bash
npm install            # cliente Firebase
firebase deploy        # hosting (public/) + firestore.rules
```

`firebase.json` já envia `sw.js` com `no-cache` (mudança de versão pega na hora)
e HTML sem cache longo.

---

## Service worker e versionamento

- `sw.js` (v9): cache do app por arquivo (um recurso ausente **não derruba** o
  install), EmulatorJS com stale-while-revalidate e warmup não-bloqueante,
  capas em cache próprio e **ROMs que o jogador escolheu levar para o offline**.
- Publicou mudança de CSS/JS? Suba o `?v=` nos HTML **e** a lista
  `STATIC_ASSETS` do `sw.js`.
- Mudou algo relevante ao jogador? Suba `VERSION` em `js/rv-extras.js` — as
  novidades reabrem 1× por perfil e o botão "Novidades da versão" relê a nota.

## Créditos

- [EmulatorJS](https://emulatorjs.org) 4.2.3 — motor de emulação (CDN fixado)
- [libretro-thumbnails](https://github.com/libretro-thumbnails) — base comunitária de capas
- Firebase (Hosting + Firestore) — hospedagem e sync opcional
