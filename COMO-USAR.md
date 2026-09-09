# RetroVerso → Firebase: como usar estes arquivos

## 1. Estrutura final esperada

```
D:\retroverse\
├── firebase.json        ← copiar daqui
├── firestore.rules      ← copiar daqui (substitui o seu atual)
├── .gitignore           ← copiar daqui (mesclar com o seu se já tiver)
├── .git\
├── tools\
├── push_git.bat
└── public\              ← CRIAR e mover o site pra dentro
    ├── index.html
    ├── games.html
    ├── login.html
    ├── play.html
    ├── profile.html
    ├── manifest.json
    ├── sw.js
    ├── css\
    ├── js\
    ├── assets\
    ├── covers\
    ├── cheats\
    └── overlays\
```

> ⚠️ Se o seu `sw.js` lista `retroflix.html` e `calibrate.html` no cache,
> e esses arquivos existirem no projeto, mova eles pra `public/` também.
> (No seu print eles não aparecem — o SW atual já ignora arquivo faltante,
> então não quebra, mas o ideal é manter a lista sincronizada.)

## 2. Passo a passo

```powershell
# 1. Na pasta D:\retroverse, crie a pasta public e mova os arquivos do site
mkdir public
move index.html public\
move games.html public\
move login.html public\
move play.html public\
move profile.html public\
move manifest.json public\
move sw.js public\
move css public\
move js public\
move assets public\
move covers public\
move cheats public\
move overlays public\

# 2. Copie firebase.json, firestore.rules e .gitignore deste pacote para D:\retroverse\

# 3. Login + deploy (na raiz D:\retroverse)
firebase login
firebase use --add        # escolhe o projeto e cria o .firebaserc (local, não vai pro git)
firebase deploy
```

Deploy só do site (sem mexer nas rules):

```powershell
firebase deploy --only hosting
```

Deploy só das rules:

```powershell
firebase deploy --only firestore:rules
```

## 3. Por que o firebase.json está assim?

| Trecho | Motivo |
|---|---|
| `"public": "public"` | Só o site vai pro ar. `.git`, `tools/`, `.bat` ficam de fora |
| `sw.js` → `no-cache, no-store` | Service Worker **nunca** pode ficar com cache velho, senão o PWA não atualiza |
| `*.html` → `no-cache` | HTML sempre fresco, mas o SW ainda permite offline |
| `manifest.json`, `js/css`, `cheats` → 1h | Seus arquivos não têm hash no nome, então cache curto = atualização rápida |
| imagens, `covers`, `overlays` → 7 dias | São pesados e mudam pouco. O SW já evita cachear `covers/` e `overlays/`, então esse header do hosting é o que vale |
| `cleanUrls: true` | Permite acessar `/games` além de `/games.html` (os links antigos continuam funcionando) |
| Sem `rewrites` de SPA | Correto pro seu caso: você tem várias páginas reais, não um index único |

## 4. Checklist Firebase Console (não esqueça!)

1. **Authentication → Sign-in method** → ativar `E-mail/senha` e `Google` (se usar)
2. **Authentication → Settings → Domínios autorizados** → adicionar `seu-projeto.web.app` e `seu-projeto.firebaseapp.com`
3. **Firestore → Criar banco de dados** (modo produção) antes do primeiro `firebase deploy`
4. Preencher `public/js/rv-config.js` com o `firebaseConfig` do seu projeto
5. Testar em aba anônima: login → jogar → salvar → recarregar

## 5. Sobre quota (plano grátis Spark)

- Hosting: 10 GB de armazenamento + 10 GB/mês de transferência
- Se a pasta `covers/` for muito pesada (milhares de imagens), vale no futuro
  mover as capas pro **Cloud Storage** ou manter o carregamento remoto via
  `thumbnails.libretro.com` (que seu SW já cacheia). Por enquanto pode subir tudo.
