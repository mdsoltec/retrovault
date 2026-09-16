#!/usr/bin/env python3
"""═══════════════════════════════════════════════════════════
RETROVERSO — Gerador/verificador de fichas dos jogos

Uso:
  python3 tools/gerar-fichas.py check   # (padrão) relatório de cobertura
  python3 tools/gerar-fichas.py inject  # injeta <script> nos HTML (idempotente)

O que faz:
  • Lê o catálogo (campo `file:` das ROMs) do js/catalog.js (fonte única);
  • Confere se todo jogo tem ficha em js/fichas.js (chave = nome do arquivo);
  • Lista os jogos sem ficha e os marcados como c:1 (dados a conferir);
  • Com `inject`, adiciona <script src="js/fichas.js"> e
    <script src="js/ficha-modal.js"> antes de </body> nos dois arquivos,
    se ainda não estiverem lá (roda quantas vezes quiser).

Só depende da biblioteca padrão do Python 3.
═══════════════════════════════════════════════════════════"""
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PAGINAS = ["index.html", "games.html"]
SCAN = ["js/catalog.js"]
FICHA_JS = RAIZ / "js" / "fichas.js"
SCRIPT_FICHAS = '<script src="js/fichas.js"></script>'
SCRIPT_CARD = '<script src="js/card-info.js"></script>'

# Captura `file: "..."` ou `file: '...'` (com escapes \' e \")
RE_FILE = re.compile(r"""file:\s*("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')""")


def desescapar(s: str) -> str:
    corpo = s[1:-1]
    return corpo.replace("\\'", "'").replace('\\"', '"').replace("\\\\", "\\")


def extrair_bloco_catalogo(html: str, marcador: str) -> str:
    """Extrai o bloco do objeto catálogo (ex.: `const CATALOG = { ... }`)
    com balanceamento de chaves — ignora comentários, Gamepass etc."""
    ini = html.find(marcador)
    if ini < 0:
        return ""
    pos = ini + len(marcador)
    depth = 1  # já consumimos a chave de abertura "{"
    for j in range(pos, len(html)):
        if html[j] == "{":
            depth += 1
        elif html[j] == "}":
            depth -= 1
            if depth == 0:
                return html[ini:j + 1]
    return html[ini:]


def extrair_arquivos(html: str) -> list[str]:
    # conta apenas dentro do bloco do catálogo (busca global ou página do console)
    bloco = extrair_bloco_catalogo(html, "const CATALOG = {") or extrair_bloco_catalogo(html, "var CATALOG = {") or extrair_bloco_catalogo(html, "const catalog = {")
    if bloco:
        return [desescapar(m.group(1)) for m in RE_FILE.finditer(bloco)]
    return [desescapar(m.group(1)) for m in RE_FILE.finditer(html)]


def extrair_chaves_fichas(js: str) -> list[str]:
    # chaves no formato `"..." : {` ou `'...' : {` no início de linha
    pat = re.compile(r"""^\s*(["'])(.*?)\1\s*:\s*\{""", re.M)
    return [m.group(2) for m in pat.finditer(js)]


def injetar_script(html: str, tag: str) -> tuple[str, bool]:
    base = tag.split('src="')[1].split('"')[0]
    if tag in html or ('src="%s?' % base) in html:
        return html, False
    if "</body>" in html:
        return html.replace("</body>", "  " + tag + "\n</body>", 1), True
    return html + "\n" + tag, True


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd not in ("check", "inject"):
        print(f"uso: {sys.argv[0]} [check|inject]")
        return 1

    fichas = extrair_chaves_fichas(FICHA_JS.read_text(encoding="utf-8")) if FICHA_JS.exists() else []
    fichas_set = set(fichas)
    # conta só `c: 1` em linhas de entrada (ignora o cabeçalho do arquivo)
    marcados = 0
    if FICHA_JS.exists():
        for linha in FICHA_JS.read_text(encoding="utf-8").splitlines():
            if "ano:" in linha and re.search(r"c:\s*1", linha):
                marcados += 1

    print(f"== RetroVerso — gerador de fichas ({cmd}) ==")
    print(f"js/fichas.js: {len(fichas)} fichas" + (f"  ({marcados} marcadas c:1 para conferir)" if marcados else ""))
    print()

    sem_ficha = []
    for nome in SCAN:
        p = RAIZ / nome
        if not p.exists():
            print(f"[{nome}] (não encontrado — pulando)")
            continue
        html = p.read_text(encoding="utf-8")
        jogos = extrair_arquivos(html)
        faltando = sorted(set(jogos) - fichas_set)
        sem_ficha += faltando
        print(f"[{nome}] {len(jogos)} jogos catalogados | {len(faltando)} sem ficha")
        for j in faltando:
            print(f"   ✗  {j}")
        if cmd == "inject" and nome.endswith(".html"):
            novo, a1 = injetar_script(html, SCRIPT_FICHAS)
            novo, a2 = injetar_script(novo, SCRIPT_CARD)
            if a1 or a2:
                p.write_text(novo, encoding="utf-8")
                print(f"   ✓ scripts injetados ({'fichas' if a1 else ''}{' + ' if a1 and a2 else ''}{'card-info' if a2 else ''})")
            else:
                print("   = scripts já presentes")
        print()

    if sem_ficha:
        print(f"⚠  {len(sem_ficha)} jogo(s) sem ficha — adicione a chave no js/fichas.js")
        return 1
    print("✓ Cobertura 100%: todo jogo do catálogo tem ficha.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
