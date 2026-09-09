/* ═══════════════════════════════════════════════════════════
   RETROVERSO — CONFIGURAÇÃO DA CONTA / NUVEM
   ───────────────────────────────────────────────────────────
   Este é o ÚNICO arquivo que você precisa editar para ligar a
   sincronização na nuvem (Firebase).

   • Enquanto os campos estiverem em branco, o RetroVerso funciona
     em MODO LOCAL: o login existe, cria perfis no próprio
     navegador e separa o histórico por jogador — só não sincroniza
     entre dispositivos.
   • Preencha com os dados do seu projeto Firebase
     (Console → Configurações do projeto → Seus apps → Web)
     e o login por e-mail + a sincronização ligam sozinhos.

   Passo a passo completo: veja FIREBASE-SETUP.md
   ═══════════════════════════════════════════════════════════ */
window.RV_CONFIG = {

  /* ─── 1. Credenciais do Firebase (cole o objeto firebaseConfig) ─── */
  firebase: {
    apiKey:            '',
    authDomain:        '',
    projectId:         '',
    storageBucket:     '',
    messagingSenderId: '',
    appId:             ''
  },

  /* ─── 2. O que sincronizar ─── */
  sync: {
    // Histórico, favoritos, conquistas, estatísticas e nome do jogador.
    profile: true,
    // Save-states (o "Salvar" da barra de sistema dentro do jogo).
    saves: true,
    // Enviar o save para a nuvem automaticamente ao salvar no jogo.
    autoUploadSaves: true,
    // Ao abrir um jogo, buscar na nuvem um save mais novo que o local.
    autoDownloadSaves: true
  },

  /* ─── 3. Limites de segurança dos saves na nuvem ─── */
  // Saves são compactados (gzip) e gravados em pedaços no Firestore,
  // que é gratuito até 1 GiB. Save maior que isto fica só no aparelho.
  maxCloudSaveMB: 8,

  /* ─── 4. Versão do SDK do Firebase carregado via CDN ─── */
  firebaseSdkVersion: '10.12.5',

  /* ─── 5. Login obrigatório? ───
     true  = as páginas redirecionam para login.html quando não há sessão
     false = navegação livre; o login vira opcional */
  requireLogin: true
};
