# Contrato dos JSONs de entrada — tema `mobilidade`

Cada arquivo `data/mobilidade/<municipio-slug>.json` descreve **um** município.
Arquivos começando com `_` (ex.: `_metodologia.json`) são companheiros
compartilhados por todos os municípios — ver `python/gerar.py`.

Campo ausente ou `null` nunca derruba o gerador: a seção correspondente sai
com `"n/d"` ou uma mensagem de "dado ainda não disponível", e um aviso é
impresso em `stderr`. Ver `python/temas/mobilidade.py`.

> **Nada aqui é dado real de Campinas ou Montes Claros ainda** — a coleta
> está em andamento (ver `CLAUDE.md`, seção Pendências). O arquivo de
> exemplo (`exemplo_fortaleza.json`) transcreve só os números que já
> apareceram, por extenso ou em rótulo de gráfico, no documento de briefing
> do projeto — nunca um valor estimado ou arredondado por mim. Campo que o
> briefing não preencheu (ex.: população, área) fica `null` no exemplo
> também, de propósito — não é para inventar um número plausível.

## Campos implementados nesta primeira versão

```jsonc
{
  "nome": "Fortaleza",           // nome do município
  "uf": "CE",

  "populacao": {"valor": null, "ano": null},
  "area_km2": null,

  // Citação de destaque da página 2 ("Por que isso importa para a
  // cidade"). Lido por python/temas/mobilidade.py::_pag_problema — campo
  // ausente usa um texto padrão embutido no tema, mas dispara o aviso
  // "'problema' ausente" em stderr (ver _avisar_se_ausente).
  "problema": {"citacao": null},

  "frota": {
    // % de crescimento acumulado por período (tabela "Evolução da frota")
    "evolucao_pct": {
      "2003_2010": {"total": 67.1, "automoveis": 49.2, "motocicletas": 150.0},
      "2011_2020": {"total": 47.3, "automoveis": 35.4, "motocicletas": 72.9},
      "2021_2025": {"total": 12.2, "automoveis": 2.5,  "motocicletas": 24.2},
      "2003_2025": {"total": 210.4, "automoveis": 122.2, "motocicletas": 566.2}
    },
    "atual": {"total": 1320000, "automoveis": 633000, "motocicletas": 428000}
  },

  // Taxa de mortalidade por 100 mil hab., ano de referência único (2024 no
  // exemplo). Uma chave por modo: total / motociclistas / pedestres / ciclistas.
  "mortalidade_2024": {
    "total": {
      "municipio": 8.2,
      "rm": 6.9,            "rm_pos": 14,      "rm_total": 19,
      "porte": 8.1,         "porte_pos": 4,    "porte_total": 15,
      "estado": 16.3,       "estado_pos": 41,  "estado_total": 184,
      "brasil": 17.4,       "brasil_pos": 1169,"brasil_total": 5570,
      "capitais": 9.2,      "capitais_pos": 5, "capitais_total": 27
    },
    "motociclistas": { "...": "mesmas chaves" },
    "pedestres":     { "...": "mesmas chaves" },
    "ciclistas":     { "...": "mesmas chaves" }
  },

  // Série histórica de mortes por modo. Todas as listas do mesmo tamanho de "anos".
  "mortes_serie_historica": {
    "anos": [2010, 2011, "...", 2024],
    "total": [410, 440, "..."],
    "motociclistas": ["..."],
    "pedestres": ["..."],
    "ciclistas": ["..."]
  },

  // Internações por sinistro (SIH/SIA). Ainda em coleta — aceitar null.
  "internacoes_2025": {
    "total":          {"municipio": null, "porte": null, "estado": null, "brasil": null},
    "motociclistas":  { "...": "idem" },
    "pedestres":      { "...": "idem" },
    "ciclistas":      { "...": "idem" }
  },

  "internacoes_serie_historica": {
    "anos": [],
    "total": [],
    // janela a hachurar no gráfico — mandato do prefeito atual
    "gestao_atual": {"inicio": null, "fim": null}
  },

  "ranking_causas_morte": {
    "fonte": "SMS",
    "total_causas": 13,
    // posição de "acidentes de trânsito" no ranking geral de causas de morte, por ano
    "posicao_acidentes_transito": {"2016": 6, "2017": 9, "2018": 12, "2019": 9}
  },

  "leitos_uti_hipotetico": {
    "nota": "Texto livre — hoje é a pergunta orientadora do projeto, não um número calculado."
  },

  "metodologia": {"passos": ["...lista de strings, uma por passo. Se ausente, usa o texto padrão do tema."]},

  "url": "https://fnp.org.br/mobilidade",   // QR da última página; se ausente, usa FolhetoMobilidade.URL_PADRAO
  "_capa_foto": null   // caminho de uma imagem full-bleed opcional para a capa; sem ela, fundo azul sólido
}
```

## Duas armadilhas do motor (achadas ao construir o formulário de edição)

`python/core/base_folheto.py` e `python/temas/mobilidade.py` usam
`dict.get(chave, padrão)`, que só cai no padrão se a **chave não existir** —
não protege contra a chave existir com `null`. Duas consequências práticas
para quem editar um JSON à mão (o formulário web em `web/municipios/`
já aplica as duas regras automaticamente):

1. **`url`: ausente ≠ `null`.** Se `url` não existir no arquivo, o gerador
   usa `FolhetoMobilidade.URL_PADRAO`. Se `url` existir como `null`, o QR
   code quebra (`TypeError` não capturado). **Nunca escrever `"url": null`
   — ou a chave tem um valor real, ou não existe.**
2. **Coluna de série 100% vazia deve ser `[]`, nunca uma lista de `null`s.**
   `draw_line_chart` plota por índice de posição; uma lista de `null` é
   *truthy* em Python e entraria na legenda desenhando uma linha vazia (ver
   `mobilidade.py`, filtro `if s["valores"]`). Lista vazia (`[]`) é filtrada
   corretamente e a série some da legenda, como esperado quando não há dado.

## Campos do briefing AINDA SEM página implementada

Estes pedidos do projeto (ver `CLAUDE.md`) dependem de dado que ainda não
existe ou de um componente visual novo (mapa) — o schema abaixo é a intenção
registrada, não um contrato já consumido pelo código:

```jsonc
{
  // Pedido 9 do briefing: custo por hospital, por modo.
  "custo_hospitalar": {
    "hospitais": [
      {"nome": "...", "custo_total": null, "custo_sinistros": null,
       "custo_por_modo": {"motociclistas": null, "pedestres": null, "ciclistas": null}}
    ]
  },

  // Pedido 9 do briefing: mapa por bairro (RM), % do custo que é do próprio
  // município vs. outras cidades atendidas. Precisa de um componente de mapa
  // novo no core — não existe ainda (o motor herdado do folheto-ifem não
  // desenha mapas, só ilustrações/fotos full-bleed).
  "internacoes_por_bairro": {
    "bairros": [
      {"nome": "...", "geometria": "...gado (GeoJSON?) — formato ainda não definido",
       "custo_total": null, "pct_moradores_proprio_municipio": null}
    ]
  }
}
```

## Companheiros (`_*.json`)

| Arquivo | Conteúdo |
|---|---|
| `_metodologia.json` | `{"passos": [...]}` — sobrescreve o texto padrão da página de metodologia para TODOS os municípios do lote. |

Nenhum companheiro é obrigatório nesta versão — na ausência de um, o tema usa
texto padrão embutido (metodologia) ou omite a seção com aviso (demais).
