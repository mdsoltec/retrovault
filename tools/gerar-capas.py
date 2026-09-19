#!/usr/bin/env python3
"""═══════════════════════════════════════════════════════════
RETROVERSO — Resolvedor automático de capas

Uso:
  python3 tools/gerar-capas.py            # gera js/covers-map.js
  python3 tools/gerar-capas.py --baixar   # também baixa as capas para covers/
  python3 tools/gerar-capas.py --tudo     # reprocessa também quem já tem capa local

O que faz:
  • Lê o catálogo (js/catalog.js — fonte única);
  • Para cada jogo SEM capa local em covers/<console>/, procura a capa
    na base libretro-thumbnails (Named_Boxarts → Named_Covers →
    Named_Titles), usando o índice completo de cada sistema e um
    casamento aproximado do nome (ignora região, revisão, pontuação);
  • Escreve js/covers-map.js com a URL EXATA de cada jogo resolvido.
    O navegador usa esse mapa direto (sem tentativa e erro), e o
    js/covers.js continua tentando variações caso o mapa não tenha
    o jogo (catálogo novo sem rodar o script).

Só depende da biblioteca padrão do Python 3.
═══════════════════════════════════════════════════════════"""
import concurrent.futures
import html as ihtml
import json
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PUBLIC = RAIZ / "public"          # raiz do site (Firebase Hosting)
PAGINAS = ["public/js/catalog.js"]
SAIDA = RAIZ / "public" / "js" / "covers-map.js"
BASE = "https://thumbnails.libretro.com"
TIPOS = ["Named_Boxarts", "Named_Covers", "Named_Titles"]

SISTEMAS = {
    "snes": "Nintendo - Super Nintendo Entertainment System",
    "nes": "Nintendo - Nintendo Entertainment System",
    "gb": "Nintendo - Game Boy",
    "gbc": "Nintendo - Game Boy Color",
    "gba": "Nintendo - Game Boy Advance",
    "n64": "Nintendo - Nintendo 64",
    "nds": "Nintendo - Nintendo DS",
    "sega": "Sega - Mega Drive - Genesis",
    "segacd": "Sega - Mega-CD - Sega CD",
    "gamegear": "Sega - Game Gear",
    "mastersystem": "Sega - Master System - Mark III",
    "atari2600": "Atari - 2600",
    "psx": "Sony - PlayStation",
    "arcade": "FBNeo - Arcade Games",
}

# Exceções manuais: jogo → URL da capa (usadas quando o nome do arquivo
# não existe na base, ex.: hacks, traduções ou títulos renomeados).
OVERRIDES = {
    "snes/Donkey Kong Classic.smc":
        BASE + "/Nintendo%20-%20Nintendo%20Entertainment%20System/Named_Boxarts/"
               "Donkey%20Kong%20%28World%29%20%28Rev%201%29.png",
    "mastersystem/Batman (USA, Europe, Brazil).sms":
        BASE + "/Sega%20-%20Master%20System%20-%20Mark%20III/Named_Boxarts/"
               "Batman%20Returns%20%28Europe%2C%20Brazil%29%20%28En%29.png",
}

RE_JOGO = re.compile(r"\{[^{}]*?file:\s*(?:\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*')[^{}]*\}")
RE_CAMPO = re.compile(r"""(\w+):\s*("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')""")


def desescapar(s):
    return s[1:-1].replace("\\'", "'").replace('\\"', '"').replace("\\\\", "\\")


def catalogo():
    """Extrai [(console, {file, remote, name, subtitle})] das páginas."""
    jogos = {}
    consola = None
    for pagina in PAGINAS:
        txt = (RAIZ / pagina).read_text(encoding="utf-8")
        # console atual = última chave `'xxx': [` vista antes do jogo
        for m in re.finditer(r"([a-z0-9]+):\s*\{\s*\n\s*name:|" + RE_JOGO.pattern, txt):
            if m.group(1):
                consola = m.group(1)
                continue
            campos = {k: desescapar(v) for k, v in RE_CAMPO.findall(m.group(0))}
            if "file" not in campos or consola not in SISTEMAS:
                continue
            campos["console"] = consola
            jogos[(consola, campos["file"])] = campos
    return list(jogos.values())


def normalizar(nome):
    """Chave de comparação: sem acento, sem região/tags, só alfanumérico."""
    nome = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    nome = re.sub(r"\.(png|zip|sfc|smc|nes|gba|gbc|md|bin|sms|iso|chd|nds|n64|z64)$", "", nome, flags=re.I)
    nome = re.sub(r"[\(\[][^\)\]]*[\)\]]", " ", nome)          # (USA), [!]
    nome = nome.replace("&", " and ").replace("_", " ")
    nome = re.sub(r"\b(the|a|an)\b", " ", nome, flags=re.I)
    nome = re.sub(r"[^a-z0-9]+", "", nome.lower())
    return nome


def titulo_principal(nome):
    """'Pitfall! - Pitfall Harry\'s Jungle Adventure (USA).png' → 'Pitfall!'"""
    nome = re.sub(r"\.png$", "", nome, flags=re.I)
    nome = re.sub(r"\s*[\(\[].*$", "", nome)      # corta região/tags
    nome = re.split(r"\s+-\s+|\s+~\s+", nome)[0]  # corta subtítulo
    return nome.strip()


