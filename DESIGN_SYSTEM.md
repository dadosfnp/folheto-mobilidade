# Design System — Folheto Mobilidade

Este projeto herdou o motor de geração (núcleo `python/core/`) e a identidade
visual institucional do **folheto-ifem** (`dadosfnp/folheto-ifem`), o gerador
unificado de folhetos da Frente Nacional de Prefeitas e Prefeitos. Paleta,
tipografia e a maior parte dos componentes visuais abaixo são os mesmos —
**só o formato de página e a estrutura de conteúdo mudaram**, ver §4 e §6.

> Ver `CLAUDE.md` para o histórico de decisão (por que A4 em vez do quadrado
> 20×20cm original, por que os dados ainda não vêm de banco).

---

## 1. Princípio fundador: sistema modular

Toda a identidade nasce de **um vocabulário gráfico mínimo** aplicado em cima
de uma grade de quadrados de mesma dimensão. Existem apenas 4 operações
dentro de cada módulo:

| Operação              | Aparência                              | Uso                              |
|-----------------------|-----------------------------------------|-----------------------------------|
| Quadrado vazio        | linha externa apenas                   | respiro, ritmo                   |
| Quadrado preenchido   | bloco sólido de cor                    | ênfase, peso visual              |
| ¼ de círculo          | quarto de disco em qualquer canto      | direção, dinamismo               |
| ½ círculo             | semicírculo em qualquer aresta         | suavidade, pontuação             |

**Regra de ouro:** se uma decoração nova precisar ser criada, ela deve sair
desse vocabulário. Não introduzir formas estranhas (triângulos, hexágonos,
ondas) sem aprovação.

---

## 2. Paleta de cores

Idêntica ao folheto-ifem — `python/core/tokens.py` é a fonte da verdade.

| Token         | Hex        | Uso primário                                        |
|---------------|------------|-----------------------------------------------------|
| `BLUE_DARK`   | `#122747`  | Títulos, texto de ênfase, faixas escuras            |
| `BLUE`        | `#1B3A6B`  | Cor institucional FNP — fundos, bordas, headers     |
| `BLUE_MID`    | `#3D6FA8`  | Gráficos secundários, hover, variação de azul       |
| `YELLOW`      | `#FFC72C`  | Acento, headlines de seção, aspas, gráficos         |
| `YELLOW_DARK` | `#C99A1F`  | Ranking (números grandes), variação de amarelo      |
| `GREEN`       | `#2A8F5C`  | Pontos fortes, contornos do alfabeto modular        |
| `RED_BURNT`   | `#C04A1A`  | Pontos de atenção (uso pontual)                     |
| `CREAM`       | `#F4EFE6`  | Fundo de cards, fundo neutro quente                 |
| `PAPER`       | `#FBF8F2`  | **Não usado como fundo de página** (ver nota abaixo) |
| `RULE`        | `#D9D2C3`  | Linhas divisórias, bordas sutis                     |
| `MUTED`       | `#6B6B6B`  | Texto secundário, fonte/captions                    |
| `INK`         | `#1A1A1A`  | Texto corrido                                       |

**Fundo de página: branco (`WHITE`), não `PAPER`/bege — corrigido em
2026-09-21, a pedido explícito do usuário.** O fundo bege que o motor herdou
do folheto-ifem (`PAPER`) não é usado em nenhuma página do tema mobilidade
hoje (capa nem conteúdo) — `PAPER` continua definido em `tokens.py` (mantido
do núcleo herdado, sem uso ativo no tema mobilidade hoje). Se um tema futuro
quiser o bege de volta, é uma decisão de tema, não voltar ao padrão do
núcleo.

