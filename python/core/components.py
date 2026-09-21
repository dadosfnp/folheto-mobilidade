"""
Componentes visuais reusáveis.

Cada função recebe um `canvas` ReportLab e desenha um elemento padronizado
(stripe, KPI, tabela, divisória de seção...). Toda primitiva visual usada
por mais de uma página vive aqui — temas individuais não devem reimplementar.
"""
from io import BytesIO
from reportlab.lib.utils import simpleSplit, ImageReader

from .asset_cache import cached_image
from .tokens import (
    BLUE, BLUE_DARK, BLUE_MID, BLUE_LIGHT, YELLOW, YELLOW_DARK,
    CREAM_DARK, RULE, MUTED, INK, WHITE,
    STRIPE_W, MARGIN, CONTENT_W, ASSETS_DIR,
    FS_EYEBROW, FS_HEADER_FOOTER, FS_BODY, FS_TITLE_DIVISOR,
    FS_HEADLINE, FS_CAPTION, FS_SUBTITLE,
    CARD_RADIUS, CARD_TOP_BAR, ROW_HEIGHT,
    QR_SIZE, QR_FILL_COLOR,
    FNP_Q1, FNP_Q3, FNP_Q5,
    FONT_NUM_BOLD, FONT_NUM_SEMIBOLD, FONT_NUM_REGULAR,
    FONT_TEXTO, FONT_TEXTO_SEMIBOLD, FONT_TEXTO_BOLD,
    STATUS_OK_PCT, STATUS_ALERTA_PCT,
)


# ─── Helper: cor de status por percentual de comparação ──────────────────────

def cor_status_landing(supera_pct: int | None):
    """Cor do quadradinho de status a partir de um percentual "supera X%".
    Thresholds vêm de tokens.STATUS_OK_PCT / STATUS_ALERTA_PCT.
    Assume polaridade "maior é melhor" — para métricas onde menor é melhor
    (ex.: taxa de mortalidade), inverta o percentual antes de chamar."""
    if supera_pct is None:
        return MUTED
    if supera_pct >= STATUS_OK_PCT:
        return FNP_Q5
    if supera_pct >= STATUS_ALERTA_PCT:
        return FNP_Q3
    return FNP_Q1


# ─── Ícones vetoriais (estilo line-art) — Resumo do card ─────────────────────
# Todos com stroke fino e cantos arredondados.

def _line_setup(c, cor, w):
    c.setStrokeColor(cor)
    c.setLineWidth(w)
    c.setLineCap(1)   # round
    c.setLineJoin(1)  # round


def draw_icon_populacao(c, cx, cy, size=14, cor=None):
    """Duas pessoas (silhuetas line-art): cabeça redonda + ombros em arco.
    Pessoa esquerda fica atrás e ligeiramente acima."""
    cor = cor or BLUE_DARK
    sw = max(0.8, size * 0.085)
    _line_setup(c, cor, sw)
    s = size * 0.5
    # Pessoa de trás (esquerda)
    rh = s * 0.34
    cx1, cy1 = cx - s*0.32, cy + s*0.18
    c.circle(cx1, cy1, rh, fill=0, stroke=1)
    p = c.beginPath()
    p.moveTo(cx1 - rh*1.4, cy1 - rh*1.0)
    p.curveTo(cx1 - rh*1.4, cy1 - rh*2.4,
              cx1 + rh*1.4, cy1 - rh*2.4,
              cx1 + rh*1.4, cy1 - rh*1.0)
    c.drawPath(p, fill=0, stroke=1)
    # Pessoa da frente (direita)
    rh2 = s * 0.38
    cx2, cy2 = cx + s*0.28, cy + s*0.04
    c.setFillColor(WHITE)
    c.circle(cx2, cy2, rh2, fill=1, stroke=1)
    p = c.beginPath()
    p.moveTo(cx2 - rh2*1.45, cy2 - rh2*1.1)
    p.curveTo(cx2 - rh2*1.45, cy2 - rh2*2.6,
              cx2 + rh2*1.45, cy2 - rh2*2.6,
              cx2 + rh2*1.45, cy2 - rh2*1.1)
    c.drawPath(p, fill=0, stroke=1)


def draw_icon_receita(c, cx, cy, size=14, cor=None):
    """Cifrão `$` em line-art. Sem círculo externo (estilo limpo do site)."""
    cor = cor or BLUE_DARK
    c.setFillColor(cor)
    c.setFont(F(FONT_NUM_BOLD), size * 1.05)
    c.drawCentredString(cx, cy - size * 0.30, "$")


def draw_icon_sus(c, cx, cy, size=14, cor=None):
    """Linha de batimento cardíaco (heartbeat). Estilo monitor de pulso."""
    cor = cor or BLUE_DARK
    sw = max(0.9, size * 0.10)
    _line_setup(c, cor, sw)
    s = size * 0.50
    # Curva tipo: __/\__/\__
    p = c.beginPath()
    p.moveTo(cx - s,           cy)
    p.lineTo(cx - s * 0.55,    cy)
    p.lineTo(cx - s * 0.30,    cy + s * 0.55)
    p.lineTo(cx - s * 0.05,    cy - s * 0.55)
    p.lineTo(cx + s * 0.18,    cy + s * 0.18)
    p.lineTo(cx + s * 0.40,    cy)
    p.lineTo(cx + s,           cy)
    c.drawPath(p, fill=0, stroke=1)


def draw_icon_cadunico(c, cx, cy, size=14, cor=None):
    """Documento line-art: retângulo com canto dobrado + linhas de texto."""
    cor = cor or BLUE_DARK
    sw = max(0.9, size * 0.09)
    _line_setup(c, cor, sw)
    s = size * 0.48
    x0, y0 = cx - s * 0.75, cy - s
    x1, y1 = cx + s * 0.75, cy + s
    fold = s * 0.32
    # Contorno com canto dobrado superior-direito
    p = c.beginPath()
    p.moveTo(x0, y0)
    p.lineTo(x0, y1)
    p.lineTo(x1 - fold, y1)
    p.lineTo(x1, y1 - fold)
    p.lineTo(x1, y0)
    p.close()
    c.setFillColor(WHITE)
    c.drawPath(p, fill=1, stroke=1)
    # Dobra do canto (triangulinho)
    p2 = c.beginPath()
    p2.moveTo(x1 - fold, y1)
    p2.lineTo(x1 - fold, y1 - fold)
    p2.lineTo(x1, y1 - fold)
    c.drawPath(p2, fill=0, stroke=1)
    # 3 linhas internas (texto fictício)
    for frac in (0.35, 0.05, -0.30):
        c.line(x0 + s*0.25, cy + s*frac, x1 - s*0.25, cy + s*frac)


def draw_icon_grafico(c, cx, cy, size=14, cor=None):
    """Gráfico de linha ascendente com pontinhos nos vértices (estilo site)."""
    cor = cor or BLUE_DARK
    sw = max(0.9, size * 0.10)
    _line_setup(c, cor, sw)
    s = size * 0.50
    # Pontos do polyline (asc) — 4 vértices, 2 sobem 1 desce 1 sobe
    pts = [
        (cx - s,        cy - s*0.55),
        (cx - s*0.30,   cy + s*0.05),
        (cx + s*0.20,   cy - s*0.20),
        (cx + s,        cy + s*0.55),
    ]
    p = c.beginPath()
    p.moveTo(*pts[0])
    for px, py in pts[1:]:
        p.lineTo(px, py)
    c.drawPath(p, fill=0, stroke=1)
    # Bolinhas nos vértices
    c.setFillColor(cor)
    for px, py in pts:
        c.circle(px, py, sw * 1.6, fill=1, stroke=0)


def _fmt_money_br(v: float) -> str:
    """Formata R$ no padrão da landing: separador BR de milhar.
    Valores < R$ 10 ganham 2 decimais (ex: R$ 0,50) para evitar "R$ 0" enganoso.
    """
    if v is None:
        return "n/d"
    if abs(v) < 10 and v != 0:
        return "R$ " + f"{v:.2f}".replace(".", ",")
    return "R$ " + f"{int(round(v)):,}".replace(",", ".")
from .fonts import F


# ─── Estrutura: stripe + numeração + header + footer ─────────────────────────

def draw_stripe(c, page_w, page_h, lado: str = "dir", cor=None):
    """Borda lateral colorida. lado ∈ {'dir', 'esq'}.
    `cor` opcional: quando o tema passa a cor do quintil do município,
    o stripe inteiro reflete o status fiscal (verde/amarelo/vermelho/azul)."""
    c.setFillColor(cor or BLUE)
    x = page_w - STRIPE_W if lado == "dir" else 0
    c.rect(x, 0, STRIPE_W, page_h, fill=1, stroke=0)


def draw_page_number(c, page_w, n: int, lado: str = "dir",
                     lettermark_img: str | None = None):
    """Número de página + lettermark vertical opcional (imagem) no stripe.
    `lettermark_img`: caminho de uma imagem PNG branca-com-transparência já
    pré-processada e rotacionada para a lateral (ratio ~120/400 = 0.30),
    desenhada por cima do número. Nenhum tema é assumido aqui — cada tema
    passa o próprio asset, se tiver."""
    cx = page_w - STRIPE_W / 2 if lado == "dir" else STRIPE_W / 2

    # Número
    c.setFillColor(WHITE)
    c.setFont(F(FONT_NUM_BOLD), 11)
    c.drawCentredString(cx, 14, f"{n:02d}")

    if lettermark_img:
        from pathlib import Path
        img_path = Path(lettermark_img)
        if img_path.exists():
            # Stripe = 20pt wide. Largura útil = 14pt (centro), altura ≈ 46pt.
            img_w = 14
            img_h = 46
            c.drawImage(str(img_path),
                        cx - img_w / 2, 32,
                        width=img_w, height=img_h,
                        preserveAspectRatio=True, mask="auto")


