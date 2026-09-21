# CLAUDE.md — Contexto do Projeto Folheto Mobilidade

> Arquivo de contexto para sessões com Claude Code.
> Criado em 2026-09-17 — primeira sessão do projeto: repositório criado,
> motor herdado e adaptado do `folheto-ifem`, tema `mobilidade` com 11
> páginas implementadas, pipeline validado de ponta a ponta com dado de
> exemplo transcrito do briefing (não oficial). Nenhum dado real de
> Campinas ou Montes Claros ainda — coleta em andamento pela equipe.
>
> Atualizado em 2026-09-18 — reabertura da Decisão "sem plataforma web"
> (ver Decisão 4): back-office Django local (só listar/gerar/baixar PDF,
> sem edição de dado nenhuma — construído com formulário de edição
> primeiro, removido no mesmo dia a pedido do usuário) e site estático de
> distribuição (`docs/`, réplica do folheto-ifem) implementados e
> testados. **Chegaram os dados reais dos dois pilotos**
> (`data/mobilidade/campinas.json`, `montes_claros.json`, gerados por
> `tools/dados_tratados_para_json.py` a partir de `data/external/`) — os
> PDFs de Campinas e Montes Claros já saem com população, frota,
> mortalidade e internações reais, não mais só o exemplo de Fortaleza.
> Ver seção "Pendências", "Marco: dados reais dos dois pilotos chegaram".

---

## Visão Geral

**Folheto Mobilidade** é a **Ficha de Diagnóstico Preliminar de Segurança
Viária** da Frente Nacional de Prefeitas e Prefeitos: um folheto impresso
institucional, com dados comparativos de mortes e internações por sinistro
de trânsito, custo hospitalar e evolução da frota — voltado a **cidades
acima de 80 mil habitantes**. Os dois pilotos definidos são **Campinas/SP**
e **Montes Claros/MG**.

O núcleo continua sendo um gerador de PDF em Python (ReportLab) — sem banco
de dados de verdade para os dados de trânsito, que seguem em JSON. Em
2026-09-18 essa decisão foi parcialmente reaberta a pedido explícito do
usuário (ver Decisão 4): existe hoje um back-office Django **local**,
usado pela equipe da FNP só para listar municípios e gerar/baixar o PDF
(sem editar dado nenhum pela web), e um site estático de distribuição
pública nos moldes do folheto-ifem. Uma plataforma completa (dashboard
público, edição de dado pela web, múltiplos temas de mobilidade, etc.)
continua sendo fase futura — não antecipar esse trabalho maior sem pedido
explícito novo.

Público-alvo do documento: gestores municipais (prefeitos, secretários) —
mesma linguagem editorial e visual institucional dos demais folhetos FNP
(ver `DESIGN_SYSTEM.md`).

---

## Origem: herdado do `folheto-ifem`