**Paleta ordinal (posição no ranking) — atenção à polaridade.**
`core/paleta_ranking.py` tem duas funções: `cor_por_percentil` (posição 1 =
melhor, verde) e `cor_por_percentil_invertido` (posição 1 = pior, verde só
no fim da lista). **Para os campos de posição que já vêm prontos do dado
tratado (`*_pos`/`*_total` de `mortalidade_2024`, `ranking_causas_morte`),
use sempre `cor_por_percentil` (a normal) — nunca a invertida.** A fonte
(SIM/DATASUS, ver `metodologia` em `indicadores_sim_relatorio.xlsx`) já
ordena "posição 1 = menor taxa de mortalidade = melhor"; aplicar a função
invertida em cima disso pintaria a cidade mais segura de vermelho. A
invertida só serve para um ranking que **você constrói do zero** ordenando
"maior valor = melhor" (nenhum caso assim existe ainda neste projeto).
Confirmado visualmente: Campinas (taxa melhor que a média) sai com círculos
verdes; Montes Claros (taxa pior que a média) sai laranja/amarelo — nunca o
contrário.

**Travessão (—) é proibido em qualquer texto impresso.** Vale para copy nova
e para placeholder de valor ausente (usar `n/d`, nunca um traço solto — num
KPI o leitor confunde com sinal de menos). A meia-risca (–) de intervalo,
como em "2010–2024", é permitida. Separador de rótulos curtos: ponto médio
(`·`).

---

## 3. Tipografia

Idêntica ao folheto-ifem (Barlow Condensed + Inter, fallback automático para
Helvetica se as fontes não estiverem em `fonts/` — ver `fonts/README.md`).

| Função              | Fonte                          | Peso        | Tamanho típico |
|---------------------|---------------------------------|-------------|----------------|
| Título de capa      | Barlow Condensed Bold          | 700         | 24–42pt        |
| Headline de seção   | Barlow Condensed Bold          | 700         | 24–32pt (caixa alta) |
| Eyebrow / capítulo  | Barlow Condensed SemiBold      | 600         | 8–10.5pt CAIXA ALTA |
| Texto corrido       | Inter Regular                  | 400         | 8.5–9.5pt      |
| Citação / destaque  | Inter SemiBold ou Barlow Bold  | 600/700     | 11–16pt        |
| Caption / fonte     | Inter Regular                  | 400         | 6.5–9pt        |

---

## 4. Formato e grid — DIFERENTE do folheto-ifem

O folheto-ifem usa página quadrada fixa (20×20cm). Este projeto usa
**A4 retrato (21×29,7cm)** — decisão registrada em `CLAUDE.md`: reaproveitar
o motor como está, só trocando o tamanho do canvas (`PAGE_SIZE` em
`python/core/tokens.py`), sem reescrever o núcleo para um layout de painéis
dobrados de verdade. As dobras físicas (A3/A4, duas dobras — ver briefing do
projeto) são, por ora, **guia de corte/dobra na hora de imprimir**, não algo
que o gerador calcula ou desenha.

- **Página:** 21cm × 29,7cm (A4 retrato).
- **Stripe lateral:** 20pt de azul (`BLUE`) numa das laterais — alterna
  esquerda/direita por página, com numeração branca no rodapé do stripe.
- **Margem útil:** 36pt no lado oposto ao stripe e nas margens sup./inf.
- **Largura de conteúdo:** `CONTENT_W` em `tokens.py` — calculada a partir da
  largura real da página, nunca hardcoded num arquivo de tema.
- **Cabeçalho:** texto pequeno em `MUTED`, caixa alta — nome da publicação.
- **Rodapé:** label da seção à esquerda + logo FNP à direita (se o arquivo
  existir — ver `assets/README.md`).

> **Espaçamento vertical da A4 — resolvido (2026-09-21), não mais "ajuste
> fino pendente":** o respiro que sobrava no fim das páginas de conteúdo
> agora é preenchido por `draw_decoracao_rodape` (ver §5.13) — o mesmo
> mecanismo do folheto-ifem, não um recálculo manual de cada componente.
> Onde o conteúdo real for suficiente para ocupar a página sozinho, a
> decoração simplesmente não aparece (ela nunca compete com conteúdo, só
> preenche o que sobra).

