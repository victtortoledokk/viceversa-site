# Como publicar no painel de notícias

## Custo: zero

Nada aqui usa API paga. Não fala com o X (que cobra por leitura desde fevereiro
de 2026) nem com IA. Usa só a API do próprio GitHub, com o token que o Actions
fornece de graça, e GitHub Actions é gratuito e ilimitado em repositório público.

## Como publicar um post

1. No repositório, vá em **Issues → New issue**.
2. **Título da Issue** = título do card no site.
3. **Corpo da Issue** = texto do card.
4. Adicione o rótulo **`post`** (só Issues com esse rótulo viram publicação).
5. Clique em *Submit new issue*.

Em cerca de um minuto o card aparece no site, sem você mexer em arquivo nenhum.
Dá para fazer pelo celular, no app do GitHub.

### Apontar o card para o seu tweet

Inclua no corpo uma linha começando com `X:` e o link. Ela é removida do texto e
vira o link do card:

```
Rockstar finally showed the game running on a base PS5.

X: https://x.com/vvviceversaa/status/123456789
```

Sem essa linha, o card aponta para a própria Issue.

### Editar, tirar do ar, trazer de volta

- **Editar** a Issue atualiza o card automaticamente.
- **Fechar** a Issue tira o post do site.
- **Reabrir** traz de volta.

A ordem no site segue a data de criação da Issue, mais recente primeiro. Ficam os
30 posts mais novos.

## Os posts do X (automático, melhor-esforço)

O `automacao/ler-x.py` tenta ler os posts públicos de @vvviceversaa e mesclá-los
ao painel, sem chave e sem custo. Ele usa os mesmos endpoints de sindicação que
um navegador deslogado usa para renderizar tweets embutidos.

**Isso pode não funcionar, e você precisa saber disso:**

- São endpoints internos do X, sem contrato público. Podem mudar ou fechar sem
  aviso; um deles vem sendo estrangulado desde ~2024.
- O X costuma bloquear requisições vindas de IPs de datacenter, e o GitHub
  Actions roda em datacenter.
- Acessar endpoints internos por script é zona cinzenta nos termos do X.

Por isso o script **nunca derruba o site**: se todas as rotas falharem, ele
registra o motivo, não mexe em nada e sai normalmente. As Issues continuam sendo
a fonte confiável.

**Como saber se está funcionando:** aba Actions → última execução → passo
"Tentar ler os posts do X". Se aparecer `feed.json atualizado (+N do X)`,
funcionou. Se aparecer `nenhuma rota funcionou`, o X está bloqueando — use as
Issues normalmente.

Roda a cada 3 horas e a cada mexida em Issue.

## Por que não existe caminho oficial gratuito

- **API do X:** desde fevereiro de 2026 é cobrada por uso. O plano gratuito
  cobre publicação (1.500 posts/mês), mas não tem cota de leitura — não há
  caminho gratuito pela API oficial para ler tweets.
- **Timeline embutida:** o X passou a exibi-la apenas para quem está logado —
  visitantes sem conta viam um espaço vazio, por isso foi removida do site.
- **Pontes RSS gratuitas:** morreram junto com o Nitter.

Se o caminho não oficial parar de funcionar e você quiser algo garantido, a API
paga sai por poucos dólares por mês no seu volume. Aí é decisão sua.

## Rodar na mão

Aba **Actions** → *Publicar posts (Issues → site)* → **Run workflow**. Útil se
alguma execução falhar ou se você quiser forçar uma atualização.