O motor de geração (`python/core/`) e a identidade visual vieram de
[`dadosfnp/folheto-ifem`](https://github.com/dadosfnp/folheto-ifem) — o
gerador unificado de folhetos institucionais da FNP (usado hoje para o
folheto IFEM e COSIP). **O que foi trazido, adaptado e descartado:**

| Trazido sem mudança | Adaptado | Descartado |
|---|---|---|
| `components.py` (KPI, tabela, ranking, divisória, QR…) | `tokens.py` — página A4 em vez de 20×20cm quadrado | Todo dado/tema IFEM, COSIP, clima (`data/ifem/`, `data/cosip/`, `data/clima/`, `temas/ifem.py`, `temas/cosip.py`) |
| `fonts.py`, `asset_cache.py`, `base_folheto.py` | `paleta_ranking.py` — nova função `cor_por_percentil_invertido` (ver §Decisões) | `core/capa.py` e `core/ultima.py` — **não eram genéricos apesar de viverem em `core/`**: hardcoded a um PNG pré-composto específico do IFEM. Substituídos por `draw_capa_padrao` (novo, genérico) e reaproveitando `draw_qr_page` já existente para a última página |
| `tools/baixar_fontes.py`, `verificar_arte.py`, `verificar_texto.py` | `gerar.py` — carregamento de "companheiros" (`_*.json`) generalizado (o folheto-ifem hardcodeava os 3 nomes de arquivo do IFEM; agora é qualquer `_*.json` em `data/<tema>/`) | `tools/planilhas_para_json.py`, `adapta_para_json.py`, `sync_dados.py`, `recalcular_problema.py`, `gerar_sem_declaracao.py`, `regerar_capa.py` — pipeline de dados fiscais do Subfinanciados, sem relação com dados de trânsito |
| `assets/padroes/*.png` (alfabeto modular — genérico) | `components.py::draw_page_number` — removida a dependência hardcoded de `ifem_assets` (módulo que não existe aqui) | `docs/` inteiro do folheto-ifem (landing page, `PASSO_A_PASSO.md`, `COMO_ALTERAR_O_FOLHETO.md`) — conteúdo específico do pipeline Subfinanciados/AdaptaBrasil, será reescrito do zero quando este projeto tiver uma landing própria |

**Nova primitiva que o folheto-ifem não tinha:** `draw_line_chart` em
`components.py` — gráfico de linha multi-série sem dependência externa,
com suporte a hachurar uma faixa (usado para marcar o período da gestão do
prefeito atual no gráfico de internações). O folheto-ifem só tinha barra
empilhada (`draw_stacked_bar`); segurança viária é fundamentalmente sobre
séries históricas, então esse componente é central aqui.

---

## Decisões de arquitetura (registradas com o usuário em 2026-09-17)

Estas três perguntas foram feitas antes de escrever qualquer código, porque
mudavam a arquitetura de forma significativa:

### 1. Formato de página: A4, reaproveitando o motor como está

O motor do folheto-ifem usa página quadrada fixa (20×20cm, um PDF de várias
páginas empilhadas — não painéis dobrados). O briefing do projeto pede
formatos A3/A4 **com duas dobras físicas** (um folheto de verdade, dobrado).
São geometrias diferentes. **Decisão do usuário: reaproveitar o motor como
está** — só o `PAGE_SIZE` em `tokens.py` mudou para A4 retrato; as dobras
viram guia de corte/dobra na hora de imprimir, não painéis calculados pelo
gerador.

Validado tecnicamente antes de aplicar ao repo novo: troquei `PAGE_SIZE`
para A4 no clone do folheto-ifem e gerei um PDF real com o tema COSIP
existente (dado de exemplo `data/cosip/rio_de_janeiro.json`) — 8 páginas
saíram sem erro, em 595×842pt (A4 exato via `pypdf`). Confirma que
`CONTENT_W`, `STRIPE_W` e `MARGIN` são genéricos o bastante (só dependiam
de `PAGE_SIZE`, não de um valor hardcoded em outro lugar do núcleo).

**Pendente:** os componentes (KPI, tabela, gráfico) ainda não tiveram o
espaçamento recalibrado para aproveitar a altura maior da A4 — hoje sobra
respiro no fim de algumas páginas de conteúdo. Ajustar conforme o conteúdo
real (Campinas/Montes Claros) for entrando, não antes.

Se algum dia a decisão for revista para um layout de dobras de verdade
(painéis calculados dentro de uma folha física), isso é reabrir esta
decisão — sinalizar explicitamente antes de agir, não decidir sozinho.

### 2. Fonte de dados: arquivos JSON, sem banco (por agora)

Os dados de mortes já foram tratados em R pela equipe e podem, no futuro,
vir de um banco Postgres no Digital Ocean — mas **decisão do usuário: por
agora, sem banco**, alinhado com "focar só no folheto". Os JSONs de entrada
em `data/mobilidade/` são preenchidos/editados à mão (ou por um script de
ingestão ainda não escrito) — nenhuma leitura automática de banco existe
neste repo.

Quando os dados tratados em R chegarem (formato ainda não definido), o
próximo passo natural é um `tools/dados_tratados_para_json.py` (mesmo
padrão do `planilhas_para_json.py` do folheto-ifem) que lê o formato bruto
e escreve `data/mobilidade/<municipio>.json` batendo com `SCHEMA.md`. Não
escrever esse script antes de saber o formato real do dado — evitar
adivinhar um contrato de entrada que a equipe de dados não confirmou.

Se decidirmos migrar para banco depois, é uma decisão de arquitetura nova
— sinalizar antes de agir, mesmo que o padrão (Subfinanciados → JSON →
PDF) já exista como referência no folheto-ifem.

### 3. Repositórios: `brunofnp` (dev) + `dadosfnp` (produção/organização)

Mesmo padrão do Legislativo FNP: `origin` = `brunofnp/folheto-mobilidade`
(pessoal, dev), `production` = `dadosfnp/folheto-mobilidade` (organização).

**Nota para quem for criar o próximo repo institucional pela conta
`brunofnp`:** nesta sessão, o repositório `dadosfnp/folheto-mobilidade`
criado inicialmente pelo usuário era **privado**, e a conta `brunofnp` não
aparecia como colaboradora nele (nem a API do GitHub o enxergava — 404
direto, mesmo com escopo `repo`/`read:org` corretos e visibilidade normal
de todos os outros repositórios públicos do org). O usuário também não
conseguiu adicionar colaborador pela tela do GitHub (provável restrição de
política do org para quem não é admin), e `brunofnp` não tem permissão de
criar repositório novo em `dadosfnp` pela API
(`brunofnp cannot create a repository for dadosfnp`). Resolvido renomeando
o repositório privado antigo (liberando o nome) e criando um novo — dessa
vez a conta que criou o repo aparece com acesso automático. Se isso se
repetir num projeto futuro, o caminho mais rápido é este, não insistir em
convite de colaborador.

---

## Stack

| Camada | Tecnologia |
|---|---|
| Geração de PDF | Python 3.12+, ReportLab ≥4.0 |
| Imagens/QR | Pillow, `qrcode[pil]` |
| Dados (futuro) | pandas, openpyxl — hoje sem uso real, mantidos do `requirements.txt` herdado para quando a ingestão de planilhas/R existir |
| Dados (hoje) | JSON versionado à mão em `data/mobilidade/` |
| Tipografia | Barlow Condensed + Inter (fallback Helvetica se ausentes) |

---

## Estrutura de Arquivos

Ver `README.md` — não duplicar aqui; manter as duas em sincronia se a
estrutura mudar.

---

## Modelo de dados

Contrato completo em `data/mobilidade/SCHEMA.md`. Resumo do que já tem
página implementada: `frota` (evolução % + valores atuais), `mortalidade_2024`
(taxa por 100 mil hab., 4 modos × 6 bases de comparação), `mortes_serie_historica`,
`internacoes_2025`, `internacoes_serie_historica` (com janela de gestão do
prefeito atual), `ranking_causas_morte`, `leitos_uti_hipotetico` (hoje é
texto livre com a pergunta orientadora do projeto, não um número calculado).

**Regra de ouro herdada do folheto-ifem, ainda mais importante aqui:** dado
externo em JSON, nunca hardcoded no código Python. E mais uma, específica
deste projeto: **nunca preencher um campo com um número estimado/lido a
olho de um gráfico como se fosse dado oficial.** O arquivo de exemplo
(`exemplo_fortaleza.json`) documenta isso explicitamente campo a campo —
onde o briefing do projeto não deu o valor por extenso, o campo ficou
`null`, mesmo quando um valor "plausível" seria fácil de inventar.

---

## Git — Remotos e fluxo

| Remoto | URL | Uso |
|---|---|---|
| `origin` | `https://github.com/brunofnp/folheto-mobilidade.git` | Repositório pessoal — desenvolvimento |
| `production` | `https://github.com/dadosfnp/folheto-mobilidade.git` | Repositório da organização |

Sem branches `next`/`main` separadas por enquanto (não há deploy nem
usuário final navegando um site — só geração local de PDF). Revisar essa
decisão se o projeto ganhar uma landing page de distribuição (mesmo padrão
do folheto-ifem, `docs/index.html` + GitHub Pages) — não introduzir isso
sem necessidade real.

### 4. Plataforma web: back-office Django local + site estático de distribuição (reabre a Decisão original)

Em 2026-09-18, a pedido explícito do usuário ("vamos fazer com que seja uma
plataforma web"), a decisão original deste documento ("não é uma plataforma
web... não antecipar sem pedido explícito") foi parcialmente revista. O
modelo concreto usado foi o próprio `dadosfnp/folheto-ifem` — mostrado ao
usuário depois que ficou claro que nada parecido existia neste repo ainda
— que tem duas partes bem separadas:

1. **Implementado, depois reduzido a propósito (2026-09-18, mesmo dia — a
   pedido explícito do usuário: "os dados não podem ser editáveis... o
   botão tem que ser somente para download")**: um back-office Django
   (`manage.py runserver`, app em `web/municipios/`) — ferramenta
   **interna, local, e só de leitura**, nunca exposta publicamente. Lista
   os municípios de `data/mobilidade/*.json` e deixa gerar/baixar o PDF com
   um clique — **sem nenhum formulário de edição**. A primeira versão desta
   sessão tinha um formulário Django de ~112 campos
   (`MunicipioForm`/`NovoMunicipioForm`, gravação atômica, etc.) — foi
   construído, testado e depois **removido por completo** a pedido do
   usuário; não existe mais `forms.py`, `tabelas.py`, `editar.html`,
   `novo.html` nem `tools/verificar_roundtrip_form.py` neste repo. **Dado
   só muda por `tools/dados_tratados_para_json.py` (a partir de
   `data/external/`) ou edição direta do arquivo** — nunca pela tela. **Sem
   banco de dados** (`DATABASES = {}` em `web/settings.py` — testado,
   funciona: o Django cai no backend `dummy` e não exige migração). O motor
   de geração de PDF (`python/core/`, `python/temas/mobilidade.py`) não foi
   tocado — o back-office só chama `gerar_um()`, o mesmo ponto de entrada
   do CLI.
2. **Implementado**: um site estático de distribuição pública
   (`docs/index.html` + GitHub Pages + PDFs hospedados em GitHub Release),
   réplica adaptada de `docs/` do folheto-ifem — sem Django, sem servidor,
   sem banco. `tools/build_site.py` gera `docs/folhetos.json` a partir de
   `data/mobilidade/*.json`, **excluindo sempre `exemplo_fortaleza.json`**
   (nunca dado publicável) e qualquer município sem PDF em `output/`.
   `tools/publicar_release.ps1` sobe os PDFs como assets de uma GitHub
   Release no repo `production` (`dadosfnp/folheto-mobilidade`, nunca no
   fork pessoal). O índice já mostra os 2 pilotos reais (ver "Marco: dados
   reais" nas Pendências) — falta só publicar a Release de verdade no
   GitHub pra a URL do "Baixar PDF" resolver. **Passo manual pendente, fora
   do alcance de código**: habilitar GitHub Pages em
   `dadosfnp/folheto-mobilidade` (Settings → Pages → branch `main`, pasta
   `/docs`) antes do primeiro merge para lá ter efeito público.

**Identidade visual (2026-09-18, a pedido explícito do usuário):** as duas
telas — `docs/index.html` (site público) e o back-office Django
(`web/municipios/templates/`) — usam o mesmo padrão visual do
`folheto-ifem` (Tailwind via CDN, mesma paleta espelhada de
`python/core/tokens.py`, mesmo componente de card com busca/filtro/
ordenação). `docs/index.html` ganhou a seção "Como é o folheto" com prévias
reais de página, geradas por `tools/gerar_preview_landing.py`
(`docs/preview/pagina-N.jpg`, via PyMuPDF — recorte quadrado do topo da
página A4, não do IFEM que é quadrado 20×20cm nativo). Só o padrão
visual/de componente foi copiado — não a estrutura de página do folheto
IFEM em si (que tem seções sem equivalente em dado de segurança viária,
como "Risco Climático" via AdaptaBrasil ou o mapa nacional de municípios;
ver `SCHEMA.md` — nunca inventar seção sem dado real por trás).

Isto não é uma decisão de reabrir a "plataforma completa de mobilidade"
mencionada na Visão Geral (dashboard público, múltiplos municípios geridos
por várias pessoas simultaneamente, etc.) — continua sendo fase futura,
fora de escopo sem pedido novo.

### 5. Estrutura do PDF: copiar o padrão visual do IFEM, teto de 5 páginas (2026-09-21)

O usuário pediu explicitamente para copiar a **estrutura geral, estilo de
capa e densidade visual** do folheto-ifem para o PDF de mobilidade ("o pdf
que estamos gerando não tem nenhuma identidade e o folheto do ifem é o
modelo geral... a estrutura, estilo de capa, tudo tirando o conteúdo deve
ser igual ao do IFEM"). Confirmado via pergunta direta ao usuário: **só o
padrão visual/de layout**, não uma cópia de conteúdo — nenhuma seção do
IFEM sem equivalente real em dado de segurança viária (Risco Climático via
AdaptaBrasil, mapa nacional) foi trazida.

Em seguida o usuário fixou um teto rígido: **no máximo 5 páginas** (a
estrutura antiga tinha 11, incluindo 2 divisórias que eram só título de
capítulo sem conteúdo). Consolidação aprovada explicitamente pelo usuário
("cortar as divisórias, fundir por tema"): as divisórias foram eliminadas
(cabeçalho de seção passou a viver dentro da própria página de conteúdo) e
os pares tabela+gráfico que eram páginas separadas foram fundidos em uma
só. Estrutura nova documentada em `DESIGN_SYSTEM.md` §6.

4 componentes genéricos novos entraram em `core/components.py` para
sustentar a densidade do padrão IFEM sem violar a regra de núcleo-nunca-
conhece-tema (ver Diretrizes de Engenharia): `draw_ranking_stat_grande`
(selo de posição), `draw_percentual_bar` (barra vermelho→verde),
`draw_donut_chart` (rosca com legenda) e `draw_qr_bloco` (QR compacto,
versão embutível de `draw_qr_page`) — detalhes em `DESIGN_SYSTEM.md`
§5.9–5.12. `python/temas/mobilidade.py` foi reescrito (não só editado) para
usar os 5 métodos de página novos.

Verificado nos 4 datasets existentes (Campinas, Montes Claros,
exemplo_fortaleza, exemplo_teresina): PDF sai com exatamente 5 páginas,
sem sobreposição de elementos, `tools/verificar_texto.py` e
`tools/verificar_arte.py` passam 4/4. Ver também a correção de polaridade
do ranking nas Diretrizes de Engenharia abaixo — foi descoberta durante
este trabalho, não antes, porque é a primeira vez que `cor_por_percentil`
entrou em uso real no tema.

**Adendo (2026-09-21, mesmo dia):** depois de ver as 5 páginas com dado real,
o usuário confirmou que a **forma como os dados aparecem está correta** (não
mexer nos KPIs/tabelas/gráficos/ranking) mas pediu que a **capa e o padrão
visual geral** ficassem de fato no mesmo padrão do IFEM — o trabalho acima
tinha coberto densidade/estrutura de página, não a "pele" visual. Investigação
no repo real do folheto-ifem (`dadosfnp/folheto-ifem`, clonado localmente para
referência, não versionado aqui) mostrou que **a capa do IFEM não é gerada por
código**: é um PNG pré-composto (mosaico fotográfico do município, mascarado
pelo alfabeto modular) que o código só sobrepõe com texto dinâmico. Sem
fotografia real de Campinas/Montes Claros neste repo (`_capa_foto` nunca foi
preenchido, ver SCHEMA.md), replicar isso literalmente exigiria uma arte nova
que não existe — não é uma decisão de código, é um asset que falta. Duas
mudanças, ambas sem depender de asset novo, aplicadas em vez disso:

1. **Faixa inferior da capa: branca, não azul** (`draw_capa_padrao`) — o
   contraste "banda de informação clara sobre topo escuro" é a característica
   mais reconhecível da capa real do IFEM, e não depende de foto nenhuma.
   Título passou de branco para `BLUE_DARK`; acento de "sistema modular"
   (2 quartos de círculo translúcidos) foi adicionado ao topo escuro no lugar
   do mosaico fotográfico que falta.
2. **`draw_decoracao_rodape`, portado do folheto-ifem** (`_decorar_rodape` em
   `python/temas/ifem.py` de lá) — preenche o respiro no fim de cada página de
   conteúdo com o alfabeto modular (`assets/padroes/arte0|1|2.png`, arquivos
   que já existiam neste repo, herdados desde o início e nunca usados). Isso
   resolve, de quebra, o "sobra respiro no fim de algumas páginas" que estava
   documentado como pendência de ajuste fino desde a Decisão 1.

Nenhuma mudança em `python/temas/mobilidade.py` além de chamar a função nova
no fim de cada página — o conteúdo (KPIs, tabelas, gráficos, ranking)
permanece exatamente como estava, por pedido explícito do usuário. Ver
`DESIGN_SYSTEM.md` §5.1 e §5.13.

**Segundo adendo (2026-09-21, mesmo dia):** o usuário aprovou o resultado
acima ("ficou muito boa a alteração... a forma como as informações
aparecem está perfeita") e pediu 3 ajustes adicionais, sem tocar em nenhum
dado/componente de conteúdo:

1. **Fundo branco em toda página, não bege.** `PAPER` (o bege herdado do
   folheto-ifem) nunca foi removido do `tokens.py`, só parou de ser usado
   como fundo de página — trocado por `WHITE` em `_topo_pagina`
   (`mobilidade.py`) e em `draw_capa_padrao`. Ver `DESIGN_SYSTEM.md` §2.
2. **Capa personalizada "como no IFEM".** Investigação no repo real
   (`dadosfnp/folheto-ifem`, clonado localmente só para referência, não
   versionado aqui) mostrou que **a capa do IFEM não personaliza foto por
   município** — é sempre o mesmo PNG pré-composto
   (`indicadores_fnp_mapa_vivo_clean.png`) para qualquer um dos 5.570
   municípios; só o nome e 2 números de ranking são texto dinâmico por
   cima (`python/temas/ifem.py::_pag_capa`, confirmado lendo o código, não
   suposição). Perguntado ao usuário antes de implementar (não presumir
   contra evidência de código): confirmado que o padrão certo é replicar
   essa mesma técnica — **um único desenho fixo, o mesmo pra todo
   município**, não fotografia real de Campinas/Montes Claros (que este
   repo não tem, ver `assets/README.md`).
3. **Alfabeto modular soletrando "MOBI" na capa** (equivalente ao
   `ifemestilo.png`/wordmark "IFEM" do folheto-ifem). Reconstruído em vetor
   puro (ReportLab, sem PNG) a partir de `inspiration/Folheto_Alfabeto.jpeg`
   daquele repo — um specimen sheet do alfabeto completo (C,O,S,I,P,D,B,F,
   G,M,N,L,J e minúsculas) que, por sorte, já tinha as 4 letras exatas de
   que precisávamos (M, O, B, I). Nova primitiva genérica
   `draw_alfabeto_modular_palavra` em `core/components.py` — a palavra é
   sempre um parâmetro (`palavra_capa`), núcleo não sabe que é "MOBI". Ver
   `DESIGN_SYSTEM.md` §5.14.

**Terceiro adendo (2026-09-21, mesmo dia):** o usuário pediu a peça que
faltava — a foto de fundo mascarada em grade (o mosaico real da capa do
IFEM, não só a estrutura em volta dela) — e indicou um arquivo já existente
em outro projeto seu (`04-Radar Brasil/radar-brasil/static/img/mobilidade-
capa.jpg`, fora deste repo). Trazido para `assets/capa/mobilidade-capa.jpg`
— redimensionado de 4096×2802/6,6 MB para ~1600px/~380 KB antes de entrar
no repo (o tamanho original é pesado demais pra um asset versionado e pra
embutir em cada PDF gerado). É uma foto genérica de mobilidade urbana
(ciclofaixa), sem relação com Campinas ou Montes Claros especificamente —
consistente com o achado do segundo adendo: a foto real do IFEM também não
é por município.

Nova primitiva `draw_mosaico_fotografico` (`core/components.py`) recorta
essa foto numa grade de janelas no vocabulário modular via *clipping
paths* do ReportLab (quarto de círculo / meio círculo / quadrado cheio,
grade determinística por `seed`) — não um PNG pré-composto, e não a foto
lisa que `draw_capa_padrao` desenhava antes deste adendo. Ver
`DESIGN_SYSTEM.md` §5.15.

**Quarto adendo (2026-09-21, mesmo dia):** com o mosaico no lugar, o
usuário pediu que a faixa inferior da capa (abaixo do mosaico) copiasse a
faixa real do IFEM com precisão: logo à esquerda, barra separadora
vertical, nome do município + ranking à direita — em vez do formato
anterior (título "SEGURANÇA VIÁRIA" grande + selos circulares de ranking),
que não seguia esse layout. `draw_capa_padrao` foi refeita nessa parte:
- Assinatura da função mudou: `titulo_capa`/`subtitulo` viraram
  `municipio_nome` (nome grande, à direita da barra) + `eyebrow_capa`
  (texto pequeno acima do nome — `mobilidade.py` passa "Segurança viária ·
  Ficha de diagnóstico preliminar" aqui, preservando a identidade temática
  que antes vivia no título grande).
- `destaques` deixou de desenhar selo circular e passou a desenhar texto
  ("RANKING DE MORTALIDADE NO ESTADO" / posição colorida + "de N
  municípios"), igual ao "RANKING POR POPULAÇÃO" da capa real do IFEM.
- Único caller (`mobilidade.py::_pag_capa`) atualizado junto — não há
  outro tema usando `draw_capa_padrao` neste repo hoje.

**Pendência que ficou exposta por este ajuste, resolvida no mesmo dia:** o
slot da logo FNP (agora bem mais visível, ocupando ~20% da largura da
faixa) tinha ficado vazio — não foi encontrado em nenhum lugar do
computador do usuário durante a investigação anterior. O usuário então
apontou o arquivo certo (`logo-FNP.png`, já em uso em outros projetos FNP
do mesmo usuário: Legislativo FNP, Radar Brasil, IFEM, Subfinanciados) e
pediu pra usar nesse lugar. Movido para `assets/logos/fnp-logo.png`
(caminho que o código já esperava — nenhuma mudança de código, só o
arquivo chegando). Ver `assets/README.md`.

---

## Diretrizes de Engenharia

**Núcleo (`python/core/`) nunca conhece um tema específico.** Foi
exatamente o oposto disso que causou o retrabalho ao herdar `capa.py`/
`ultima.py` do folheto-ifem (hardcoded a um PNG do IFEM apesar de viverem
em `core/`) e a dependência de `ifem_assets` dentro de
`draw_page_number`. Qualquer nova primitiva visual entra em
`components.py` de forma genérica (parâmetros, nunca um `if tema == "x"`).

**Tokens só em `core/tokens.py`.** Cores, tamanhos, dimensões — nunca
hardcodar num arquivo de tema.

**Degradação é sempre barulhenta.** Campo ausente no JSON não derruba o
gerador — a seção sai com `"n/d"` ou uma mensagem de "dado ainda não
disponível", e um aviso vai para `stderr` (`_avisar_se_ausente` em
`mobilidade.py`). Nunca transformar um aviso desses em silêncio.

**Nunca propor comando destrutivo em banco como passo de rotina** (lição
herdada do `folheto-ifem`, `tasks/lessons.md` de lá) — se algum dia este
projeto ganhar um banco (ver Decisão 2 acima), qualquer comando que apague,
dropa, trunque ou sobrescreva dados vai numa mensagem isolada, com o risco
declarado antes, nunca dentro de uma lista de passos "normais".

**Precisão de dado importa mais aqui do que em qualquer folheto anterior.**
Este documento cita taxas de mortalidade e ranking de causas de morte —
número errado aqui não é só um typo, é uma alegação sobre mortes reais.
Nunca completar um campo vazio com um valor "razoável" para o PDF "ficar
completo". Preferir sempre "n/d" ou a seção ausente a um número inventado.

**Comentário Django `{# #}` nunca em mais de uma linha, nos templates de
`web/municipios/templates/`.** O tokenizer do Django não trata esse par
como multi-linha (falta `re.DOTALL`) — um `{# ... #}` que quebra linha
sobra como texto literal `{#`/`#}` no HTML renderizado (ou, dentro de um
`<script>`, vira `SyntaxError` de JS em tempo de execução, quebrando o
script inteiro **sem erro nenhum do lado do Django** — foi assim que o
`tailwind.config` do back-office silenciosamente nunca rodava, e nenhuma
cor customizada aparecia). Comentário de uma linha só, `{% comment %}
...{% endcomment %}` para texto maior, ou comentário `/* */`/`//` nativo
quando é dentro de `<script>`/`<style>`.

**Polaridade do ranking:** os campos de posição que já vêm prontos do dado
tratado (`*_pos`/`*_total` de `mortalidade_2024`, `ranking_causas_morte`)
usam `cor_por_percentil` (a **normal**, posição 1 = melhor/verde) — **não**
a invertida. Confirmado na fonte: a aba `metodologia` de
`data/external/indicadores_sim_relatorio.xlsx` documenta "Ranking: ordenado
da menor para a maior taxa. A posição 1 corresponde à menor taxa de
mortalidade" — ou seja, a própria fonte já ordena "1 = melhor", a mesma
convenção que `cor_por_percentil` assume. Usar a invertida em cima disso
pintaria a cidade mais segura de vermelho. (Esta regra estava documentada
ao contrário numa versão anterior deste arquivo — corrigido em 2026-09-21,
antes de qualquer PDF real ter usado a cor errada.) `cor_por_percentil_invertido`
continua existindo para o caso hipotético de um ranking construído do zero
com a convenção oposta ("maior valor = melhor") — nenhum campo deste
projeto está nesse caso hoje. Ver `DESIGN_SYSTEM.md` §2.

---

## Pendências e próximos passos

### Marco: dados reais dos dois pilotos chegaram (2026-09-18)

`data/mobilidade/campinas.json` e `data/mobilidade/montes_claros.json`
existem e são **dado real, não exemplo** — gerados por
`tools/dados_tratados_para_json.py` a partir de `data/external/`
(planilhas já tratadas: `populacao_anual.xlsx`, `area_municipal_2024.xlsx`,
`indicadores_frota.xlsx`, `indicadores_sim_relatorio.xlsx`,
`indicadores_sih_relatorio.xlsx`) e `data/raw/` (extração original SIH/SIM
em parquet, ~6,6 GB — **nunca versionado em git**, ver `.gitignore`; cada
máquina mantém sua própria cópia local até existir o banco mencionado na
Decisão 2). Isso resolve praticamente toda a lista antiga de "dado que a
equipe ainda está coletando": população, área, frota, mortalidade 2024,
série histórica de mortes 2010-2024, internações 2025 e série histórica de
internações — tudo isso agora é real para os dois pilotos, com PDF gerado
e validado (`python python/gerar.py --tema mobilidade --dados
data/mobilidade/campinas.json`).

Rodar de novo quando a planilha tratada for atualizada:
`python tools/dados_tratados_para_json.py` (ou `--municipio campinas` /
`--municipio montes_claros` para só um).

**Ainda não coberto por nenhuma fonte disponível** (não é código a
escrever, é dado que precisa vir de outro lugar):
- **Ranking de causas de morte** (posição de "acidentes de trânsito" entre
  as causas de óbito do município, por ano) — SIM/SIH do DATASUS não têm
  esse recorte; o exemplo de Fortaleza usou um relatório da Secretaria
  Municipal de Saúde local. Precisa do equivalente para Campinas/Montes
  Claros, se existir.
- **Início/fim da gestão do prefeito atual**
  (`internacoes_serie_historica.gestao_atual`, usado pra hachurar o
  gráfico de internações) — dado político, não fiscal/de saúde; não vem de
  SIM/SIH/SENATRAN. Fácil de preencher (é só o ano de posse e o ano
  previsto de fim de mandato), mas precisa ser confirmado antes de
  escrever — não adivinhar.
- Custo hospitalar por hospital e por modo (pedido nº 9 do briefing) —
  schema documentado em `SCHEMA.md`, nenhuma página implementada ainda.
- Mapa de internações por bairro na RM (pedido nº 9 do briefing) — precisa
  de dado geográfico E de um componente de mapa novo no núcleo (o motor
  herdado não desenha mapas, só fotos/ilustrações full-bleed e formas
  geométricas simples). `data/external/contorno_municipal_2024.gpkg` é
  contorno **municipal**, não por bairro — não resolve isso sozinho. Não
  começar a implementar sem primeiro decidir o formato do dado geográfico
  por bairro.
- `problema.citacao` (citação de destaque da página 2) e `metodologia`
  (passos customizados) — texto editorial, não dado SIM/SIH; ficam com o
  texto padrão do tema até alguém escrever um específico.

**Trabalho técnico pendente:**
- **URL do QR code é placeholder, não confirmada** (`FolhetoMobilidade.URL_PADRAO` em `mobilidade.py` = `https://fnp.org.br/mobilidade`) — nunca enviar um PDF para impressão sem sobrescrever com uma URL real e testada via o campo `"url"` no JSON de dados. Vale pros dois pilotos reais também, que hoje ainda usam o placeholder.
- **Logo oficial FNP — resolvido em 2026-09-21** (ver `assets/README.md` e Decisão 5, quarto adendo). `assets/logos/fnp-logo.png` existe e aparece no rodapé de todas as páginas de conteúdo e à esquerda da barra separadora na capa.
- Fontes oficiais (Barlow Condensed + Inter) — baixar com `tools/baixar_fontes.py` antes de qualquer PDF "para valer" (sem elas, sai em Helvetica). Já feito na máquina onde os PDFs de Campinas/Montes Claros foram gerados.
- **Espaçamento vertical da A4 — resolvido (2026-09-21).** Não foi um recálculo manual de cada componente: `draw_decoracao_rodape` (portado do `_decorar_rodape` do folheto-ifem, ver Decisão 5) preenche o respiro no fim da página com o alfabeto modular (`assets/padroes/arte0|1|2.png`) sempre que sobra espaço — mesmo mecanismo, mesmos arquivos, do folheto-ifem. Ver `DESIGN_SYSTEM.md` §5.13.
- **Site estático de distribuição (`docs/`) — implementado (Decisão 4).** `docs/index.html` + `tools/build_site.py` + `tools/publicar_release.ps1` prontos e testados; `docs/folhetos.json` já mostra os 2 pilotos reais (com URL de release que ainda não existe no GitHub). Falta: (1) habilitar GitHub Pages em `dadosfnp/folheto-mobilidade` (Settings → Pages → branch `main`, pasta `/docs` — passo manual, fora do alcance de código) e (2) publicar de verdade a release (`tools/publicar_release.ps1`) e recommitar `docs/folhetos.json` na main.
- `tools/dados_tratados_para_json.py` está escrito e funcionando para o formato de `data/external/` atual — se esse formato mudar (nova coluna, planilha reestruturada), o script precisa acompanhar.