**A3, disponível desde 2026-09-21 — mesmo design, escalado, não um
segundo layout.** `FolhetoFNP.gerar()` desenha cada página com A4 lógico
(`PAGE_SIZE`, `STRIPE_W`, `MARGIN`, `CONTENT_W` — nenhum desses muda) e
aplica `c.scale()` no canvas físico quando `tamanho="A3"`. Nenhum
componente em `components.py` sabe que existe A3; a escolha vive só em
`base_folheto.py`. Ver CLAUDE.md, seção do back-office, para a cadeia
completa (CLI `--tamanho`, Django `?tamanho=A3`, toggle em `lista.html`).

---

## 5. Componentes recorrentes

### 5.1 Capa (`core/components.py::draw_capa_padrao`)
- Fundo **branco** em toda a página (não bege, não azul — ver §2). A zona
  acima da faixa mostra `foto_path` — hoje sempre `assets/capa/mobilidade-
  capa.jpg` (`_capa_foto` no JSON tem prioridade se um piloto ganhar foto
  própria, ver SCHEMA.md) — **mascarada pelo alfabeto modular**
  (`draw_mosaico_fotografico`, §5.15), não uma foto lisa retangular. Sem
  nenhuma foto disponível, `palavra_capa` desenha essa mesma zona no
  alfabeto modular como palavra (`draw_alfabeto_modular_palavra`, §5.14) —
  o tema mobilidade passa `palavra_capa="MOBI"` como esse fallback.
- Fio `RULE` separando a zona de cima (foto ou palavra) da faixa de
  informação — mesmo contraste "banda clara sobre topo" do folheto-ifem
  (capa.py de lá usa um PNG pré-composto foto+banda branca; aqui é tudo
  branco, então o fio é o que ainda marca a transição — ver CLAUDE.md
  Decisão 5).
- **Faixa inferior no layout exato da capa real do IFEM** (corrigido em
  2026-09-21, ver CLAUDE.md Decisão 5): logo FNP à esquerda (centralizada
  verticalmente, ~20% da largura útil), barra separadora vertical (`RULE`,
  em ~42% da largura útil), e à direita `eyebrow_capa` (pequeno, caixa
  alta, `MUTED`) + `municipio_nome` (grande, `BLUE_DARK` bold, encolhe se
  não couber) + até 2 linhas de `destaques`.
- `destaques`: cada item vira uma linha "RÓTULO" (caixa alta, pequeno) +
  posição (grande, cor via `cor_por_percentil`, sufixo "ª") + "de N
  municípios" — texto, **não mais selo circular** (mudou nesta mesma
  correção; a versão anterior com círculos foi só uma etapa intermediária,
  não o padrão final).
- O bloco de texto (eyebrow + nome + destaques) é **centralizado na mesma
  linha média da logo**, não ancorado no topo da faixa — a altura do bloco
  é calculada antes de desenhar (depende do tamanho de fonte do nome e de
  quantos `destaques` existem) especificamente para isso. Sem essa conta,
  um bloco de texto mais curto que a logo fica "grudado" no topo enquanto
  a logo, sempre centralizada, sobra por baixo — leu como desalinhado
  (reportado pelo usuário no primeiro PDF com este layout).

**Achado que motivou este desenho (2026-09-21):** a capa real do IFEM
(`dadosfnp/folheto-ifem`, clonado localmente para referência, não
versionado aqui) **não personaliza foto por município** — `python/temas/
ifem.py::_pag_capa` sempre carrega o mesmo PNG (`indicadores_fnp_mapa_vivo
_clean.png`) pra qualquer um dos 5.570 municípios; só o nome e os 2 números
de ranking são texto dinâmico por cima. O mesmo padrão foi replicado aqui:
`palavra_capa` é um único desenho fixo (o mesmo "MOBI" pra Campinas, Montes
Claros ou qualquer piloto futuro), só o texto/ranking da faixa muda.

*Diferença do folheto-ifem: lá a capa usa um PNG pré-composto específico do
IFEM (`core/capa.py`, não herdado por este repo — era hardcoded a um asset
que não existe aqui, um mosaico fotográfico do município com o alfabeto
modular como máscara). `draw_capa_padrao` é genérico, reutilizável por
qualquer tema futuro, e não depende de fotografia real do município — que
este projeto não tem para nenhum dos pilotos ainda (`_capa_foto` seguirá
funcionando no dia em que existir).*