def listar(sistema, tipo):
    url = f"{BASE}/{urllib.parse.quote(sistema)}/{tipo}/"
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            corpo = r.read().decode("utf-8", "replace")
    except Exception as e:
        print(f"  ! falha ao listar {sistema}/{tipo}: {e}")
        return {}
    nomes = re.findall(r'href="([^"]+\.png)"', corpo)
    indice = {}
    for n in nomes:
        nome = ihtml.unescape(urllib.parse.unquote(n))
        indice.setdefault(normalizar(nome), nome)
    return indice


def escolher(indices, jogo):
    """Procura o melhor arquivo remoto para o jogo, em ordem de tipo."""
    base = re.sub(r"\.[^.]+$", "", jogo["file"])
    nome_exibido = jogo.get("name", "")
    if jogo.get("subtitle"):
        nome_exibido += " - " + jogo["subtitle"]
    tentativas = [jogo.get("remote"), base, nome_exibido, jogo.get("name")]
    chaves = []
    for t in tentativas:
        if t:
            k = normalizar(t)
            if k and k not in chaves:
                chaves.append(k)

    for tipo in TIPOS:
        idx = indices.get(tipo, {})
        for k in chaves:
            if k in idx:
                return tipo, idx[k]
        # casamento pelo "título principal" (antes de " - " ou " (" )
        # Ex.: "Pitfall!" → "Pitfall! - Pitfall Harry's Jungle Adventure (USA)"
        # sem confundir com "Pitfall II - Lost Caverns".
        for k in chaves:
            if len(k) < 4:
                continue
            cands = [v for v in idx.values() if normalizar(titulo_principal(v)) == k]
            if cands:
                return tipo, sorted(cands, key=len)[0]
    return None, None


def main():
    baixar = "--baixar" in sys.argv
    tudo = "--tudo" in sys.argv   # reprocessa mesmo quem já tem capa local
    jogos = catalogo()
    print(f"Catálogo: {len(jogos)} jogos")

    pendentes = []
    for j in jogos:
        base = re.sub(r"\.[^.]+$", "", j["file"])
        local = RAIZ / "covers" / j["console"] / (base + ".png")
        if local.exists() and not tudo:
            continue
        pendentes.append(j)
    print(f"Sem capa local: {len(pendentes)}")

    sistemas_usados = sorted({j["console"] for j in pendentes})
    indices = {}
    total_list = len(sistemas_usados) * len(TIPOS)
    print(f"Baixando índices de {len(sistemas_usados)} sistemas ({total_list} listagens, pode levar alguns minutos)...")
    with concurrent.futures.ThreadPoolExecutor(8) as ex:
        futuros = {
            ex.submit(listar, SISTEMAS[c], t): (c, t)
            for c in sistemas_usados for t in TIPOS
        }
        for f in concurrent.futures.as_completed(futuros):
            c, t = futuros[f]
            idx = f.result()
            indices.setdefault(c, {})[t] = idx
            if idx:
                print(f"  ✓ {c}/{t}: {len(idx)} capas")

    mapa, faltando = {}, []
    for j in pendentes:
        chave = f"{j['console']}/{j['file']}"
        if chave in OVERRIDES:
            mapa[chave] = OVERRIDES[chave]
            continue
        tipo, arquivo = escolher(indices[j["console"]], j)
        if not arquivo:
            faltando.append(j)
            continue
        url = (f"{BASE}/{urllib.parse.quote(SISTEMAS[j['console']])}/"
               f"{tipo}/{urllib.parse.quote(arquivo)}")
        mapa[f"{j['console']}/{j['file']}"] = url

    cab = ("/* GERADO POR tools/gerar-capas.py — NÃO EDITE À MÃO.\n"
           "   Mapa de capas remotas (libretro-thumbnails) para os jogos\n"
           "   que não têm capa local em covers/. Usado por js/covers.js. */\n")
    SAIDA.write_text(cab + "window.RV_COVER_MAP = " +
                     json.dumps(mapa, ensure_ascii=False, indent=1, sort_keys=True) +
                     ";\n", encoding="utf-8")
    print(f"\nResolvidos: {len(mapa)} → {SAIDA.relative_to(RAIZ)}")
    if faltando:
        print(f"Sem capa em nenhuma fonte: {len(faltando)}")
        for j in faltando:
            print(f"  X {j['console']}/{j['file']}")

    if baixar:
        print("\nBaixando capas para covers/ ...")
        def puxar(item):
            chave, url = item
            consola, arq = chave.split("/", 1)
            destino = PUBLIC / "covers" / consola / (re.sub(r"\.[^.]+$", "", arq) + ".png")
            destino.parent.mkdir(parents=True, exist_ok=True)
            if destino.exists() and not tudo:
                return None
            try:
                with urllib.request.urlopen(url, timeout=60) as r:
                    destino.write_bytes(r.read())
                return destino
            except Exception as e:
                return f"erro {chave}: {e}"
        with concurrent.futures.ThreadPoolExecutor(8) as ex:
            for res in ex.map(puxar, mapa.items()):
                if isinstance(res, str):
                    print("  !", res)
        print("Download concluído.")


if __name__ == "__main__":
    main()