def draw_header(c, page_h, titulo_publicacao: str):
    """Cabeçalho discreto com o nome da publicação."""
    c.setFillColor(MUTED)
    c.setFont(F(FONT_NUM_SEMIBOLD), FS_HEADER_FOOTER)
    c.drawString(STRIPE_W + MARGIN, page_h - 20, titulo_publicacao.upper())


def draw_footer(c, page_w, label_secao: str):
    """Rodapé: label da seção à esquerda + logo FNP à direita."""
    c.setFillColor(MUTED)
    c.setFont(F(FONT_NUM_SEMIBOLD), FS_HEADER_FOOTER)
    c.drawString(STRIPE_W + MARGIN, 16, label_secao.upper())

    fnp_path = ASSETS_DIR / "logos" / "fnp-logo.png"
    if fnp_path.exists():
        c.drawImage(
            str(fnp_path),
            page_w - STRIPE_W - MARGIN - 60, 8,
            width=58, height=21,
            preserveAspectRatio=True, mask="auto",
        )


# ─── Texto: eyebrow, título, corpo ───────────────────────────────────────────

def draw_eyebrow(c, texto: str, x: float, y: float, color=BLUE):
    c.setFillColor(color)
    c.setFont(F(FONT_NUM_SEMIBOLD), FS_EYEBROW)
    c.drawString(x, y, texto.upper())


def draw_titulo(c, texto: str, x: float, y: float, size: int = 26, color=BLUE_DARK,
                max_width: float | None = CONTENT_W):
    """Suporta '\\n' como quebra manual de linha (o chamador decide onde
    quebrar — isto NÃO reflui automaticamente uma linha longa em várias).
    Encolhe a fonte se a linha mais larga estourar `max_width` (padrão:
    largura de conteúdo da página) — sem isso, um título sem '\\n' manual
    que passe da largura simplesmente sai da página, sem aviso nenhum.
    Passe `max_width=None` para desligar (ex.: títulos já garantidamente
    curtos, como capítulos de 1-2 palavras)."""
    c.setFillColor(color)
    font = F(FONT_NUM_BOLD)
    linhas = texto.split("\n")
    if max_width:
        maior = max(c.stringWidth(l, font, size) for l in linhas)
        while maior > max_width and size > 12:
            size -= 1
            maior = max(c.stringWidth(l, font, size) for l in linhas)
    c.setFont(font, size)
    for i, linha in enumerate(linhas):
        c.drawString(x, y - i * (size * 0.95), linha)


def draw_body(c, texto: str, x: float, y: float, width: float,
              size: float = FS_BODY, color=INK) -> float:
    """Texto corrido com quebra automática. Retorna y final (após última linha)."""
    c.setFillColor(color)
    font = F(FONT_TEXTO)
    c.setFont(font, size)
    linhas = simpleSplit(texto, font, size, width)
    for i, linha in enumerate(linhas):
        c.drawString(x, y - i * (size * 1.5), linha)
    return y - len(linhas) * (size * 1.5)


def draw_caption(c, texto: str, x: float, y: float):
    """Fonte/elaboração. Sempre que houver gráfico ou tabela."""
    c.setFillColor(MUTED)
    c.setFont(F(FONT_TEXTO), FS_CAPTION)
    c.drawString(x, y, texto)


# ─── Componentes de bloco ────────────────────────────────────────────────────

def draw_kpi_box(c, label: str, valor, unidade: str,
                 x: float, y: float, w: float = 110, h: float = 58,
                 icone=None, upper: bool = True):
    """Card de KPI com borda esquerda azul. Layout: ícone opcional + label no
    topo, valor grande embaixo (alinhado), unidade em fonte menor à direita
    do valor com gap. `icone` deve ser uma função(c, cx, cy, size, cor).
    `upper` força ou não o label em CAIXA ALTA."""
    c.setFillColor(WHITE)
    c.roundRect(x, y, w, h, CARD_RADIUS, fill=1, stroke=0)
    c.setFillColor(BLUE_MID)
    c.rect(x, y, 4, h, fill=1, stroke=0)

    pad_l = 12
    label_y = y + h - 16
    if icone:
        icone(c, x + pad_l + 8, label_y + 6, size=15)
        label_x = x + pad_l + 22
    else:
        label_x = x + pad_l
    c.setFillColor(BLUE_DARK if not upper else MUTED)
    label_inner_w = (x + w - pad_l) - label_x  # largura disponível até a borda direita do card
    label_txt = label.upper() if upper else label
    label_font = F(FONT_TEXTO) if upper else F(FONT_TEXTO_SEMIBOLD)
    label_size = 8.5 if upper else 10
    while c.stringWidth(label_txt, label_font, label_size) > label_inner_w and label_size > 6:
        label_size -= 0.5
    c.setFont(label_font, label_size)
    c.drawString(label_x, label_y, label_txt)

    valor_str = str(valor)
    unidade_font = F(FONT_TEXTO)
    unidade_size = 9
    unidade_w = c.stringWidth(unidade, unidade_font, unidade_size) + 4 if unidade else 0

    # Reduz a fonte do valor automaticamente até caber, já reservando o
    # espaço real da unidade (não um valor fixo) — sem isso, um valor que só
    # cabe sozinho empurra a unidade para fora do card (ela é desenhada
    # depois, sem clipping automático do ReportLab).
    valor_size = FS_HEADLINE
    valor_font = F(FONT_NUM_BOLD)
    inner_w = w - pad_l * 2
    while (c.stringWidth(valor_str, valor_font, valor_size) + unidade_w > inner_w
           and valor_size > 12):
        valor_size -= 1
    valor_w = c.stringWidth(valor_str, valor_font, valor_size)

    c.setFillColor(BLUE_DARK)
    c.setFont(valor_font, valor_size)
    valor_y = y + 14  # baseline com mais espaço do fundo
    c.drawString(x + pad_l, valor_y, valor_str)

    # Mesmo no tamanho mínimo, valor + unidade podem não caber (ex.: valor
    # já grande por si só). Preferir omitir a unidade a sobrepor o card
    # vizinho — degradação silenciosa aqui é melhor que um bug visual.
    if unidade and (valor_w + unidade_w) <= inner_w:
        c.setFont(unidade_font, unidade_size)
        c.setFillColor(MUTED)
        c.drawString(x + pad_l + valor_w + 4, valor_y + 2, unidade)


def draw_ranking_item(c, pos: int, label: str, total: int,
                      x: float, y: float, w: float = 300):
    """Linha de ranking: posição grande em amarelo + label + 'de N'."""
    c.setFillColor(WHITE)
    c.rect(x, y, w, 30, fill=1, stroke=0)
    c.setStrokeColor(RULE)
    c.rect(x, y, w, 30, fill=0, stroke=1)

    c.setFillColor(YELLOW_DARK)
    pos_font = F(FONT_NUM_BOLD)
    pos_size = 20
    c.setFont(pos_font, pos_size)
    pos_str = f"{pos:,}º".replace(",", ".")
    c.drawString(x + 8, y + 8, pos_str)
    pos_w = c.stringWidth(pos_str, pos_font, pos_size)

    c.setFillColor(INK)
    c.setFont(F(FONT_TEXTO), 9.5)
    c.drawString(x + 16 + pos_w, y + 12, label)

    c.setFillColor(MUTED)
    c.setFont(F(FONT_TEXTO), 8)
    c.drawRightString(x + w - 8, y + 12, f"de {total:,}".replace(",", "."))


def draw_destaque_box(c, eyebrow: str, texto: str,
                      x: float, y: float, w: float, h: float = 60,
                      font_size: float = 16):
    """Box azul com eyebrow no topo + texto abaixo. Quebra automática se necessário."""
    c.setFillColor(BLUE)
    c.roundRect(x, y, w, h, CARD_RADIUS, fill=1, stroke=0)
    c.setFillColor(BLUE_MID)
    c.rect(x, y, 4, h, fill=1, stroke=0)

    # Eyebrow no topo do box (baseline a 10pt do topo).
    eyebrow_y = y + h - 12
    c.setFillColor(YELLOW)
    c.setFont(F(FONT_NUM_SEMIBOLD), FS_EYEBROW)
    c.drawString(x + 10, eyebrow_y, eyebrow.upper())

    # Texto abaixo do eyebrow, com gap de 4pt. Reduz fonte se passar de 2 linhas.
    c.setFillColor(WHITE)
    font = F(FONT_NUM_BOLD)
    inner_w = w - 20
    while True:
        linhas = simpleSplit(texto, font, font_size, inner_w)
        if len(linhas) <= 2 or font_size <= 11:
            break
        font_size -= 1
    c.setFont(font, font_size)
    text_top_y = eyebrow_y - 6 - font_size
    for i, linha in enumerate(linhas[:2]):
        c.drawString(x + 10, text_top_y - i * (font_size * 1.1), linha)


def draw_card_topbar(c, titulo: str, descricao: str,
                     x: float, y: float, w: float, h: float,
                     top_color=BLUE):
    """Card branco com barra colorida no topo. Usado em listas de pontos."""
    c.setFillColor(WHITE)
    c.roundRect(x, y, w, h, CARD_RADIUS, fill=1, stroke=0)
    c.setStrokeColor(RULE)
    c.roundRect(x, y, w, h, CARD_RADIUS, fill=0, stroke=1)

    c.setFillColor(top_color)
    c.rect(x, y + h - CARD_TOP_BAR, w, CARD_TOP_BAR, fill=1, stroke=0)

    c.setFillColor(BLUE_DARK)
    c.setFont(F(FONT_NUM_BOLD), FS_SUBTITLE)
    c.drawString(x + 10, y + h - 20, titulo.upper())

    draw_body(c, descricao, x + 10, y + h - 36, w - 20, size=FS_BODY)