### 5.2 Divisória de seção (`draw_section_divider`)
Fundo `BLUE` cheio, quarto de círculo translúcido no canto, capítulo em
`YELLOW`, título grande branco, subtítulo em azul claro.

### 5.3 Página de conteúdo
Fundo `PAPER`, eyebrow + título no topo, corpo Inter Regular, cards/tabelas
conforme o conteúdo, sempre com `draw_caption` citando a fonte do dado.

### 5.4 Card de KPI (`draw_kpi_box`)
Borda esquerda `BLUE_MID`, label em caixa alta, número grande Barlow Bold
(encolhe automaticamente se não couber), unidade em fonte menor ao lado.

### 5.5 Tabela comparativa (`draw_table`)
Header `BLUE` + texto branco, linhas alternadas branco/creme, coluna de
destaque (`highlight_col`) em `BLUE_DARK` SemiBold. Usada nas páginas de
mortalidade e internações (município vs. RM vs. mesmo porte vs. estado vs.
Brasil vs. capitais) — **mesmas larguras de coluna nas duas tabelas**, para
que leiam como um sistema, não duas tabelas soltas.

### 5.6 Gráfico de linha (`draw_line_chart` — NOVO, não existe no folheto-ifem)
Série histórica multi-categoria (mortes/internações por modo, por ano), sem
dependência externa (só ReportLab). Suporta uma faixa de destaque
(`faixa_destaque`) para hachurar um intervalo — usado para marcar o período
da gestão do prefeito atual no gráfico de internações (pedido do briefing).

### 5.7 QR code / encerramento (`draw_qr_page`)
Fundo azul-escuro (ou imagem, se houver), QR 140×140pt, URL em `YELLOW`
abaixo.

### 5.8 Bullets / lista
Quadrado `BLUE` 8×8pt. Nunca bullets redondos genéricos.

### 5.9 Selo de ranking grande (`draw_ranking_stat_grande` — NOVO)
Círculo colorido (via `cor_por_percentil`, ver §2) com a posição em número
grande, "de N" abaixo em fonte menor, rótulo acima em caixa alta. Usado na
capa (posição no estado/Brasil) e, sem o "de N", como selo numerado de passo
na página de metodologia (`_selo_numerado` em `mobilidade.py`).

### 5.10 Barra percentual (`draw_percentual_bar` — NOVO)
Barra horizontal vermelho→verde (via `cor_status_landing`), preenchida até o
percentual informado. O rótulo é sempre passado pelo chamador — nunca um
texto fixo tipo "supera X%", porque a polaridade muda conforme a métrica
(mortalidade não é "quanto maior, melhor").

### 5.11 Donut (`draw_donut_chart` — NOVO)
Gráfico de rosca genérico, segmentos `{label, valor, cor}`, com legenda
lateral opcional. Não desenha nada se todos os valores forem `None`/zero
(degradação silenciosa e intencional — decorativo, não uma tabela; o "n/d"
já aparece na tabela ao lado). Usado para a distribuição de mortes por modo
no último ano disponível.

### 5.12 QR compacto (`draw_qr_bloco` — NOVO)
Card branco arredondado com QR + rótulo "Acesse" + URL, dimensionado para
encaixar ao lado de outro conteúdo (≈120×150pt) — diferente de
`draw_qr_page` (§5.7), que pinta a página inteira e segue existindo para um
tema que queira uma página de encerramento dedicada.

### 5.13 Decoração de rodapé / alfabeto modular (`draw_decoracao_rodape` — NOVO, portado do folheto-ifem)
Preenche o respiro que sobra no fim de uma página de conteúdo com um dos 3
padrões modulares (`assets/padroes/arte0|1|2.png`, herdados sem mudança do
folheto-ifem — ver tabela na abertura deste documento). Portado de
`_decorar_rodape` (`python/temas/ifem.py`) como primitiva genérica de
`core/components.py`, sem nenhuma referência a tema.

