# Assets

Imagens e logos usados pelo folheto. Organizados por subpasta.

## Estrutura

```
assets/
├── logos/
│   └── fnp-logo.png         # Logo oficial FNP (rodapé + capa) — chegou em
│                             # 2026-09-21, ver "Logo oficial FNP" abaixo.
├── padroes/
│   ├── arte0.png             # padrão modular geométrico (faixa mais fina)
│   ├── arte1.png             # padrão modular geométrico (faixa média)
│   └── arte2.png             # padrão modular geométrico (faixa mais alta)
└── capa/
    └── mobilidade-capa.jpg   # arte fixa da capa (mosaico mascarado, ver
        abaixo) — igual pra todo município, mesmo padrão do folheto-ifem.
        Se um dia existir foto real de um piloto específico, o campo
        `_capa_foto` no JSON do município (ver SCHEMA.md) tem prioridade
        sobre este arquivo.
```

## Foto de capa (`capa/mobilidade-capa.jpg`)

Foto genérica de mobilidade urbana (ciclofaixa), sem relação com nenhum
piloto específico — mesmo espírito da capa real do IFEM, que também usa a
MESMA foto de fundo pra qualquer um dos 5.570 municípios (confirmado lendo
o código de lá, `python/temas/ifem.py::_pag_capa`; não é per-município,
apesar de parecer). `draw_mosaico_fotografico`
(`python/core/components.py`) fatiada essa foto numa grade de janelas no
vocabulário modular (§1 do `DESIGN_SYSTEM.md`) — não aparece como
retângulo liso. Redimensionada para ~1600px no lado maior antes de entrar
no repo (o arquivo original tinha 4096×2802, ~6,6 MB — pesado demais pra
um asset versionado e pra embutir em cada PDF gerado).

## Logo oficial FNP (`logos/fnp-logo.png`)

Chegou em 2026-09-21 — o usuário indicou o arquivo `logo-FNP.png`, já usado
em outros projetos FNP (`08-Legislativo FNP`, `04-Radar Brasil`,
`01-IFEM`, `02-Subfinanciados`); movido para o caminho que o código já
esperava (`assets/logos/fnp-logo.png`, nenhuma mudança de código
necessária). 187×69px, PNG com transparência, ~8 KB.

`python/core/components.py::draw_footer` e `draw_capa_padrao` procuram
esse caminho e **não desenham nada** se o arquivo não existir —
degradação intencional (mesmo padrão documentado no `folheto-ifem`, do
qual este motor foi herdado), preservada caso o arquivo seja removido ou
trocado por engano.

## Especificações

- **Logos:** PNG com fundo transparente. O arquivo atual (187×69px) é
  suficiente pro tamanho usado hoje (rodapé ~58×21pt, capa até ~60pt de
  altura) — se o visual sair granulado em impressão de alta resolução,
  trocar por uma versão maior é só substituir o arquivo, nenhum código
  muda.
- **Padrões:** PNG (os 3 arquivos já existem, herdados do folheto-ifem —
  são o "alfabeto modular" da identidade visual da FNP, genérico, não
  específico de nenhum tema).
- **Foto de capa:** se usada, cobre a página inteira (full-bleed) — ver
  `DESIGN_SYSTEM.md` §5.1. Sem foto, a capa cai no alfabeto modular
  soletrando a palavra do tema (`palavra_capa`, ver §5.14).

## Como o código resolve os caminhos

`python/core/tokens.py` define `ASSETS_DIR = ROOT_DIR / "assets"`. Cada tema
referencia explicitamente, nunca hardcoda o caminho:

```python
from core.tokens import ASSETS_DIR
logo = ASSETS_DIR / "logos" / "fnp-logo.png"
```
