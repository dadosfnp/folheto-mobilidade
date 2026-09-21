# Folheto Mobilidade

Ficha de Diagnóstico Preliminar de Segurança Viária — folheto institucional
da Frente Nacional de Prefeitas e Prefeitos, para municípios acima de 80 mil
habitantes. Pilotos: **Campinas/SP** e **Montes Claros/MG**.

Motor de geração herdado do [`folheto-ifem`](https://github.com/dadosfnp/folheto-ifem)
(gerador unificado de folhetos FNP) — mesma identidade visual, formato de
página diferente (A4 em vez do quadrado 20×20cm original). Ver
`DESIGN_SYSTEM.md` e `CLAUDE.md` para o histórico completo das decisões.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Fontes oficiais (Barlow Condensed + Inter) — não vêm no git
python tools/baixar_fontes.py

# Configuração local (opcional nesta fase — ver .env.example)
Copy-Item .env.example .env
```

## Gerar um folheto

```powershell
# Listar temas registrados
python python/gerar.py --listar

# Os dois pilotos reais
python python/gerar.py --tema mobilidade --dados data/mobilidade/campinas.json
python python/gerar.py --tema mobilidade --dados data/mobilidade/montes_claros.json

# Exemplo de validação do pipeline (dado transcrito do briefing do projeto,
# NÃO um dado oficial publicável — ver data/mobilidade/SCHEMA.md)
python python/gerar.py --tema mobilidade --dados data/mobilidade/exemplo_fortaleza.json

# Um lote inteiro
python python/gerar.py --tema mobilidade --lote "data/mobilidade/*.json"
```

O PDF sai em `output/FolhetoMobilidade_<Município>_<UF>.pdf`.

## Gerar os JSONs a partir do dado tratado

`data/mobilidade/campinas.json` e `montes_claros.json` não são escritos à
mão — vêm de `data/external/` (planilhas SIM/SIH/SENATRAN já tratadas pela
equipe) via:

```powershell
python tools/dados_tratados_para_json.py                    # os dois pilotos
python tools/dados_tratados_para_json.py --municipio campinas
```

`data/external/` (planilhas agregadas, ~350 MB) e `data/raw/` (extração
original SIH/SIM em parquet, ~6,6 GB) não são versionados em git — cada
máquina mantém sua própria cópia local (ver `.gitignore`). Sem essas
pastas, o script sai com um erro claro listando o que falta. Campos que
essas fontes não cobrem (ranking de causas de morte, mandato do prefeito
atual, custo hospitalar) continuam `null` — ver `CLAUDE.md`, "Pendências".

## Gerar e baixar PDFs pelo navegador

Back-office Django local, só pra equipe da FNP (nunca exposto publicamente
— ver CLAUDE.md, Decisão 4). **Só leitura**: lista os municípios, gera e
baixa o PDF — não edita dado nenhum. Atualizar dado é sempre via
`tools/dados_tratados_para_json.py` ou editando o arquivo diretamente.

```powershell
python manage.py runserver
# abrir http://127.0.0.1:8000/
```

Os avisos que normalmente só apareceriam no console ao gerar (fontes
ausentes, campo faltando) aparecem na tela antes do download. Sem banco de
dados.

## Publicar (PDFs e site)

Site estático de distribuição pública (`docs/`, GitHub Pages) — réplica
adaptada do padrão do [`folheto-ifem`](https://github.com/dadosfnp/folheto-ifem/tree/main/docs).
Sem servidor: os PDFs ficam como assets de uma GitHub Release (repo
`production`, nunca o fork pessoal) e `docs/index.html` só lê um índice
JSON gerado localmente.

```powershell
# 1. Gerar os PDFs reais (ver "Gerar um folheto" acima)
# 2. Subir como assets de uma Release no repo da organização
.\tools\publicar_release.ps1 -Tag v1

# 3. Reindexar a landing
python tools/build_site.py --release-tag v1

# 4. Commitar docs/folhetos.json na main — é o que a página lê em produção
git add docs/folhetos.json
```

`exemplo_fortaleza.json` nunca entra no índice (dado de validação, não
oficial — ver `SCHEMA.md`). Habilitar GitHub Pages
(`dadosfnp/folheto-mobilidade` → Settings → Pages → branch `main`, pasta
`/docs`) é um passo manual, feito uma vez, fora deste repositório.

## Estrutura

```
.
├── CLAUDE.md                   # Contexto do projeto (decisões, pendências, histórico)
├── DESIGN_SYSTEM.md             # Identidade visual (paleta, tipografia, grid, componentes)
├── manage.py                     # CLI do back-office Django (ver "Gerar e baixar PDFs pelo navegador")
├── web/                          # Back-office Django, só leitura — lista/gera/baixa,
│   └── municipios/                # nunca edita dado (chama gerar_um(), ver web/municipios/geracao.py)
├── python/
│   ├── core/                    # Núcleo reusável — herdado do folheto-ifem
│   │   ├── tokens.py             # Cores, dimensões, tamanhos de fonte, A4
│   │   ├── components.py         # Primitivas visuais (KPI, tabela, gráfico de linha…)
│   │   ├── paleta_ranking.py     # Cor por percentil — normal E invertida (mortalidade)
│   │   └── base_folheto.py       # Classe-base FolhetoFNP
│   ├── temas/
│   │   └── mobilidade.py         # Único tema deste repo
│   └── gerar.py                  # CLI unificada
├── tools/
│   ├── baixar_fontes.py
│   ├── verificar_arte.py
│   ├── verificar_texto.py
│   ├── dados_tratados_para_json.py  # data/external/ -> data/mobilidade/<slug>.json
│   ├── build_site.py              # Gera docs/folhetos.json (ver "Publicar")
│   ├── publicar_release.ps1       # Sobe PDFs como assets de GitHub Release
│   └── gerar_preview_landing.py   # Gera docs/preview/*.jpg a partir de um PDF real
├── docs/                          # Site estático de distribuição (GitHub Pages)
│   ├── index.html                  # UI: busca, filtro por UF, ordenação
│   ├── folhetos.json               # Índice gerado — NÃO editar à mão
│   └── preview/                    # Prévias de página (JPEG) — geradas, versionadas
├── data/
│   ├── mobilidade/
│   │   ├── SCHEMA.md              # Contrato dos JSONs de entrada
│   │   ├── campinas.json          # Piloto real
│   │   ├── montes_claros.json     # Piloto real
│   │   └── exemplo_fortaleza.json # Dado de validação do pipeline (não oficial)
│   ├── external/                  # Planilhas SIM/SIH/SENATRAN já tratadas — não versionado
│   └── raw/                       # Extração original SIH/SIM (parquet) — não versionado
├── assets/                       # Logos, padrões decorativos
├── fonts/                        # Barlow Condensed + Inter (não versionado)
└── output/                       # PDFs gerados (não versionado)
```

## Estado do projeto

Ver `CLAUDE.md`, seção "Pendências" — em resumo: **os dois pilotos têm
dado real** (população, frota, mortalidade 2024, série histórica de
mortes, internações 2025 e série histórica de internações). Ainda
pendentes: ranking de causas de morte, mandato do prefeito atual, custo
hospitalar e o mapa por bairro — nenhuma dessas fontes está em
`data/external/`.