- `y_max` é o Y onde o conteúdo real terminou — a função mede o espaço livre
  até o rodapé e escolhe sozinha entre as 3 artes (da mais alta, `arte2`,
  até a ultra-fina `arte0`); se nenhuma couber, não desenha nada. **Quem
  mede é a função, nunca o chamador** — cada página só informa onde parou
  de desenhar, mesma regra que evita o defeito que o folheto-ifem já teve
  (tabela com a última linha coberta por decoração calculada errado).
- Chamada no fim de cada uma das 4 páginas de conteúdo do tema `mobilidade`
  (`mobilidade.py`, um `draw_decoracao_rodape(...)` por página). Na página 5
  (duas colunas: passos numerados + QR), o `y_max` passado é o menor dos
  dois — nunca sobrepõe o card de QR, mesmo quando ele termina mais baixo
  que o texto.
- É o que resolve o "sobra respiro" documentado como pendência em versões
  anteriores deste arquivo (§4) — não um recálculo manual de espaçamento
  por componente.

Verificação objetiva no PDF gerado: `python tools/verificar_arte.py output/`.

### 5.14 Alfabeto modular por palavra (`draw_alfabeto_modular_palavra` — NOVO, técnica reconstruída do folheto-ifem)
Desenha uma palavra usando só as formas do "sistema modular" (§1: quarto de
círculo, meio círculo, quadrado) — reconstrução em vetor (ReportLab puro,
sem PNG) do alfabeto visto em `inspiration/Folheto_Alfabeto.jpeg` do
folheto-ifem (arquivo não trazido para este repo — só a técnica foi
reconstruída, letra por letra, a partir da imagem de referência).

- Cada letra é uma função `_glifo_<letra>(c, x0, y0, modulo, cores, traco)`
  que desenha dentro de uma célula de `2×modulo` (`1×modulo` para o "I",
  mais estreito) e devolve a largura usada — cadastradas em
  `_GLIFOS_MODULARES`. Hoje **M, O, B, I, L, D, A, E** têm glifo (as letras
  que o tema mobilidade precisa para soletrar "MOBI" na capa e
  "MOBILIDADE" no stripe, §5.16); uma letra sem glifo degrada para um
  quadrado vazio, nunca quebra a geração.
- `traco` (espessura do traçado, `_TRACO_MODULAR` por padrão) é parâmetro
  desde que o stripe (§5.16) passou a reaproveitar os mesmos glifos em
  traço bem mais fino (0.5pt) — sem isso, o traço grosso da capa ficaria
  desproporcional dentro dos 20pt do stripe.
- **M vs. D:** as duas letras usam o mesmo domo de 180° (dois quartos de
  círculo com o mesmo vértice) — sem mais nada, ficam indistinguíveis. `M`
  ganha uma linha reta do vértice até o topo do arco (a "costura" entre as
  duas cristas); `D` não ganha essa linha, porque ali o domo deve ler como
  uma curva contínua só. Achado ao construir o stripe (§5.16): o traço fino
  (0.5pt) e a rotação de 90° tornam essa diferença ainda mais sutil que na
  capa — QA visual (recorte via PyMuPDF, nunca só "gerou sem erro") pegou o
  caso antes de qualquer PDF real sair com M lendo como D.
- `largura_alfabeto_modular_palavra(palavra, modulo)` calcula a largura
  total sem desenhar nada — usado por `draw_capa_padrao` pra centralizar a
  palavra e escolher o `modulo` (mira ~80% da largura de conteúdo
  disponível, até um teto de 90pt por módulo).
- Cor cíclica a partir de uma paleta de 4 tons (`_PALETA_MODULAR`:
  `BLUE_DARK`, `BLUE`, `BLUE_MID`, `YELLOW_DARK`) — mesma família de cores
  usada em `draw_decoracao_rodape` (§5.13), pra as duas decorações lerem
  como o mesmo sistema visual.
