# VICEVERSA — Pacote de automação

Este pacote transforma o site em um portal que se atualiza sozinho. A arquitetura tem duas camadas, e é importante entender por que ela funciona nesse sentido:

## Como o site fica sincronizado com o X

**Camada 1 — Timeline embutida (já funciona, custo zero).** A seção "Plantão em tempo real" do site embute a timeline oficial do X de `@vvviceversaa`. Qualquer coisa postada no X — pelo robô ou por você manualmente — aparece no site automaticamente, porque quem busca os posts é o navegador do visitante, direto dos servidores do X. Não há nada para configurar além de ter o site no ar.

Limitação honesta: o embed do X às vezes é bloqueado por adblockers ou por configurações da própria plataforma. Por isso o site tem um fallback elegante (um botão levando ao perfil) e a Camada 2 abaixo, que não depende do X para exibir conteúdo.

**Camada 2 — Robô de redação com IA (`bot.py`).** A cada 6 horas, o GitHub Actions roda o robô, que: (1) varre feeds RSS de sites de games atrás de notícias de GTA VI; (2) usa a IA (Claude) para escrever título, resumo e um post curto em português, no tom do VICEVERSA; (3) publica o post no X; (4) grava o resumo no `feed.json`, que o site lê e exibe no painel "Resumo automático da redação". Site e X são atualizados no mesmo instante, pela mesma fonte.

**Por que o fluxo é site→X e não X→site?** A API do X cobra US$ 200/mês só para *ler* posts, mas permite *escrever* (~500 posts/mês) de graça. Então, em vez de o site "puxar" do X (caro), o robô escreve nos dois lugares ao mesmo tempo (grátis). O resultado para o visitante é idêntico — e a timeline embutida ainda cobre os posts que você fizer manualmente.

## Passo a passo de configuração

1. **Repositório.** Crie um repositório no GitHub e envie o `viceversa.html` (renomeie para `index.html`), o `feed.json`, o `bot.py`, o `requirements.txt` e a pasta `.github/`. Ative o GitHub Pages (Settings → Pages → branch main). Pronto: o site está no ar, com a timeline do X funcionando.

2. **Chave da IA.** Crie uma chave em https://console.anthropic.com e guarde-a.

3. **Credenciais do X.** Em https://developer.x.com, crie um app no plano Free, gere as quatro credenciais (API Key, API Secret, Access Token, Access Secret) e dê permissão de **Read and Write** ao app.

4. **Secrets.** No repositório: Settings → Secrets and variables → Actions → New repository secret. Cadastre: `ANTHROPIC_API_KEY`, `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_SECRET`.

5. **Teste em modo ensaio.** No arquivo `.github/workflows/plantao.yml`, troque `PUBLICAR_NO_X: "1"` por `"0"` e rode o workflow manualmente (aba Actions → Plantão VICEVERSA → Run workflow). O robô fará tudo, menos postar no X — você verá os posts gerados no log e no `feed.json`.

6. **Ligue de verdade.** Volte `PUBLICAR_NO_X` para `"1"`. A partir daí, a cada 6 horas o robô roda sozinho.

## Ajustes úteis

- **Fontes de notícia:** edite a lista `FEEDS` no `bot.py`.
- **Ritmo:** `MAX_POSTS_POR_RODADA = 2` mantém o robô dentro do limite gratuito do X com folga (2 posts × 4 rodadas/dia = ~240/mês). 
- **Tom dos posts:** edite o `PROMPT_REDATOR` no `bot.py` — é ali que mora a "personalidade" da redação.
- **Frequência:** mude o `cron` no workflow (`0 */6 * * *` = a cada 6h).

## Custos

- GitHub Actions + Pages: grátis para repositório público.
- X API (escrita): grátis.
- IA: centavos por rodada (cada post consome poucos milhares de tokens).

## Uma nota de responsabilidade

O robô só resume notícias que encontrou nos RSS — o prompt o instrui a não inventar fatos e a sinalizar rumores. Ainda assim, revise o feed de vez em quando: automação boa é automação supervisionada. O X também exige que contas automatizadas indiquem isso no perfil (rótulo de conta automatizada nas configurações).
