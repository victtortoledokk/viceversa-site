"""
VICEVERSA — Robô de redação automática
=======================================
Fluxo: RSS de notícias -> IA escreve o post -> feed.json (site) -> post no X.

O site é a FONTE e o X é o espelho. Esse sentido é proposital:
- ESCREVER no X é permitido no plano gratuito da API (~500 posts/mês).
- LER posts do X exige plano pago (US$ 200/mês no Basic).
Como o robô é quem escreve nos dois lugares ao mesmo tempo, site e X
ficam sempre sincronizados sem pagar pela leitura. Além disso, o site
embute a timeline oficial do X, então até posts manuais aparecem lá.

Variáveis de ambiente necessárias (ver README.md):
  ANTHROPIC_API_KEY   — chave da API da Anthropic (IA que escreve os posts)
  X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET — credenciais do X
  PUBLICAR_NO_X=1     — se ausente, roda em modo ensaio (não posta no X)
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import feedparser

# ----------------------------------------------------------------------
# Configuração
# ----------------------------------------------------------------------
RAIZ = Path(__file__).parent
REPO = RAIZ.parent
ARQ_FEED = REPO / "feed.json"          # fonte; montar.py copia para docs/
ARQ_VISTOS = RAIZ / "vistos.json"      # links já processados (evita repetição)
MAX_POSTS_POR_RODADA = 2               # segura o ritmo p/ caber no plano grátis do X
MAX_FEED = 30                          # itens mantidos no feed.json

# Fontes de notícias (RSS). Adicione/remova à vontade.
FEEDS = [
    "https://www.gamespot.com/feeds/game-news/",
    "https://www.videogameschronicle.com/feed/",
    "https://feeds.ign.com/ign/games-all",
]

# Só interessa GTA VI:
PADRAO_GTA = re.compile(r"\bgta\s*(vi|6)\b|grand theft auto\s*(vi|6)", re.I)

# Idioma dos posts. O site tem o inglês como idioma principal, então o robô
# escreve em inglês por padrão. Troque para "português do Brasil" ou "espanhol"
# se quiser mudar a língua da conta.
IDIOMA = "English"

PROMPT_REDATOR = """Você é o redator do VICEVERSA, um portal de fãs sobre GTA VI, \
com tom jovem, direto e bem-humorado (mas sem inventar fatos).

A partir da manchete e do resumo abaixo, escreva em {idioma}:
1. Um título curto e chamativo (máx. 80 caracteres).
2. Um resumo de 2 frases para o site.
3. Um post para o X com no máximo 260 caracteres, incluindo 1-2 hashtags \
(ex.: #GTAVI, #GTA6) e SEM link.

Baseie-se APENAS nas informações fornecidas. Se a notícia for rumor, deixe claro \
que é rumor. Responda SOMENTE com JSON válido, sem markdown, no formato:
{"titulo": "...", "resumo": "...", "post_x": "..."}

Manchete: {manchete}
Resumo da fonte: {resumo}
"""


def log(msg: str) -> None:
    print(f"[viceversa-bot] {msg}", flush=True)


def carregar_json(caminho: Path, padrao):
    if caminho.exists():
        try:
            return json.loads(caminho.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            log(f"aviso: {caminho.name} corrompido, recomeçando.")
    return padrao


# ----------------------------------------------------------------------
# 1) Coleta: varre os RSS atrás de notícias novas de GTA VI
# ----------------------------------------------------------------------
def coletar_noticias(vistos: set) -> list[dict]:
    achados = []
    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
        except Exception as exc:  # rede fora do ar etc.
            log(f"falha ao ler {url}: {exc}")
            continue
        for item in feed.entries[:25]:
            link = item.get("link", "")
            titulo = item.get("title", "")
            resumo = re.sub(r"<[^>]+>", "", item.get("summary", ""))[:600]
            if not link or link in vistos:
                continue
            if PADRAO_GTA.search(titulo) or PADRAO_GTA.search(resumo):
                achados.append({"titulo": titulo, "resumo": resumo, "link": link})
    log(f"{len(achados)} notícia(s) nova(s) de GTA VI encontrada(s).")
    return achados


# ----------------------------------------------------------------------
# 2) Redação: a IA transforma a notícia em post do VICEVERSA
# ----------------------------------------------------------------------
def redigir_com_ia(noticia: dict) -> dict | None:
    import anthropic

    cliente = anthropic.Anthropic()  # usa ANTHROPIC_API_KEY do ambiente
    prompt = (PROMPT_REDATOR
              .replace("{idioma}", IDIOMA)
              .replace("{manchete}", noticia["titulo"])
              .replace("{resumo}", noticia["resumo"]))
    try:
        resposta = cliente.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        texto = resposta.content[0].text.strip()
        texto = re.sub(r"^```(json)?|```$", "", texto, flags=re.M).strip()
        dados = json.loads(texto)
        if not all(k in dados for k in ("titulo", "resumo", "post_x")):
            raise ValueError("JSON incompleto")
        dados["post_x"] = dados["post_x"][:270]
        return dados
    except Exception as exc:
        log(f"IA falhou nesta notícia ({exc}); pulando.")
        return None


# ----------------------------------------------------------------------
# 3) Publicação no X (plano gratuito permite escrever)
# ----------------------------------------------------------------------
def publicar_no_x(texto: str) -> str | None:
    if os.environ.get("PUBLICAR_NO_X") != "1":
        log("modo ensaio: post NÃO enviado ao X. -> " + texto)
        return None
    import tweepy

    cliente = tweepy.Client(
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_SECRET"],
    )
    resultado = cliente.create_tweet(text=texto)
    id_post = resultado.data["id"]
    log(f"publicado no X: id {id_post}")
    return f"https://x.com/vvviceversaa/status/{id_post}"


# ----------------------------------------------------------------------
# 4) Atualiza o feed.json que o site consome
# ----------------------------------------------------------------------
def atualizar_feed(novos: list[dict]) -> None:
    feed = carregar_json(ARQ_FEED, [])
    feed = novos + feed
    ARQ_FEED.write_text(
        json.dumps(feed[:MAX_FEED], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log(f"feed.json atualizado ({len(novos)} novo(s), {min(len(feed), MAX_FEED)} no total).")


# ----------------------------------------------------------------------
def main() -> int:
    vistos = set(carregar_json(ARQ_VISTOS, []))
    noticias = coletar_noticias(vistos)
    if not noticias:
        log("nada novo hoje. Até a próxima rodada.")
        return 0

    publicados = []
    for noticia in noticias[:MAX_POSTS_POR_RODADA]:
        post = redigir_com_ia(noticia)
        vistos.add(noticia["link"])
        if not post:
            continue
        link_x = publicar_no_x(post["post_x"])
        publicados.append(
            {
                "data": datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC"),
                "titulo": post["titulo"],
                "texto": post["resumo"],
                "link": link_x or noticia["link"],
            }
        )

    if publicados:
        atualizar_feed(publicados)
    ARQ_VISTOS.write_text(
        json.dumps(sorted(vistos)[-500:], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