- Genérico: a palavra é sempre um parâmetro (`palavra_capa` em
  `draw_capa_padrao`) — o núcleo nunca sabe que o tema mobilidade soletra
  "MOBI" especificamente. Um tema novo passaria a própria palavra (e
  precisaria adicionar glifo pra qualquer letra que ainda não exista em
  `_GLIFOS_MODULARES`).

### 5.15 Mosaico fotográfico mascarado (`draw_mosaico_fotografico` — NOVO, técnica real do folheto-ifem)
A capa real do IFEM não mostra a foto como um retângulo liso — ela aparece
fatiada por uma grade de janelas no vocabulário modular (quarto de círculo,
meio círculo, quadrado cheio), com branco entre as formas. Reconstruído
aqui via **clipping paths do ReportLab** (não um PNG pré-composto): a
mesma foto é redesenhada uma vez por célula da grade, cada vez recortada
(`canvas.clipPath`) por uma forma diferente.

- Grade determinística: `seed` fixo (padrão 13) garante que a mesma foto
  sempre produz a mesma grade — regenerar o PDF não muda o resultado, nem
  produz uma grade diferente por município (é a mesma foto pra todos, ver
  §5.1 e o achado documentado ali).
- Cada célula sorteia entre 3 categorias: quadrado cheio (~25%), quarto de
  círculo com vértice num dos 4 cantos da célula (~40%, mesma técnica de
  `_glifo_m`/`_glifo_o` em §5.14, aqui usada como máscara em vez de
  contorno), ou meio círculo com base numa das 4 arestas (~35%, mesma
  técnica do `_glifo_b`). Fora da forma sorteada, a célula fica branca —
  isso é o que dá o efeito "janela fragmentada", não um recorte comum.
- **Contorno fino (`WHITE`, 0.6pt) em TODA célula, sem exceção** — mesmo
  padrão da capa real do IFEM (as janelas do mosaico de lá têm contorno
  visível e uniforme, não são recortes soltos). Uma linha só, uma
  espessura só, nunca um tratamento especial só pra alguma célula
  específica ("padrão", não destaque — pedido explícito do usuário).
- `y0`/`y1` delimitam a faixa vertical onde o mosaico é desenhado
  (full-bleed em `page_w`); um clip externo nessa faixa garante que nenhuma
  célula da última linha vaze pra baixo da faixa de informação da capa.
- Não desenha nada se o arquivo de foto não existir — degradação
  silenciosa, mesmo espírito do restante dos componentes decorativos (ver
  §5.11).

**`palavra_mosaico` — soletra dentro da própria grade, não um selo por
cima.** Em vez de sortear a forma de cada célula do bloco ocupado pela
palavra, usa a receita fixa de cada letra (`_RECEITA_GLIFO_MOSAICO` —
mesmas categorias de célula do mosaico: canto de quarto-de-círculo, meio
círculo por aresta, quadrado, círculo inscrito). Ancorada na quina
inferior-direita da grade (2 linhas mais próximas da faixa de informação).

- `margem_direita`: reserva colunas inteiras de respiro antes de ancorar a
  palavra, sem mudar a grade aleatória (que continua sangrando até a borda
  física normalmente) — necessário porque o stripe lateral (20pt) é pintado
  por cima do mosaico depois; sem essa margem, a última letra ficava
  parcialmente escondida atrás dele. `draw_capa_padrao` passa
  `margem_direita=STRIPE_W` quando `lado="dir"`.
- A receita de "B" usa dois meios-círculos por aresta (`esq`/`esq`), não
  dois quartos de círculo de canto — a versão de canto fundia os dois
  bojos num só (lia como "D"); o meio-círculo por aresta cria a "cintura"
  que faz ler como B.
- Como toda célula já tem contorno uniforme (ver acima), a palavra não
  precisa de nenhum tratamento visual extra pra se destacar — a própria
  regularidade da forma (2 letras de largura par, alinhadas à grade) já lê
  como intencional dentro do mosaico aleatório ao redor.

