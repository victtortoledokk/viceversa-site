"""
VICEVERSA — leitor dos posts do X (sem API paga)
=================================================
Tenta ler os posts públicos de @vvviceversaa pelos mesmos endpoints que um
navegador deslogado usa para renderizar tweets embutidos. Não usa a API oficial
(que cobra por leitura) nem chave nenhuma.

IMPORTANTE — isto é melhor-esforço, não garantia:

  * São endpoints internos do X, sem contrato público. Podem mudar ou fechar
    sem aviso. Um deles vem sendo estrangulado desde ~2024.
  * O X costuma bloquear requisições vindas de IPs de datacenter, e o GitHub
    Actions roda em datacenter. Pode simplesmente não responder.
  * Acessar endpoints internos por script é zona cinzenta nos termos do X.

Por isso o script NUNCA derruba o site: se todas as rotas falharem, ele registra
o motivo, não mexe em nada e sai com código 0. As Issues continuam sendo a fonte
confiável; o X entra como complemento quando funciona.

Uso: chamado pelo workflow, depois de posts.py (que monta o feed das Issues).
Este script MESCLA os posts do X ao que já existe, sem duplicar.
"""

import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).parent
REPO = RAIZ.parent
ARQ_FEED = REPO / "feed.json"

PERFIL = "vvviceversaa"
MAX_FEED = 30
MAX_DO_X = 10          # quantos posts do X considerar por rodada

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


def log(msg):
    print(f"[viceversa-x] {msg}", flush=True)


def pegar(url, timeout=20):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


# ----------------------------------------------------------------------
# Rotas de leitura, da mais simples para a mais frágil
# ----------------------------------------------------------------------
def rota_syndication_cdn():
    """Endpoint de sindicação do embed. Sem autenticação."""
    url = (f"https://cdn.syndication.twimg.com/timeline/profile"
           f"?screen_name={PERFIL}&dnt=true&with_replies=false")
    bruto = pegar(url)
    dados = json.loads(bruto)
    # o corpo vem como HTML com um blob __INITIAL_STATE__ embutido
    html = dados.get("body", "") if isinstance(dados, dict) else ""
    m = re.search(r"__INITIAL_STATE__\s*=\s*(\{.*?\});", html, re.S)
    if not m:
        raise ValueError("blob __INITIAL_STATE__ não encontrado")
    estado = json.loads(m.group(1))
    tweets = (estado.get("entities", {}) or {}).get("tweets", {}) or {}
    saida = []
    for tid, t in tweets.items():
        texto = t.get("full_text") or t.get("text") or ""
        if texto:
            saida.append({"id": str(tid), "texto": texto,
                          "criado": t.get("created_at", "")})
    return saida


def rota_syndication_alt():
    """Variante do mesmo serviço, em outro domínio."""
    url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{PERFIL}"
    html = pegar(url)
    m = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(\{.*?\})</script>', html, re.S)
    if not m:
        raise ValueError("__NEXT_DATA__ não encontrado")
    dados = json.loads(m.group(1))
    entradas = (dados.get("props", {}).get("pageProps", {})
                .get("timeline", {}).get("entries", []) or [])
    saida = []
    for e in entradas:
        t = (e.get("content", {}) or {}).get("tweet", {}) or {}
        texto = t.get("full_text") or t.get("text") or ""
        tid = t.get("id_str") or e.get("entry_id", "")
        if texto and tid:
            saida.append({"id": str(tid), "texto": texto,
                          "criado": t.get("created_at", "")})
    return saida


ROTAS = [
    ("syndication cdn", rota_syndication_cdn),
    ("syndication alt", rota_syndication_alt),
]


def ler_posts_do_x():
    for nome, rota in ROTAS:
        try:
            posts = rota()
            if posts:
                log(f"rota '{nome}': {len(posts)} post(s).")
                return posts
            log(f"rota '{nome}': respondeu, mas sem posts.")
        except urllib.error.HTTPError as e:
            log(f"rota '{nome}' falhou: HTTP {e.code}")
        except Exception as e:
            log(f"rota '{nome}' falhou: {type(e).__name__} {e}")
    return []


# ----------------------------------------------------------------------
def formatar_data(bruto):
    for fmt in ("%a %b %d %H:%M:%S %z %Y", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            d = datetime.strptime(bruto, fmt)
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            return d.strftime("%d/%m/%Y %H:%M UTC")
        except (ValueError, TypeError):
            continue
    return datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")


def limpar(texto):
    """Tira o link encurtado que o X anexa no fim e espaços sobrando."""
    texto = re.sub(r"\s*https://t\.co/\w+\s*$", "", texto).strip()
    return re.sub(r"\s+", " ", texto)


def main():
    posts = ler_posts_do_x()
    if not posts:
        log("nenhuma rota funcionou — o feed das Issues fica como está. "
            "Isso é esperado: são endpoints não oficiais e instáveis.")
        return 0

    feed = []
    if ARQ_FEED.exists():
        try:
            feed = json.loads(ARQ_FEED.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            feed = []

    ja_tem = {item.get("link", "") for item in feed}
    novos = []
    for p in posts[:MAX_DO_X]:
        link = f"https://x.com/{PERFIL}/status/{p['id']}"
        if link in ja_tem:
            continue
        texto = limpar(p["texto"])
        if not texto:
            continue
        novos.append({
            "data": formatar_data(p.get("criado", "")),
            "titulo": (texto[:76] + "…") if len(texto) > 78 else texto,
            "texto": texto,
            "link": link,
        })

    if not novos:
        log("nada novo no X.")
        return 0

    combinado = novos + feed
    ARQ_FEED.write_text(
        json.dumps(combinado[:MAX_FEED], ensure_ascii=False, indent=2),
        encoding="utf-8")
    log(f"feed.json atualizado (+{len(novos)} do X).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
