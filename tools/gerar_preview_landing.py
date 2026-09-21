"""
Renderiza páginas de um folheto como JPEG para mostrar um modelo — tanto no
site estático (`docs/preview/pagina-N.jpg`) quanto no back-office Django
(`web/municipios/static/municipios/preview/pagina-N.jpg`, mesma imagem,
pra tela ter a mesma seção "Como é o folheto" que o site público). Mesmo
padrão de `dadosfnp/folheto-ifem/tools/gerar_preview_landing.py`, adaptado
para a página A4 retrato deste tema (o folheto-ifem é 20×20cm, quadrado —
aqui recortamos um quadrado a partir do topo de cada página, onde o
conteúdo real vive; a parte de baixo hoje é respiro em branco, ver
CLAUDE.md "Recalibrar espaçamento").

Uso:
    python tools/gerar_preview_landing.py
    python tools/gerar_preview_landing.py --municipio campinas --paginas 1,4,5
"""
import argparse
import io
import sys
from pathlib import Path

try:
    import pymupdf as fitz
except ImportError:
    sys.exit("Falta a dependência 'pymupdf': pip install pymupdf")

try:
    from PIL import Image
except ImportError:
    sys.exit("Falta a dependência 'Pillow': pip install Pillow")

ROOT_DIR = Path(__file__).resolve().parent.parent
DIR_DADOS = ROOT_DIR / "data" / "mobilidade"
OUTPUT_DIR = ROOT_DIR / "output"
OUT_DIRS = (
    ROOT_DIR / "docs" / "preview",
    ROOT_DIR / "web" / "municipios" / "static" / "municipios" / "preview",
)

# Campinas: o piloto com o dado mais completo hoje (ver CLAUDE.md, Decisão 4).
SLUG_PADRAO = "campinas"

# Capa, taxa de mortalidade (a tabela que resume o diagnóstico) e evolução
# das mortes (o gráfico de linha) — mesmo espírito da escolha do folheto-ifem
# (capa + página de dado central + página de gráfico).
PAGINAS_PADRAO = "1,4,5"

# draw_capa_padrao (components.py) desenha o título na faixa inferior (27% da
# altura, a partir de y=0 no sistema de coordenadas do PDF) — que corresponde
# ao FUNDO da imagem renderizada (linha 0 da imagem = topo da página = maior
# y do PDF). Um recorte quadrado a partir do topo pega só o azul sólido, sem
# nenhum texto. As páginas de conteúdo são o oposto: título e tabela/gráfico
# ficam no topo, sobra respiro embaixo (ver CLAUDE.md "Recalibrar
# espaçamento") — recorte do topo é o certo pra essas.
PAGINAS_ANCORA_INFERIOR = {1}

LARGURA_ALVO = 720  # suficiente pra leitura em tela sem inflar o repositório


def _nome_pdf(slug: str) -> Path:
    import json

    caminho_json = DIR_DADOS / f"{slug}.json"
    if not caminho_json.exists():
        sys.exit(f"Município '{slug}' não encontrado em {DIR_DADOS}")
    with caminho_json.open(encoding="utf-8") as f:
        d = json.load(f)
    nome = (d.get("nome") or slug).replace(" ", "_")
    uf = d.get("uf") or ""
    pdf = OUTPUT_DIR / f"FolhetoMobilidade_{nome}_{uf}.pdf"
    if not pdf.exists():
        sys.exit(f"PDF não encontrado em {pdf} — gere-o primeiro "
                  f"(python python/gerar.py --tema mobilidade --dados {caminho_json}).")
    return pdf


def main() -> int:
    ap = argparse.ArgumentParser(description="Gera JPEGs de prévia para o site estático")
    ap.add_argument("--municipio", default=SLUG_PADRAO, help="slug em data/mobilidade/ (ex.: campinas)")
    ap.add_argument("--paginas", default=PAGINAS_PADRAO, help="ex.: 1,4,5")
    args = ap.parse_args()

    pdf_path = _nome_pdf(args.municipio)
    paginas = [int(p.strip()) for p in args.paginas.split(",") if p.strip()]
    print(f"origem: {pdf_path.name}")

    for out_dir in OUT_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)

    gerados = []
    for num in paginas:
        if num < 1 or num > doc.page_count:
            print(f"  [aviso] página {num} fora do intervalo (1-{doc.page_count})", file=sys.stderr)
            continue
        pagina = doc[num - 1]
        escala = LARGURA_ALVO / pagina.rect.width
        pix = pagina.get_pixmap(matrix=fitz.Matrix(escala, escala))
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

        # Recorte quadrado — de baixo pra cima na capa (título vive na faixa
        # inferior), do topo pra baixo nas páginas de conteúdo (ver
        # PAGINAS_ANCORA_INFERIOR acima).
        lado = min(img.width, img.height)
        if num in PAGINAS_ANCORA_INFERIOR:
            img = img.crop((0, img.height - lado, img.width, img.height))
        else:
            img = img.crop((0, 0, img.width, lado))

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85, optimize=True, progressive=True)
        conteudo = buf.getvalue()

        for out_dir in OUT_DIRS:
            destino = out_dir / f"pagina-{num}.jpg"
            destino.write_bytes(conteudo)
        gerados.append((num, img.size, len(conteudo)))
        print(f"  + pagina-{num}.jpg  {img.size[0]}x{img.size[1]}px  {len(conteudo) / 1024:,.0f} KB "
              f"(em {len(OUT_DIRS)} pasta(s))")

    doc.close()

    total = sum(g[2] for g in gerados) * len(OUT_DIRS)
    print(f"\n{len(gerados)} imagem(ns) × {len(OUT_DIRS)} destino(s), {total / 1024:,.0f} KB no total")
    for out_dir in OUT_DIRS:
        print(f"  - {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