### 5.16 Lettermark vertical no stripe (`draw_lettermark_stripe` — NOVO, padrão real do folheto-ifem)
Toda página (não só a capa) ganha a palavra **"MOBILIDADE"** escrita de
baixo pra cima dentro do próprio stripe lateral de 20pt — mesmo padrão que
o folheto-ifem já tinha (lá, um PNG pré-rotacionado; aqui, desenho
vetorial girado em tempo de execução, sem asset raster nenhum).

- Reaproveita o mesmo alfabeto modular do §5.14 (`_GLIFOS_MODULARES`), só
  que em módulo bem menor (`modulo=7.0`, contra ~80pt na capa) e traço fino
  (`0.5pt`) — cabe inteiro dentro da largura do stripe (`STRIPE_W=20pt`).
- Rotação: `c.translate(cx, (page_h + largura)/2); c.rotate(-90)` — desenha
  a palavra "deitada" (eixo X normal) e gira o canvas inteiro, não a
  palavra ponto a ponto; centraliza verticalmente contra a altura da
  página via `largura_alfabeto_modular_palavra`.
- `setStrokeAlpha(0.35)` — mais discreto que o alfabeto da capa (que é o
  elemento principal da página); no stripe é textura de fundo, não deve
  competir com o conteúdo.
- `lado` (`"dir"`/`"esq"`) decide qual stripe recebe a palavra — sempre o
  mesmo lado que `draw_stripe`/`draw_page_number` já usam naquela página,
  nunca hardcoded.
- Chamado de `_topo_pagina` em `mobilidade.py` (toda página de conteúdo) e
  também do fim de `draw_capa_padrao` (capa) — `PALAVRA_STRIPE = "MOBILIDADE"`
  é constante do tema, não do núcleo; um tema novo passaria a própria
  palavra ou omitiria o parâmetro.

---

## 6. Estrutura canônica do folheto (tema `mobilidade`)

**Teto rígido: no máximo 5 páginas** (decisão do usuário, registrada em
`CLAUDE.md`). Isso significa nenhuma página de divisória — o cabeçalho de
seção vive dentro da própria página de conteúdo, e os pares tabela+gráfico
que antes eram páginas separadas foram fundidos.

| Pág. | Função                                        | Stripe | Status |
|------|------------------------------------------------|--------|--------|
| 01   | Capa (+ selo de posição no estado/Brasil)      | dir    | ✅ implementada |
| 02   | "Por que importa" + KPIs + tabela de mortalidade 2024 + barra percentual | esq | ✅ implementada |
| 03   | Série histórica de mortes + donut por modo + ranking de causas de morte | dir | ✅ implementada (aceita `null`) |
| 04   | Tabela de internações + série histórica de internações (gestão hachurada) | esq | ✅ implementada (aceita `null`) |
| 05   | Metodologia (passos numerados) + "leitos de UTI" + QR compacto | dir | ✅ implementada |
| —    | Custo por hospital, por modo                   | —      | ❌ pendente de dado (ver CLAUDE.md) |
| —    | Mapa de internações por bairro (RM)            | —      | ❌ pendente de dado + componente novo |

> **Regra de stripe:** alternar lados a cada página (espelho), sem reset —
> não há mais divisória no meio pra "recomeçar" o padrão.

---

## 7. Checklist antes de exportar PDF

- [ ] Nenhum travessão (—) no texto do PDF: `python tools/verificar_texto.py output/`.
- [ ] Nenhuma arte de rodapé cobrindo conteúdo: `python tools/verificar_arte.py output/`.
- [ ] Stripes alternam corretamente entre páginas.
- [ ] Numeração de página aparece em todas as páginas.
- [ ] Toda página interna tem cabeçalho e rodapé.
- [ ] Toda fonte de dado aparece como caption em `MUTED` no fim do gráfico/tabela.
- [ ] Nenhum valor ausente aparece como traço solto — sempre `n/d`.
- [ ] Ranking de mortalidade/internação usa `cor_por_percentil` (normal, posição 1 = melhor), nunca a invertida.
- [ ] QR code da última página aponta para URL real.