def draw_table(c, headers: list[str], rows: list[list[str]],
               col_widths: list[float], x: float, y: float,
               row_h: float = ROW_HEIGHT, highlight_col: int = 1):
    """
    Tabela padrão FNP: header azul + zebra creme.
    `highlight_col` recebe destaque BLUE_DARK SemiBold; demais ficam MUTED Regular.
    Retorna y final (após última linha).
    """
    total_w = sum(col_widths)

    # Header
    c.setFillColor(BLUE)
    c.rect(x, y - row_h, total_w, row_h, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont(F(FONT_NUM_SEMIBOLD), FS_EYEBROW)
    cx = x
    for i, h in enumerate(headers):
        if i == 0:
            c.drawString(cx + 4, y - 13, h)
        else:
            c.drawRightString(cx + col_widths[i] - 4, y - 13, h)
        cx += col_widths[i]
    y -= row_h

    # Linhas
    for ri, row in enumerate(rows):
        bg = WHITE if ri % 2 == 0 else CREAM_DARK
        c.setFillColor(bg)
        c.rect(x, y - row_h, total_w, row_h, fill=1, stroke=0)
        c.setStrokeColor(RULE)
        c.line(x, y - row_h, x + total_w, y - row_h)

        cx = x
        for i, v in enumerate(row):
            if i == 0:
                c.setFillColor(INK)
                c.setFont(F(FONT_TEXTO), 8)
                c.drawString(cx + 4, y - 13, str(v))
            elif i == highlight_col:
                c.setFillColor(BLUE_DARK)
                c.setFont(F(FONT_TEXTO_SEMIBOLD), 8)
                c.drawRightString(cx + col_widths[i] - 4, y - 13, str(v))
            else:
                c.setFillColor(MUTED)
                c.setFont(F(FONT_TEXTO), 8)
                c.drawRightString(cx + col_widths[i] - 4, y - 13, str(v))
            cx += col_widths[i]
        y -= row_h

    return y


def draw_stacked_bar(c, segmentos: list[dict], x: float, y: float,
                     w: float, h: float = 32,
                     cores=(BLUE, BLUE_MID, YELLOW, YELLOW_DARK)):
    """
    Barra empilhada horizontal. Segmentos: [{'pct': float, 'categoria': str, ...}, ...].
    Retorna y abaixo da barra (já com 10pt de respiro).
    """
    total = sum(s["pct"] for s in segmentos)
    cur_x = x
    for i, seg in enumerate(segmentos):
        seg_w = w * (seg["pct"] / total)
        c.setFillColor(cores[i % len(cores)])
        c.rect(cur_x, y - h, seg_w, h, fill=1, stroke=0)
        if seg_w > 30:
            c.setFillColor(WHITE if i < 2 else BLUE_DARK)
            c.setFont(F(FONT_TEXTO), 7)
            c.drawCentredString(cur_x + seg_w / 2, y - h / 2 - 3, f"{seg['pct']:.1f}%")
        cur_x += seg_w
    return y - h - 10


# ─── Páginas-padrão completas ────────────────────────────────────────────────

def draw_section_divider(c, page_w, page_h, capitulo: str, titulo: str,
                         subtitulo: str, n_pagina: int, lado: str = "esq"):
    """Página divisória de seção: fundo azul cheio + capítulo grande."""
    c.setFillColor(BLUE)
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

    # Acento sutil: quarto de círculo translúcido no canto
    c.setFillColor(WHITE)
    c.setFillAlpha(0.08)
    c.circle(page_w if lado == "esq" else 0, 0, 300, fill=1, stroke=0)
    c.setFillAlpha(1.0)

    draw_stripe(c, page_w, page_h, lado)
    draw_page_number(c, page_w, n_pagina, lado)

    x = STRIPE_W + MARGIN if lado == "esq" else MARGIN
    y = page_h / 2 + 60

    c.setFillColor(YELLOW)
    c.setFont(F(FONT_NUM_SEMIBOLD), FS_EYEBROW)
    c.drawString(x, y + 55, capitulo.upper())

    c.setFillColor(WHITE)
    c.setFont(F(FONT_NUM_BOLD), FS_TITLE_DIVISOR)
    for i, linha in enumerate(titulo.split("\n")):
        c.drawString(x, y - i * (FS_TITLE_DIVISOR * 0.95), linha)

    c.setFillColor(BLUE_LIGHT)
    c.setFont(F(FONT_TEXTO), 10)
    c.drawString(x, y - 82, subtitulo)


def draw_qr_page(c, page_w, page_h, url: str, n_pagina: int,
                 lado: str = "esq", imagem_fundo: str | None = None):
    """Última página: imagem de fundo opcional + QR + URL."""
    if imagem_fundo:
        from pathlib import Path
        img_path = Path(imagem_fundo)
        if img_path.exists():
            c.drawImage(
                str(img_path), STRIPE_W if lado == "esq" else 0, 0,
                width=page_w - STRIPE_W, height=page_h,
                preserveAspectRatio=False, mask="auto",
            )
        else:
            c.setFillColor(BLUE_DARK)
            c.rect(0, 0, page_w, page_h, fill=1, stroke=0)
    else:
        c.setFillColor(BLUE_DARK)
        c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

    # QR real
    try:
        import qrcode as qr_lib
        qr = qr_lib.QRCode(version=1, box_size=4, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color=QR_FILL_COLOR, back_color="white")
        buf = BytesIO()
        qr_img.save(buf, format="PNG")
        buf.seek(0)
        c.drawImage(
            ImageReader(buf),
            page_w / 2 - QR_SIZE / 2, page_h / 2 - QR_SIZE / 2,
            width=QR_SIZE, height=QR_SIZE,
        )
    except ImportError:
        # qrcode não instalado: mantém fundo limpo (placeholder textual).
        c.setFillColor(WHITE)
        c.setFont(F(FONT_NUM_BOLD), 12)
        c.drawCentredString(page_w / 2, page_h / 2, url)

    # URL embaixo do QR
    c.setFillColor(YELLOW)
    c.setFont(F(FONT_TEXTO_SEMIBOLD), 9)
    c.drawCentredString(page_w / 2, page_h / 2 - QR_SIZE / 2 - 18, f"Acesse  {url}")

    draw_stripe(c, page_w, page_h, lado)
    draw_page_number(c, page_w, n_pagina, lado)


def draw_capa_padrao(c, page_w, page_h, *,
                     municipio_nome: str,
                     eyebrow_capa: str = "",
                     foto_path: str | None = None,
                     logo_path: str | None = None,
                     lado: str = "dir",
                     destaques: list[tuple[str, int | None, int | None]] | None = None,
                     palavra_capa: str | None = None,
                     palavra_mosaico: str | None = None,
                     palavra_stripe: str | None = None):
    """Capa padrão FNP, sem depender de nenhuma arte pré-composta de tema:
    fundo branco (ver DESIGN_SYSTEM.md — corrigido de bege em 2026-09-21) +
    foto full-bleed no topo se `foto_path` existir (com `palavra_mosaico`
    soletrada dentro da própria grade do mosaico, ver §5.15), senão
    `palavra_capa` desenhada no alfabeto modular (`draw_alfabeto_modular_
    palavra`) no lugar onde o IFEM tem o mosaico fotográfico. Faixa inferior (~27% da altura)
    no MESMO layout da capa real do IFEM (`python/temas/ifem.py::_pag_capa`
    via `core/capa.py` de lá, confirmado lendo o código — ver CLAUDE.md
    Decisão 5): logo à esquerda, barra separadora vertical, e à direita um
    eyebrow pequeno + nome do município grande + até 2 linhas de ranking.
    Ver DESIGN_SYSTEM.md §5.1.

    `destaques`: até 2 estatísticas de posição pra mostrar na capa, cada
    uma `(rotulo, posicao, total)` — renderizadas como texto ("RÓTULO" +
    posição colorida + "de N municípios"), não mais selos circulares
    (mudou em 2026-09-21 pra bater com o layout real do IFEM). Item com
    `posicao`/`total` ausente é pulado em silêncio (não é um dado
    obrigatório do folheto, só um destaque a mais quando existe).

    `palavra_stripe`: soletra a palavra verticalmente dentro do stripe
    lateral (§5.16) — mesmo lettermark que o IFEM tem em toda página."""
    from pathlib import Path

    faixa_h = page_h * 0.27

    c.setFillColor(WHITE)
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

    foto = Path(foto_path) if foto_path else None
    if foto and foto.exists():
        # Mosaico mascarado pelo vocabulário modular — não a foto lisa (ver
        # DESIGN_SYSTEM.md §5.1 e §5.15, mesma técnica da capa real do IFEM).
        # `palavra_mosaico` soletra dentro do próprio mosaico (mesma célula,
        # preenchida pela mesma foto) — não é um selo por cima.
        draw_mosaico_fotografico(c, foto, page_w, faixa_h, page_h,
                                 palavra_mosaico=palavra_mosaico,
                                 margem_direita=STRIPE_W if lado == "dir" else 0)
    elif palavra_capa:
        # Sem foto real do município (nenhum piloto tem hoje — ver
        # assets/README.md): o alfabeto modular soletrando a palavra do
        # tema ocupa o lugar do mosaico fotográfico do IFEM — mesmo
        # vocabulário (DESIGN_SYSTEM.md §1), sem inventar fotografia que
        # não existe. Ver CLAUDE.md Decisão 5.
        max_w_palavra = page_w - STRIPE_W - MARGIN * 2
        # Mira ~80% da largura disponível (logotipo dominante, não um
        # esboço pequeno perdido no branco) — coeficiente calculado a
        # partir de modulo=1 porque a largura é linear em `modulo` (o gap
        # também escala com ele), então dá pra resolver direto sem laço.
        coef = largura_alfabeto_modular_palavra(palavra_capa, 1.0)
        modulo = min(90.0, (max_w_palavra * 0.8) / coef) if coef else 46.0
        largura = largura_alfabeto_modular_palavra(palavra_capa, modulo)
        px = (page_w - largura) / 2
        py = faixa_h + (page_h - faixa_h) / 2 - modulo
        draw_alfabeto_modular_palavra(c, palavra_capa, px, py, modulo)

    # Fio separador entre o topo (foto ou alfabeto modular) e a faixa de
    # informação — mesmo contraste "banda clara sobre topo" do folheto-ifem
    # (capa.py, PNG pré-composto foto+banda branca — ver CLAUDE.md Decisão 5).
    c.setStrokeColor(RULE)
    c.setLineWidth(0.75)
    c.line(0, faixa_h, page_w, faixa_h)

    content_x0 = STRIPE_W + MARGIN if lado == "esq" else MARGIN
    content_x1 = (page_w - MARGIN) if lado == "esq" else (page_w - STRIPE_W - MARGIN)
    content_w = content_x1 - content_x0

    band_top = faixa_h - 26
    band_bottom = 24

    # Logo FNP à esquerda, centralizada verticalmente na faixa — mesma
    # posição relativa da logo IFEM na capa real (core/capa.py de lá:
    # ifem_cx = page_w*0.24). Sem logo (ainda não existe neste repo, ver
    # assets/README.md), o espaço fica em branco — degradação intencional.
    logo = Path(logo_path) if logo_path else None
    logo_cx = content_x0 + content_w * 0.20
    if logo and logo.exists():
        logo_h = min(60.0, (band_top - band_bottom) * 0.75)
        logo_w = logo_h * 2.6  # proporção aproximada do wordmark FNP horizontal
        logo_cy = (band_top + band_bottom) / 2
        c.drawImage(str(logo), logo_cx - logo_w / 2, logo_cy - logo_h / 2,
                    width=logo_w, height=logo_h,
                    preserveAspectRatio=True, mask="auto")

    # Barra separadora vertical entre a logo e o texto — mesma posição
    # relativa da capa real do IFEM (separador em page_w*0.48 lá).
    separador_x = content_x0 + content_w * 0.42
    c.setStrokeColor(RULE)
    c.setLineWidth(0.75)
    c.line(separador_x, band_bottom, separador_x, band_top)

    text_x = content_x0 + content_w * 0.48
    text_w = content_x1 - text_x

    # Nome do município — grande, encolhe se não couber na coluna de texto.
    # Calculado antes de desenhar (só a fonte, não o desenho em si) porque
    # a altura do bloco de texto inteiro precisa ser conhecida ANTES de
    # decidir onde começar a desenhar (ver centralização abaixo).
    nome_size = 20.0
    font_nome = F(FONT_NUM_BOLD)
    while c.stringWidth(municipio_nome, font_nome, nome_size) > text_w and nome_size > 12:
        nome_size -= 1

    itens = [d for d in (destaques or []) if d[1] is not None and d[2]][:2]

    # Bloco de texto centralizado na MESMA linha média da logo — sem isso,
    # o texto (mais curto que a faixa toda) fica "grudado" no topo mesmo
    # com a logo bem mais alta e centralizada, lendo como desalinhado
    # (bug real, reportado pelo usuário no primeiro PDF com esse layout).
    bloco_h = (17 if eyebrow_capa else 0) + (nome_size + 16) + 36 * len(itens)
    logo_cy_calc = (band_top + band_bottom) / 2
    y = min(band_top, logo_cy_calc + bloco_h / 2)

    if eyebrow_capa:
        c.setFillColor(MUTED)
        c.setFont(F(FONT_NUM_SEMIBOLD), FS_EYEBROW)
        c.drawString(text_x, y, eyebrow_capa.upper())
        y -= 17

    c.setFillColor(BLUE_DARK)
    c.setFont(font_nome, nome_size)
    c.drawString(text_x, y, municipio_nome)
    y -= nome_size + 16

    # Destaques (opcional) — texto "RÓTULO" + posição colorida + "de N
    # municípios", mesmo formato "RANKING POR X" da capa real do IFEM (não
    # mais selo circular).
    if itens:
        from .paleta_ranking import cor_por_percentil
        for rotulo, pos, tot in itens:
            c.setFillColor(MUTED)
            c.setFont(F(FONT_TEXTO_SEMIBOLD), 7.5)
            c.drawString(text_x, y, rotulo.upper())
            y -= 13
            pos_str = f"{pos:,}ª".replace(",", ".")
            c.setFillColor(cor_por_percentil(pos, tot))
            c.setFont(F(FONT_NUM_BOLD), 14)
            c.drawString(text_x, y, pos_str)
            pos_w = c.stringWidth(pos_str, F(FONT_NUM_BOLD), 14)
            c.setFillColor(MUTED)
            c.setFont(F(FONT_TEXTO), 9)
            c.drawString(text_x + pos_w + 6, y + 1,
                        f"de {tot:,}".replace(",", ".") + " municípios")
            y -= 23

    draw_stripe(c, page_w, page_h, lado)
    draw_page_number(c, page_w, 1, lado)
    if palavra_stripe:
        draw_lettermark_stripe(c, palavra_stripe, page_w, page_h, lado)


# ─── Cards estilo landing IFEM (categoria + sub-cards aninhados) ─────────────

def draw_categoria_card(c, *, x: float, y_top: float, w: float,
                        titulo: str,
                        municipio_nome: str,
                        supera_pct: int | None,
                        valor_per_capita: float,
                        media_nacional: float | None,
                        size: str = "full") -> float:
    """Card estilo landing IFEM: quadradinho de status + título + frase
    "supera X% dos municípios" + duas caixas (Valor por Habitante / Média).

    Tamanhos:
      - size="full":    altura 100pt (KPIs grandes, fonte 12-16pt)
      - size="compact": altura  80pt (KPIs menores, para sub-cards aninhados)

    Retorna a coordenada Y abaixo do card (y_top - altura - 6pt de respiro).
    """
    if size == "compact":
        h = 78
        kpi_h = 28
        title_size = 11
        frase_size = 9
        valor_size = 13
        label_size = 6
        pad_t_ext = 10
    else:
        h = 96
        kpi_h = 40
        title_size = 13
        frase_size = 10.5
        valor_size = 17
        label_size = 7
        pad_t_ext = 12

    y_bot = y_top - h

    # Fundo do card
    c.setFillColor(WHITE)
    c.roundRect(x, y_bot, w, h, CARD_RADIUS, fill=1, stroke=0)
    c.setStrokeColor(RULE)
    c.setLineWidth(0.6)
    c.roundRect(x, y_bot, w, h, CARD_RADIUS, fill=0, stroke=1)

    # Header: quadradinho colorido + título
    cor = cor_status_landing(supera_pct)
    pad_l = 12
    pad_t = pad_t_ext
    box_size = 9
    box_x = x + pad_l
    box_y = y_top - pad_t - box_size
    c.setFillColor(cor)
    c.rect(box_x, box_y, box_size, box_size, fill=1, stroke=0)

    # Título
    c.setFillColor(BLUE_DARK)
    c.setFont(F(FONT_NUM_BOLD), title_size)
    c.drawString(box_x + box_size + 7, box_y + 1, titulo)

    # Frase "Supera X% dos municípios" (colorizado, sem nome do município)
    frase_y = box_y - 14
    if supera_pct is not None:
        verbo_txt = ("Supera apenas " if supera_pct < 60 else "Supera ") + f"{supera_pct}%"
        c.setFillColor(cor)
        c.setFont(F(FONT_TEXTO_SEMIBOLD), frase_size)
        c.drawString(x + pad_l, frase_y, verbo_txt)
        w_verbo = c.stringWidth(verbo_txt, F(FONT_TEXTO_SEMIBOLD), frase_size)

        c.setFillColor(INK)
        c.setFont(F(FONT_TEXTO), frase_size)
        c.drawString(x + pad_l + w_verbo, frase_y, " dos municípios")

    # Duas caixinhas inferiores: VALOR POR HABITANTE | MÉDIA DOS MUNICÍPIOS (NACIONAL)
    kpi_y = y_bot + 8
    gap = 8
    kpi_w = (w - pad_l * 2 - gap) / 2

    def _kpi(kx, label, valor):
        c.setFillColor(CREAM_DARK)
        c.roundRect(kx, kpi_y, kpi_w, kpi_h, 2, fill=1, stroke=0)
        c.setFillColor(MUTED)
        c.setFont(F(FONT_TEXTO), label_size)
        c.drawCentredString(kx + kpi_w / 2, kpi_y + kpi_h - 11, label.upper())
        c.setFillColor(BLUE_DARK)
        c.setFont(F(FONT_NUM_BOLD), valor_size)
        c.drawCentredString(kx + kpi_w / 2, kpi_y + 6, valor)

    # Labels: no card compact (sub) usamos rótulo curto pra não estourar a largura.
    label_media = "Média nacional" if size == "compact" else "Média dos municípios (nacional)"
    _kpi(x + pad_l,                "Valor por habitante", _fmt_money_br(valor_per_capita))
    _kpi(x + pad_l + kpi_w + gap,  label_media,           _fmt_money_br(media_nacional))

    return y_bot - 4


def draw_categoria_bloco(c, *, x: float, y_top: float, w: float,
                          mae_titulo: str,
                          mae_supera_pct: int | None,
                          municipio_nome: str,
                          mae_per_capita: float,
                          mae_media: float | None,
                          filhos: list[dict]) -> float:
    """Bloco da página 6: card-mãe (compact) + subcards filhos em 2 colunas
    abaixo. Cada filho é um dict com keys:
      {titulo, supera_pct, per_capita, media}

    Retorna y abaixo do bloco completo.
    """
    y_cur = draw_categoria_card(
        c, x=x, y_top=y_top, w=w,
        titulo=mae_titulo,
        municipio_nome=municipio_nome,
        supera_pct=mae_supera_pct,
        valor_per_capita=mae_per_capita,
        media_nacional=mae_media,
        size="compact",
    )
    if not filhos:
        return y_cur

    gap = 5
    sub_w = (w - gap) / 2
    SUB_H = 78
    n = len(filhos)
    # Se sobrar um filho ímpar na última linha, ele ocupa a largura toda
    # (evita um card "órfão" pequeno num canto).
    ultimo_full = (n % 2) == 1
    rows = (n + 1) // 2
    for i, f in enumerate(filhos):
        eh_ultimo_impar = ultimo_full and i == n - 1
        if eh_ultimo_impar:
            sx = x
            cw = w
            sy = y_cur - (rows - 1) * (SUB_H + gap)
        else:
            col, row = i % 2, i // 2
            sx = x + col * (sub_w + gap)
            cw = sub_w
            sy = y_cur - row * (SUB_H + gap)
        draw_categoria_card(
            c, x=sx, y_top=sy, w=cw,
            titulo=f["titulo"],
            municipio_nome=municipio_nome,
            supera_pct=f.get("supera_pct"),
            valor_per_capita=f["per_capita"],
            media_nacional=f.get("media"),
            size="compact",
        )
    return y_cur - rows * (SUB_H + gap) - 4


# ─── Gráfico de linha (série histórica multi-categoria) ──────────────────────

def draw_line_chart(c, *, series: list[dict], categorias: list,
                    x: float, y: float, w: float, h: float,
                    y_max: float | None = None, y_min: float = 0,
                    n_linhas_grade: int = 4,
                    faixa_destaque: tuple | None = None,
                    faixa_label: str | None = None,
                    legenda: bool = True) -> float:
    """
    Gráfico de linha simples, sem dependência externa (só ReportLab).

    `series`: [{"nome": str, "valores": list[float], "cor": Color}, ...] —
    todas as listas de `valores` devem ter o mesmo tamanho de `categorias`.
    `categorias`: rótulos do eixo X (ex.: anos 2010..2024). Só uma amostra
    é impressa (todo, a cada 2, etc. — decidido aqui pela largura disponível).
    `faixa_destaque`: (índice_inicio, índice_fim) em `categorias` para
    hachurar uma janela (ex.: o período da gestão do prefeito atual) com uma
    faixa clara por trás das linhas.

    Retorna y abaixo do gráfico (já descontando eixo + legenda, se houver).
    """
    n = len(categorias)
    if n < 2 or not series:
        return y - h

    todos_valores = [v for s in series for v in s["valores"] if v is not None]
    if y_max is None:
        y_max = max(todos_valores) * 1.15 if todos_valores else 1

    eixo_x = x + 28   # respiro pra rótulos do eixo Y
    eixo_w = w - 28
    eixo_y = y - h + 22  # respiro pro eixo X embaixo
    eixo_h = h - 22 - 8  # respiro em cima

    def _px(i):
        return eixo_x + (i / (n - 1)) * eixo_w

    def _py(v):
        if y_max == y_min:
            return eixo_y
        return eixo_y + ((v - y_min) / (y_max - y_min)) * eixo_h

    # Faixa de destaque (ex.: gestão do prefeito atual)
    if faixa_destaque:
        i0, i1 = faixa_destaque
        fx0, fx1 = _px(max(0, i0)), _px(min(n - 1, i1))
        c.setFillColor(CREAM_DARK)
        c.rect(fx0, eixo_y, fx1 - fx0, eixo_h, fill=1, stroke=0)
        if faixa_label:
            c.setFillColor(MUTED)
            c.setFont(F(FONT_TEXTO), 6.5)
            c.drawCentredString((fx0 + fx1) / 2, eixo_y + eixo_h + 4, faixa_label.upper())

    # Grade horizontal + rótulos do eixo Y
    c.setStrokeColor(RULE)
    c.setLineWidth(0.5)
    c.setFillColor(MUTED)
    c.setFont(F(FONT_TEXTO), 6.5)
    for i in range(n_linhas_grade + 1):
        gv = y_min + (y_max - y_min) * i / n_linhas_grade
        gy = _py(gv)
        c.line(eixo_x, gy, eixo_x + eixo_w, gy)
        c.drawRightString(eixo_x - 4, gy - 2, f"{gv:,.0f}".replace(",", "."))

    # Eixo X: só uma amostra dos rótulos pra não sobrepor.
    passo = max(1, round(n / 8))
    c.setFillColor(MUTED)
    c.setFont(F(FONT_TEXTO), 6.5)
    for i, rot in enumerate(categorias):
        if i % passo == 0 or i == n - 1:
            c.drawCentredString(_px(i), eixo_y - 10, str(rot))

    # Linhas de cada série
    for s in series:
        cor = s.get("cor", BLUE)
        c.setStrokeColor(cor)
        c.setLineWidth(1.6)
        pontos = [(i, v) for i, v in enumerate(s["valores"]) if v is not None]
        for (i0, v0), (i1, v1) in zip(pontos, pontos[1:]):
            c.line(_px(i0), _py(v0), _px(i1), _py(v1))
        c.setFillColor(cor)
        for i, v in pontos:
            c.circle(_px(i), _py(v), 1.8, fill=1, stroke=0)

    y_abaixo = y - h

    # Legenda: uma linha, quadradinho + nome por série.
    if legenda and len(series) > 1:
        leg_y = y_abaixo - 10
        leg_x = eixo_x
        c.setFont(F(FONT_TEXTO), 7.5)
        for s in series:
            c.setFillColor(s.get("cor", BLUE))
            c.rect(leg_x, leg_y - 1, 7, 7, fill=1, stroke=0)
            c.setFillColor(INK)
            c.drawString(leg_x + 11, leg_y, s["nome"])
            leg_x += 11 + c.stringWidth(s["nome"], F(FONT_TEXTO), 7.5) + 14
        y_abaixo -= 16

    return y_abaixo


# ─── Selo de posição, barra percentual e donut — padrão visual do IFEM ───────
# Genéricos: nenhuma referência a mortalidade/receita/tema específico aqui.
# Quem chama decide o texto e a polaridade (ver DESIGN_SYSTEM.md §5.9-5.11).

def draw_ranking_stat_grande(c, pos: int, total: int, label: str,
                             cx: float, y_top: float, raio: float = 26) -> float:
    """Selo circular grande com uma posição de ranking — "246º" dentro do
    círculo, "de 645" embaixo, rótulo curto acima (ex.: "ESTADO"). Cor pela
    posição via `paleta_ranking.cor_por_percentil` — quem chama decide se
    é essa ou a invertida, dependendo de qual convenção a fonte do dado usa
    para "posição 1" (ver CLAUDE.md, Diretrizes de Engenharia).

    Retorna y abaixo do selo."""
    c.setFillColor(MUTED)
    c.setFont(F(FONT_TEXTO_SEMIBOLD), FS_CAPTION)
    c.drawCentredString(cx, y_top, label.upper())

    cy = y_top - 16 - raio
    if total:
        from .paleta_ranking import cor_por_percentil
        cor = cor_por_percentil(pos, total)
    else:
        cor = MUTED
    c.setFillColor(cor)
    c.circle(cx, cy, raio, fill=1, stroke=0)

    pos_str = f"{pos}º"
    fs = 20
    font = F(FONT_NUM_BOLD)
    while c.stringWidth(pos_str, font, fs) > raio * 1.6 and fs > 9:
        fs -= 1
    c.setFillColor(WHITE)
    c.setFont(font, fs)
    c.drawCentredString(cx, cy - fs * 0.32, pos_str)

    if total:
        c.setFillColor(MUTED)
        c.setFont(F(FONT_TEXTO), FS_CAPTION)
        c.drawCentredString(cx, cy - raio - 14, f"de {total:,}".replace(",", "."))

    return cy - raio - (26 if total else 10)


def draw_percentual_bar(c, pct: float, rotulo: str, x: float, y: float,
                        w: float, h: float = 10) -> float:
    """Barra horizontal colorida (0-100%, escala vermelho→verde de
    `cor_status_landing`) com um rótulo textual acima — o texto vem de
    fora porque a polaridade muda por métrica (nunca fixar algo tipo
    "supera X%": pra mortalidade a frase certa é o oposto, ver
    `mobilidade.py`). `pct` já deve estar na orientação "maior = melhor"
    antes de chamar.

    Retorna y abaixo da barra."""
    c.setFillColor(MUTED)
    c.setFont(F(FONT_TEXTO), FS_CAPTION)
    c.drawString(x, y, rotulo)
    y -= 16

    c.setFillColor(RULE)
    c.roundRect(x, y - h, w, h, h / 2, fill=1, stroke=0)

    pct_c = max(0.0, min(100.0, pct))
    fill_w = max(w * pct_c / 100, h) if pct_c > 0 else 0
    if fill_w > 0:
        c.setFillColor(cor_status_landing(pct_c))
        c.roundRect(x, y - h, fill_w, h, h / 2, fill=1, stroke=0)

    c.setFillColor(INK)
    c.setFont(F(FONT_NUM_BOLD), 11)
    c.drawRightString(x + w, y - h - 13, f"{pct_c:.0f}%")

    return y - h - 26


def draw_donut_chart(c, segmentos: list[dict], cx: float, cy: float,
                     raio: float, raio_interno: float | None = None,
                     legenda_x: float | None = None, legenda_y: float | None = None) -> float:
    """Donut chart genérico. `segmentos`: [{"label", "valor", "cor"}, ...].
    Fatias proporcionais ao valor, começando no topo (12h), sentido
    horário — furo central (`raio_interno`, default 55% do raio) em
    branco. Técnica: path poligonal aproximando o arco (sem depender de
    lib de gráfico externa), mesma usada no folheto-ifem.

    Se `legenda_x`/`legenda_y` forem passados, desenha uma legenda (uma
    linha por segmento: quadradinho + rótulo + %) a partir dali. Sem
    segmentos com valor (todos None/zero), não desenha nada e retorna
    `cy - raio` — degradação silenciosa, é um elemento complementar, não
    a informação principal da página."""
    import math

    validos = [s for s in segmentos if s.get("valor")]
    total = sum(s["valor"] for s in validos)
    if not total:
        return cy - raio

    raio_int = raio_interno if raio_interno is not None else raio * 0.55

    start = 90.0
    for seg in validos:
        ang = 360 * (seg["valor"] / total)
        end = start - ang
        c.setFillColor(seg.get("cor", BLUE))
        p = c.beginPath()
        p.moveTo(cx, cy)
        n_steps = max(6, int(abs(start - end) / 4))
        for i in range(n_steps + 1):
            t = i / n_steps
            a = math.radians(start + (end - start) * t)
            p.lineTo(cx + raio * math.cos(a), cy + raio * math.sin(a))
        p.close()
        c.drawPath(p, fill=1, stroke=0)
        start = end

    if raio_int > 0:
        c.setFillColor(WHITE)
        c.circle(cx, cy, raio_int, fill=1, stroke=0)

    if legenda_x is not None and legenda_y is not None:
        ly = legenda_y
        for seg in validos:
            pct = seg["valor"] / total * 100
            c.setFillColor(seg.get("cor", BLUE))
            c.rect(legenda_x, ly - 1, 8, 8, fill=1, stroke=0)
            c.setFillColor(INK)
            c.setFont(F(FONT_TEXTO_SEMIBOLD), 9)
            c.drawString(legenda_x + 13, ly, seg["label"])
            c.setFillColor(MUTED)
            c.setFont(F(FONT_TEXTO), 9)
            c.drawString(legenda_x + 13 + c.stringWidth(seg["label"], F(FONT_TEXTO_SEMIBOLD), 9) + 6,
                        ly, f"{pct:.0f}%")
            ly -= 16

    return cy - raio


def draw_qr_bloco(c, url: str, x: float, y_top: float, w: float, h: float = 150) -> float:
    """Versão compacta do QR code — um card branco com QR + URL, pra
    encaixar ao lado de outro conteúdo (ex.: a página de metodologia).
    `draw_qr_page` continua existindo pra quem precisar da versão página
    inteira (capa de encerramento dedicada).

    Retorna y abaixo do card."""
    c.setFillColor(WHITE)
    c.roundRect(x, y_top - h, w, h, CARD_RADIUS, fill=1, stroke=0)
    c.setStrokeColor(RULE)
    c.setLineWidth(0.6)
    c.roundRect(x, y_top - h, w, h, CARD_RADIUS, fill=0, stroke=1)

    qr_lado = min(w - 30, h - 50)
    qr_x = x + (w - qr_lado) / 2
    qr_y = y_top - 18 - qr_lado

    try:
        import qrcode as qr_lib
        qr = qr_lib.QRCode(version=1, box_size=4, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color=QR_FILL_COLOR, back_color="white")
        buf = BytesIO()
        qr_img.save(buf, format="PNG")
        buf.seek(0)
        c.drawImage(ImageReader(buf), qr_x, qr_y, width=qr_lado, height=qr_lado)
    except ImportError:
        c.setFillColor(MUTED)
        c.setFont(F(FONT_TEXTO), 8)
        c.drawCentredString(x + w / 2, qr_y + qr_lado / 2, url)

    c.setFillColor(BLUE_DARK)
    c.setFont(F(FONT_TEXTO_SEMIBOLD), 8.5)
    c.drawCentredString(x + w / 2, qr_y - 16, "Acesse")
    c.setFont(F(FONT_TEXTO_SEMIBOLD), 7.5)
    c.drawCentredString(x + w / 2, qr_y - 27, url)

    return y_top - h - 10


# ─── Mosaico fotográfico mascarado (capa) — técnica real do folheto-ifem ─────
# A capa real do IFEM não usa a foto retangular lisa: ela aparece fatiada
# por uma grade de janelas no vocabulário modular (quarto de círculo, meio
# círculo, quadrado cheio) — ver DESIGN_SYSTEM.md §1 e §5.1. Reconstruído
# aqui via clipping paths (ReportLab), não um PNG pré-composto: qualquer
# foto full-bleed passada em `foto_path` ganha o mesmo tratamento.

def _caminho_cunha(c, cx: float, cy: float, raio: float, ang_inicio: float, extensao: float):
    """Path de uma 'cunha' (pie slice): do vértice (cx,cy) até o início do
    arco, o arco em si, e de volta ao vértice. Para `extensao=90` é um
    quarto de círculo (vértice = canto); para `extensao=180`, como o
    vértice fica exatamente no meio da corda, o resultado é um meio-disco
    (mesma técnica do glifo 'B', §5.14)."""
    p = c.beginPath()
    p.moveTo(cx, cy)
    p.arcTo(cx - raio, cy - raio, cx + raio, cy + raio, ang_inicio, extensao)
    p.close()
    return p


# Receita de cada letra em termos das PRÓPRIAS categorias de célula do
# mosaico (canto de quarto-de-círculo, quadrado cheio, círculo inscrito) —
# não o traço colorido do §5.14, aqui é a mesma máscara-preenchida-pela-
# foto de cada célula do mosaico, só que arranjada pra ler como letra.
# Coordenadas (linha, coluna) relativas ao canto inferior-esquerdo da
# PRÓPRIA letra (linha 0 = base da letra; 2 linhas de altura, exceto "I",
# que é só 1 coluna).
_RECEITA_GLIFO_MOSAICO = {
    "M": {(1, 0): "br", (1, 1): "bl", (0, 0): "quadrado", (0, 1): "quadrado"},
    "O": {(1, 0): "br", (1, 1): "bl", (0, 0): "tr", (0, 1): "tl"},
    # "bl"/"tl" nas duas células da direita criava só UM bojo contínuo (lia
    # como "D", reportado pelo usuário) — "esq" (meio-círculo por aresta,
    # mesma técnica do glifo original em vetor) cria dois bojos separados
    # por uma "cintura" no meio, que é o que faz ler como "B".
    "B": {(1, 0): "quadrado", (0, 0): "quadrado", (1, 1): "esq", (0, 1): "esq"},
    "I": {(1, 0): "circulo", (0, 0): "quadrado"},
}
_LARGURA_GLIFO_MOSAICO = {"M": 2, "O": 2, "B": 2, "I": 1}


def draw_mosaico_fotografico(c, foto_path, page_w: float, y0: float, y1: float,
                             seed: int = 13, cols: int = 8,
                             palavra_mosaico: str | None = None,
                             margem_direita: float = 0) -> None:
    """Preenche a faixa vertical [y0, y1] (full-bleed em `page_w`) com a
    MESMA foto recortada por uma grade de janelas modulares — não uma foto
    lisa. Cada célula da grade sorteia (determinístico via `seed`, mesma
    imagem sempre gera a mesma grade) entre: quadrado cheio, quarto de
    círculo (vértice num dos 4 cantos da célula) ou meio círculo (base numa
    das 4 arestas). Fora da forma sorteada, a célula fica em branco — é
    isso que dá o efeito "janela", não um recorte retangular comum.

    `palavra_mosaico` (opcional): soletra a palavra usando as MESMAS
    células do mosaico (não um selo por cima) — encostada na quina
    inferior-direita da grade, nas 2 linhas mais próximas da faixa de
    informação da capa. Só as letras em `_RECEITA_GLIFO_MOSAICO` têm
    receita; uma letra sem receita é ignorada em silêncio (a palavra
    inteira não cabendo na largura da grade também degrada assim — nunca
    quebra a geração por causa de decoração).

    `margem_direita`: reserva colunas inteiras de respiro na borda direita
    antes de ancorar a palavra ali (não a grade inteira, que continua
    sangrando até `page_w`) — necessário quando o stripe lateral fica por
    cima do mosaico (`draw_capa_padrao` com `lado="dir"`): sem isso, a
    última letra ficava parcialmente escondida atrás do stripe (bug real,
    visto no primeiro resultado com essa palavra).

    Não desenha nada se `foto_path` não existir (fallback documentado em
    `assets/README.md` — a página fica só com o fundo branco, ou o
    chamador usa `palavra_capa` como alternativa, ver `draw_capa_padrao`)."""
    import math
    import random
    from pathlib import Path

    foto = Path(foto_path)
    if not foto.exists():
        return

    cell = page_w / cols
    zona_h = y1 - y0
    linhas = math.ceil(zona_h / cell)
    rng = random.Random(seed)
    img = cached_image(foto)

    c.saveState()
    zona = c.beginPath()
    zona.rect(0, y0, page_w, zona_h)
    c.clipPath(zona, stroke=0, fill=0)

    # Vértice em cada canto da célula, arco de 90° bulindo pro interior —
    # mesma técnica de `_glifo_m`/`_glifo_o` (§5.14), agora usada como
    # máscara em vez de contorno.
    cantos_quarto = {
        "bl": (0, 0, 0, 90), "br": (cell, 0, 90, 90),
        "tr": (cell, cell, 180, 90), "tl": (0, cell, 270, 90),
    }
    # Base numa aresta, meio-círculo bulindo pro interior — mesma técnica
    # do glifo 'B'.
    arestas_meio = {
        "esq": (0, cell / 2, 270, 180), "dir": (cell, cell / 2, 90, 180),
        "baixo": (cell / 2, 0, 0, 180), "cima": (cell / 2, cell, 180, 180),
    }

    # Sobreposição determinística das células que a palavra ocupa —
    # calculada ANTES do laço principal, pra cada célula só decidir uma vez
    # entre "faz parte da palavra" ou "sorteio normal do mosaico".
    sobreposicao: dict[tuple[int, int], str] = {}
    if palavra_mosaico:
        letras = [l for l in palavra_mosaico.upper() if l in _RECEITA_GLIFO_MOSAICO]
        largura_total = sum(_LARGURA_GLIFO_MOSAICO[l] for l in letras)
        # Colunas inteiras cobertas por `margem_direita` viram respiro —
        # arredonda pra cima: sobrar um pouco de folga é melhor que a
        # última coluna ficar meio-escondida atrás do stripe.
        cols_reservadas = math.ceil(margem_direita / cell) if margem_direita > 0 else 0
        cols_uteis = cols - cols_reservadas
        if letras and largura_total <= cols_uteis and linhas >= 2:
            col_cursor = cols_uteis - largura_total  # encosta na quina útil
            for letra in letras:
                for (r, cc), tipo in _RECEITA_GLIFO_MOSAICO[letra].items():
                    sobreposicao[(r, col_cursor + cc)] = tipo
                col_cursor += _LARGURA_GLIFO_MOSAICO[letra]

    for lin in range(linhas):
        for col in range(cols):
            cx0, cy0 = col * cell, y0 + lin * cell
            sorteio = rng.random()  # sempre avança o RNG, mesmo em célula sobreposta —
            c.saveState()           # preserva o padrão sorteado nas outras células.
            tipo_forcado = sobreposicao.get((lin, col))
            if tipo_forcado == "quadrado":
                p = c.beginPath()
                p.rect(cx0, cy0, cell, cell)
            elif tipo_forcado == "circulo":
                p = c.beginPath()
                p.circle(cx0 + cell / 2, cy0 + cell / 2, cell / 2)
            elif tipo_forcado in cantos_quarto:
                dx, dy, ang, ext = cantos_quarto[tipo_forcado]
                p = _caminho_cunha(c, cx0 + dx, cy0 + dy, cell, ang, ext)
            elif tipo_forcado in arestas_meio:
                dx, dy, ang, ext = arestas_meio[tipo_forcado]
                p = _caminho_cunha(c, cx0 + dx, cy0 + dy, cell / 2, ang, ext)
            elif sorteio < 0.25:
                p = c.beginPath()
                p.rect(cx0, cy0, cell, cell)
            elif sorteio < 0.65:
                dx, dy, ang, ext = rng.choice(list(cantos_quarto.values()))
                p = _caminho_cunha(c, cx0 + dx, cy0 + dy, cell, ang, ext)
            else:
                dx, dy, ang, ext = rng.choice(list(arestas_meio.values()))
                p = _caminho_cunha(c, cx0 + dx, cy0 + dy, cell / 2, ang, ext)
            c.clipPath(p, stroke=0, fill=0)
            c.drawImage(img, 0, y0, width=page_w, height=zona_h,
                        preserveAspectRatio=False, mask="auto")
            c.restoreState()
            # Contorno fino em TODA célula, igual e único (fora do clip, já
            # restaurado) — mesmo padrão da capa real do IFEM: uma linha só,
            # bem fina, igual em toda a grade, sem tratamento especial pras
            # células da palavra (o usuário pediu "padrão", não destaque).
            # Sem contorno nenhum, duas células vizinhas mostrando um pedaço
            # contínuo da mesma foto não têm fronteira visível — é o que
            # também apagava a palavra "MOBI" dentro do mosaico.
            c.setStrokeColor(WHITE)
            c.setLineWidth(0.6)
            c.drawPath(p, fill=0, stroke=1)

    c.restoreState()


# ─── Alfabeto modular (capa) — vocabulário geométrico do folheto-ifem ────────
# Cada letra é composta só das formas do "sistema modular" (DESIGN_SYSTEM.md
# §1: quadrado vazio, quarto de círculo, meio círculo), reconstruída em vetor
# a partir de `inspiration/Folheto_Alfabeto.jpeg` do repo `dadosfnp/folheto-
# ifem` (não trazido para este repo — só a técnica; ver CLAUDE.md Decisão 5).
# Genérico: a palavra é sempre um parâmetro, núcleo nunca sabe que o tema
# mobilidade soletra "MOBI".

_PALETA_MODULAR = (BLUE_DARK, BLUE, BLUE_MID, YELLOW_DARK)


_TRACO_MODULAR = 2.2  # espessura do traço — precisa ler como logotipo, não esboço fino


def _glifo_m(c, x0, y0, m, cores, traco=_TRACO_MODULAR):
    """'M': dois quartos de círculo formando as duas cristas do topo (mesmo
    vértice, no centro do bloco 2m×2m) + dois quadrados na base. Em cor
    única (sem a alternância de cor por wedge que a capa usa), as duas
    cristas se fundiam visualmente num arco só, liso — ficava indistinguível
    do 'A' (reportado pelo usuário no lettermark do stripe, §5.16). A linha
    reta do vértice até o topo do arco marca a "costura" entre as cristas
    mesmo com as duas na mesma cor."""
    box = (x0, y0, x0 + 2 * m, y0 + 2 * m)
    c.setLineWidth(traco)
    c.setStrokeColor(cores[0])
    c.wedge(*box, 90, 90, stroke=1, fill=0)
    c.setStrokeColor(cores[1])
    c.wedge(*box, 0, 90, stroke=1, fill=0)
    c.setStrokeColor(cores[0])
    c.line(x0 + m, y0 + m, x0 + m, y0 + 2 * m)
    c.setStrokeColor(cores[2])
    c.rect(x0, y0, m, m, fill=0, stroke=1)
    c.rect(x0 + m, y0, m, m, fill=0, stroke=1)
    return 2 * m


def _glifo_o(c, x0, y0, m, cores, traco=_TRACO_MODULAR):
    """'O': círculo inscrito no bloco 2m×2m, em 4 quartos coloridos —
    mesma leitura do '0' em `Folheto_Alfabeto.jpeg`."""
    box = (x0, y0, x0 + 2 * m, y0 + 2 * m)
    c.setLineWidth(traco)
    for i, ang in enumerate((0, 90, 180, 270)):
        c.setStrokeColor(cores[i % len(cores)])
        c.wedge(*box, ang, 90, stroke=1, fill=0)
    return 2 * m


def _glifo_b(c, x0, y0, m, cores, traco=_TRACO_MODULAR):
    """'B': espinha vertical grossa + 2 meios-círculos empilhados,
    abaulando pra direita e quase se tocando no meio (vocabulário "meio
    círculo" do sistema modular, §1) — lido como o corpo da letra, a
    espinha como o traço reto."""
    c.setLineWidth(traco + 0.6)
    c.setStrokeColor(cores[2])
    c.line(x0, y0, x0, y0 + 2 * m)
    r = m * 0.92
    c.setLineWidth(traco)
    for i, cy in enumerate((y0 + 1.5 * m, y0 + 0.5 * m)):
        c.setStrokeColor(cores[i % len(cores)])
        c.wedge(x0 - r, cy - r, x0 + r, cy + r, 270, 180, stroke=1, fill=0)
    return 2 * m


def _glifo_i(c, x0, y0, m, cores, traco=_TRACO_MODULAR):
    """'I': círculo sobre quadrado, só a coluna esquerda (mais estreita que
    as outras letras) — mesmo desenho do 'I' em `Folheto_Alfabeto.jpeg`."""
    c.setLineWidth(traco)
    c.setStrokeColor(cores[0])
    c.circle(x0 + m / 2, y0 + 1.5 * m, m / 2, fill=0, stroke=1)
    c.setStrokeColor(cores[1])
    c.rect(x0, y0, m, m, fill=0, stroke=1)
    return m


def _glifo_l(c, x0, y0, m, cores, traco=_TRACO_MODULAR):
    """'L': espinha vertical (2 quadrados à esquerda) + "pé" (1 quadrado
    embaixo à direita) — mesmo desenho blocado do 'L' em
    `Folheto_Alfabeto.jpeg`."""
    c.setLineWidth(traco)
    c.setStrokeColor(cores[0])
    c.rect(x0, y0 + m, m, m, fill=0, stroke=1)
    c.setStrokeColor(cores[1])
    c.rect(x0, y0, m, m, fill=0, stroke=1)
    c.setStrokeColor(cores[2])
    c.rect(x0 + m, y0, m, m, fill=0, stroke=1)
    return 2 * m


def _glifo_d(c, x0, y0, m, cores, traco=_TRACO_MODULAR):
    """'D': espinha vertical (2 quadrados à esquerda) + um bojo único à
    direita (2 quartos de círculo com o MESMO vértice — ao contrário do
    'B', aqui os dois se fundem numa curva só, sem cintura, exatamente
    porque um bojo contínuo é o que faz ler como D, não como B)."""
    box = (x0, y0, x0 + 2 * m, y0 + 2 * m)
    c.setLineWidth(traco)
    c.setStrokeColor(cores[0])
    c.rect(x0, y0 + m, m, m, fill=0, stroke=1)
    c.setStrokeColor(cores[1])
    c.rect(x0, y0, m, m, fill=0, stroke=1)
    c.setStrokeColor(cores[2])
    c.wedge(*box, 0, 90, stroke=1, fill=0)
    c.wedge(*box, 270, 90, stroke=1, fill=0)
    return 2 * m


def _glifo_a(c, x0, y0, m, cores, traco=_TRACO_MODULAR):
    """'A': meio-círculo único no topo (abaulando pra cima, vértice no
    meio da altura) + duas "pernas" (quadrados) na base."""
    c.setLineWidth(traco)
    c.setStrokeColor(cores[0])
    c.wedge(x0, y0, x0 + 2 * m, y0 + 2 * m, 0, 180, stroke=1, fill=0)
    c.setStrokeColor(cores[2])
    c.rect(x0, y0, m, m, fill=0, stroke=1)
    c.rect(x0 + m, y0, m, m, fill=0, stroke=1)
    return 2 * m


def _glifo_e(c, x0, y0, m, cores, traco=_TRACO_MODULAR):
    """'E': espinha vertical (2 quadrados à esquerda) + topo e base à
    direita (2 quadrados) — lê como um "C" quadrado; aproximação
    deliberada (a grade 2×2 não tem uma terceira linha pro travessão do
    meio de um E "de verdade")."""
    c.setLineWidth(traco)
    c.setStrokeColor(cores[0])
    c.rect(x0, y0 + m, m, m, fill=0, stroke=1)
    c.rect(x0 + m, y0 + m, m, m, fill=0, stroke=1)
    c.setStrokeColor(cores[1])
    c.rect(x0, y0, m, m, fill=0, stroke=1)
    c.rect(x0 + m, y0, m, m, fill=0, stroke=1)
    return 2 * m


_GLIFOS_MODULARES = {
    "M": _glifo_m, "O": _glifo_o, "B": _glifo_b, "I": _glifo_i,
    "L": _glifo_l, "D": _glifo_d, "A": _glifo_a, "E": _glifo_e,
}
_LARGURA_GLIFO_MULT = {"M": 2, "O": 2, "B": 2, "I": 1, "L": 2, "D": 2, "A": 2, "E": 2}


def largura_alfabeto_modular_palavra(palavra: str, modulo: float, gap: float | None = None) -> float:
    """Largura total que `draw_alfabeto_modular_palavra` vai ocupar, sem
    desenhar nada — usado pra centralizar a palavra antes de saber onde
    colocar `x`. Mantida em sincronia com `_GLIFOS_MODULARES`/`_LARGURA_GLIFO_MULT`
    (letra sem glifo conta como 1 módulo de largura, igual ao fallback de
    quadrado vazio que `draw_alfabeto_modular_palavra` desenha)."""
    gap = gap if gap is not None else modulo * 0.35
    letras = palavra.upper()
    if not letras:
        return 0.0
    total = sum(_LARGURA_GLIFO_MULT.get(l, 1) * modulo for l in letras)
    return total + gap * (len(letras) - 1)


def draw_alfabeto_modular_palavra(c, palavra: str, x: float, y: float, modulo: float,
                                  cores=_PALETA_MODULAR, gap: float | None = None,
                                  traco: float = _TRACO_MODULAR) -> float:
    """Desenha `palavra` no alfabeto modular (vocabulário de quarto de
    círculo / meio círculo / quadrado — DESIGN_SYSTEM.md §1). `x`, `y` é o
    canto inferior-esquerdo; cada letra ocupa uma célula de altura
    `2*modulo` (largura `2*modulo`, ou `modulo` para o 'I'). Cor cíclica a
    partir de `cores`. `traco` é a espessura do traço — o padrão (2.2pt) é
    pensado pro tamanho grande da capa; um lettermark pequeno (stripe,
    §5.16) precisa de um traço bem mais fino, senão as formas se fundem.

    Só as letras em `_GLIFOS_MODULARES` têm glifo desenhado hoje — uma letra
    sem glifo vira um quadrado vazio (degradação silenciosa: nunca quebra a
    geração por causa de uma letra que ainda não tem desenho).

    Retorna a largura total desenhada."""
    gap = gap if gap is not None else modulo * 0.35
    cx = x
    for letra in palavra.upper():
        glifo = _GLIFOS_MODULARES.get(letra)
        if glifo:
            w = glifo(c, cx, y, modulo, cores, traco=traco)
        else:
            c.setStrokeColor(cores[0])
            c.setLineWidth(traco)
            c.rect(cx, y, modulo, modulo * 2, fill=0, stroke=1)
            w = modulo
        cx += w + gap
    return cx - gap - x


def draw_lettermark_stripe(c, palavra: str, page_w: float, page_h: float,
                           lado: str = "dir", modulo: float = 7.0) -> None:
    """Palavra soletrada VERTICALMENTE dentro do stripe lateral, no alfabeto
    modular (§5.14) — mesmo padrão do folheto-ifem, que tem "IFEM" vertical
    no stripe via um PNG pré-rotacionado (`core/ifem_assets.py::
    ifem_lettermark_vertical_path`). Aqui é vetor puro, rotacionado na hora
    (`canvas.rotate`) — nunca um asset raster, mesma filosofia do resto do
    alfabeto modular deste projeto.

    Traço bem mais fino que o da capa (`modulo` pequeno pede isso — senão
    as formas se fundem) e branco translúcido, pra ler como marca d'água
    discreta no azul do stripe, não competir com o número de página.
    Centralizado na altura inteira da página; leitura de baixo pra cima
    (primeira letra embaixo, subindo — pedido explícito do usuário, com uma
    seta desenhada apontando pra cima sobre o stripe). A rotação do canvas
    continua a mesma; o que inverte a direção é desenhar a palavra ao
    contrário (`palavra[::-1]`) — a última letra desenhada (primeira letra
    da palavra) fica no topo, a primeira desenhada (última letra da
    palavra) fica embaixo, então ler de baixo pra cima dá a palavra certa."""
    largura = largura_alfabeto_modular_palavra(palavra, modulo)
    if largura <= 0:
        return
    cx = STRIPE_W / 2 if lado == "esq" else page_w - STRIPE_W / 2
    c.saveState()
    c.setStrokeAlpha(0.35)
    c.translate(cx, (page_h + largura) / 2)
    c.rotate(-90)
    draw_alfabeto_modular_palavra(c, palavra[::-1], 0, -modulo, modulo,
                                  cores=(WHITE, WHITE, WHITE), traco=0.5)
    c.restoreState()


# ─── Decoração de rodapé (alfabeto modular) — preenche o respiro final ───────
# Portada de `_decorar_rodape` do folheto-ifem (python/temas/ifem.py) como
# primitiva genérica de core — nenhuma referência a tema aqui. É a peça que
# fechava a lacuna de "identidade" nas páginas com sobra de espaço embaixo
# (ver DESIGN_SYSTEM.md §5.13, CLAUDE.md Decisão 5).

_ARTES_RODAPE = (
    ("arte2", 592 / 216),   # faixa alta
    ("arte1", 591 / 108),   # faixa fina
    ("arte0", 437 / 39),    # ultra-fina
)
# Abaixo disso a arte vira um carimbo perdido no meio da página: melhor
# descer para a próxima mais fina ou não desenhar nada.
_LARGURA_MIN_ARTE = 0.6


def draw_decoracao_rodape(c, lado: str, y_max: float,
                          forcar_fina: bool = False, arte: str | None = None) -> None:
    """Preenche o espaço vazio no fim de uma página de conteúdo com um dos
    3 padrões modulares (`assets/padroes/arte0|1|2.png`).

    `y_max` é o Y onde o conteúdo real da página terminou: a arte é sempre
    desenhada abaixo dele, e é esta função — nunca o chamador — quem garante
    isso, medindo o espaço livre até o rodapé. Uma arte que não cabe é
    trocada pela próxima mais fina; se nenhuma couber, a página fica sem
    decoração (respiro em branco é aceitável; conteúdo coberto não é).

    `arte` fixa a preferência ('arte0'|'arte1'|'arte2'); `forcar_fina`
    começa a busca em 'arte1'. Em ambos os casos é um teto pra busca: ela só
    desce a lista, nunca sobe para uma arte mais alta do que a pedida."""
    footer_y = 36
    base_y = footer_y + 4
    h_disp = y_max - base_y
    if h_disp < 20:
        return

    x0 = STRIPE_W + MARGIN if lado == "esq" else MARGIN
    w_disp = CONTENT_W
    padroes_dir = ASSETS_DIR / "padroes"

    preferida = arte or ("arte1" if forcar_fina else "arte2")
    inicio = next((i for i, (nome, _) in enumerate(_ARTES_RODAPE) if nome == preferida), 0)

    for nome, ratio in _ARTES_RODAPE[inicio:]:
        img_path = padroes_dir / f"{nome}.png"
        if not img_path.exists():
            continue
        h_cheia = w_disp / ratio
        if h_cheia <= h_disp:
            # Cabe inteira: largura total do conteúdo, o encaixe mais limpo.
            w_fit, h_fit = w_disp, h_cheia
        else:
            # Não cabe: encolhe preservando o ratio, só até ainda ler como
            # faixa (abaixo de LARGURA_MIN_ARTE, tenta a próxima mais fina).
            h_fit = h_disp
            w_fit = h_fit * ratio
            if w_fit < w_disp * _LARGURA_MIN_ARTE:
                continue
        img_x = x0 + (w_disp - w_fit) / 2
        c.drawImage(cached_image(img_path), img_x, base_y,
                    width=w_fit, height=h_fit,
                    preserveAspectRatio=True, mask="auto")
        return
