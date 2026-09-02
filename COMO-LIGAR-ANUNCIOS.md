# Como ligar os anúncios

A estrutura já está no site: três espaços reservados (entre as manchetes e o mapa,
antes do plantão e antes do FAQ), com carregamento tardio e altura reservada.
**Enquanto o ID estiver vazio, os espaços ficam invisíveis** — o site fica limpo.

## Passo a passo (Google AdSense)

1. **Publique o site primeiro.** O AdSense só aprova domínios no ar com conteúdo real.
   Com o site vazio ou recém-criado, a resposta costuma ser "conteúdo de baixo valor".

2. **Crie a conta** em adsense.google.com, adicione seu domínio e aguarde a análise
   (de alguns dias a algumas semanas).

3. **Crie 3 blocos de anúncio** do tipo "display responsivo". Cada um gera um número
   de slot.

4. **Preencha as chaves** nos três arquivos `idiomas/*.json`:
   - `ad_cliente`: `ca-pub-XXXXXXXXXXXXXXXX` (seu ID de editor)
   - `ad_slot_a`, `ad_slot_b`, `ad_slot_c`: os números dos blocos criados

5. **Corrija o `ads.txt`** na raiz do site com o seu `pub-XXXXXXXXXXXXXXXX`.

6. Rode `python3 montar.py` e publique. Os anúncios aparecem nas três versões.

## Obrigatório: consentimento

Para tráfego da Europa e do Reino Unido, o Google exige uma CMP **certificada** —
um banner caseiro não serve e resulta em anúncios bloqueados. Use a CMP gratuita do
próprio Google: painel do AdSense → Privacidade e mensagens → Mensagem de consentimento
da UE. Ative antes de divulgar as versões em inglês e espanhol.

Para o Brasil, a LGPD pede aviso sobre cookies. A mesma ferramenta do Google cobre isso.

## Regras que derrubam contas

- **Nunca clique nos próprios anúncios**, nem peça para amigos clicarem. O Google detecta
  e banir é permanente.
- **Não coloque anúncio demais.** Três slots já é o limite saudável para esta página.
- **Rotule sempre** — o rótulo "Publicidade" já está implementado em cada slot.
- **Nada de conteúdo vazado.** Anúncio em página com material pirateado encerra a conta
  e ainda te expõe ao takedown da Take-Two.

## Se o AdSense recusar

Alternativas que aceitam sites menores: **Ezoic** (sem mínimo de tráfego, mas injeta mais
scripts e pesa mais) e **Adsterra** ou **PropellerAds** (aceitam quase todo mundo, pagam
melhor, mas os formatos são agressivos — pop-under, redirecionamento — e queimam a
confiança do leitor). Eu só usaria essas duas como último recurso.

Quando o site passar de ~50 mil sessões/mês, vale migrar para **Mediavine** ou
**Raptive**: os RPMs são de 2 a 5 vezes maiores que os do AdSense.
