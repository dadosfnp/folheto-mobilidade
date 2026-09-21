"""
Tema MOBILIDADE — Ficha de Diagnóstico Preliminar de Segurança Viária.

Público-alvo do folheto: cidades acima de 80 mil habitantes. Conteúdo
derivado do documento de briefing do projeto (mortes, internações, custo
hospitalar, ranking de causas de morte, evolução da frota).

**5 páginas, teto fixo** (decidido em 2026-09-21) — sem página de divisória
dedicada só a título de capítulo; o cabeçalho de seção vive dentro da
própria página de conteúdo, mesmo padrão de densidade do folheto-ifem (ver
CLAUDE.md, Decisão 4, e DESIGN_SYSTEM.md §6).

Estado desta versão (ver CLAUDE.md "Pendências"):
  - Frota, mortalidade, série histórica de mortes, internações e ranking de
    causas: implementados, com dado real para os 2 pilotos.
  - Custo por hospital e mapa de internações por bairro: NÃO implementados
    ainda — dependem de dado que ainda não existe (ver SCHEMA.md).

Contrato de dados completo: data/mobilidade/SCHEMA.md.
"""
import sys

from core.base_folheto import FolhetoFNP
from core.components import (
    draw_stripe, draw_page_number, draw_header, draw_footer,
    draw_eyebrow, draw_titulo, draw_body, draw_caption,
    draw_kpi_box, draw_destaque_box, draw_table, draw_ranking_item,
    draw_qr_bloco, draw_capa_padrao, draw_line_chart,
    draw_percentual_bar, draw_donut_chart, draw_decoracao_rodape,
)
from core.paleta_ranking import cor_por_percentil
from core.tokens import (
    MARGIN, STRIPE_W, CONTENT_W, ASSETS_DIR,
    BLUE, BLUE_DARK, RED_BURNT, GREEN, WHITE,
    FONT_NUM_BOLD,
    FS_TITLE_SECAO,
)
from core.fonts import F


def _fmt_taxa(v) -> str:
    """Taxa por 100 mil habitantes. `None` vira 'n/d' — nunca um traço solto
    (ver DESIGN_SYSTEM.md: travessão é proibido e confunde com sinal de menos)."""
    if v is None:
        return "n/d"
    return f"{v:,.1f}".replace(",", "@").replace(".", ",").replace("@", ".")


def _fmt_pct(v) -> str:
    if v is None:
        return "n/d"
    sinal = "+" if v >= 0 else ""
    return f"{sinal}{v:,.1f}%".replace(".", ",")


def _fmt_int(v) -> str:
    if v is None:
        return "n/d"
    return f"{v:,.0f}".replace(",", ".")


class FolhetoMobilidade(FolhetoFNP):
    titulo_publicacao = "SEGURANÇA VIÁRIA · DIAGNÓSTICO PRELIMINAR FNP"

    # PLACEHOLDER — não confirmado que esta URL existe/resolve. Nunca enviar
    # para impressão sem sobrescrever via campo "url" no JSON (ver SCHEMA.md)
    # com um endereço real e testado. Ver CLAUDE.md, seção Pendências.
    URL_PADRAO = "https://fnp.org.br/mobilidade"

    def construir_paginas(self):
        return [
            self._pag_capa,
            self._pag_problema_mortalidade,
            self._pag_serie_mortes_causas,
            self._pag_internacoes,
            self._pag_metodologia_encerramento,
        ]

    # ─── Helpers de conteúdo/ausência de dado ────────────────────────────────

    def _output_name(self):
        return self.d.get("nome", "folheto"), self.d.get("uf", "")

    def _avisar_se_ausente(self, chave: str, secao: str):
        if not self.d.get(chave):
            print(f"[aviso] '{chave}' ausente nos dados; a seção '{secao}' sairá "
                  f"incompleta ou vazia.", file=sys.stderr)

    def _topo_pagina(self, c, n, lado, label_secao, eyebrow, titulo, titulo_size=FS_TITLE_SECAO):
        """Fundo + stripe + numeração + header + eyebrow/título + footer.
        Retorna (x_conteudo, y_abaixo_titulo) prontos para o corpo da página."""
        c.setFillColor(WHITE)
        c.rect(0, 0, self.W, self.H, fill=1, stroke=0)

        draw_stripe(c, self.W, self.H, lado)
        draw_page_number(c, self.W, n, lado)
        draw_header(c, self.H, self.titulo_publicacao)
        draw_footer(c, self.W, label_secao)

        x = STRIPE_W + MARGIN if lado == "esq" else MARGIN
        y = self.H - 56
        draw_eyebrow(c, eyebrow, x, y)
        # Gap entre a baseline do eyebrow e a do título precisa acompanhar o
        # tamanho do título: um título de 30pt tem ascendentes que
        # ultrapassam um gap fixo pequeno e encostam no eyebrow (bug real,
        # visível sobretudo em letras com acento como "Ó").
        titulo_y = y - titulo_size * 1.05
        draw_titulo(c, titulo, x, titulo_y, size=titulo_size)
        y_corpo = titulo_y - titulo_size * 0.95 * titulo.count("\n") - 26
        return x, y_corpo

    def _selo_numerado(self, c, numero: int, cx: float, cy: float, raio: float = 13):
        """Círculo pequeno com um número dentro — passos da metodologia.
        Não é `draw_ranking_stat_grande` (não tem "de N", não é uma
        posição de ranking) — um selo simples o bastante pra não merecer
        virar primitiva genérica em `components.py`."""
        c.setFillColor(BLUE)
        c.circle(cx, cy, raio, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont(F(FONT_NUM_BOLD), 13)
        c.drawCentredString(cx, cy - 4.5, str(numero))

    # ─── Página 1: Capa ───────────────────────────────────────────────────────

    def _pag_capa(self, c, n):
        nome = self.d.get("nome", "Município")
        uf = self.d.get("uf", "")
        total_mort = (self.d.get("mortalidade_2024") or {}).get("total") or {}
        destaques = [
            ("Ranking de mortalidade no estado", total_mort.get("estado_pos"), total_mort.get("estado_total")),
            ("Ranking de mortalidade no Brasil", total_mort.get("brasil_pos"), total_mort.get("brasil_total")),
        ]
        draw_capa_padrao(
            c, self.W, self.H,
            municipio_nome=f"{nome}/{uf}" if uf else nome,
            eyebrow_capa="Segurança viária · Ficha de diagnóstico preliminar",
            # `_capa_foto` no JSON permite uma foto específica do município
            # no futuro (ver SCHEMA.md); sem isso, cai na arte fixa do tema
            # (mesmo padrão do IFEM — o mosaico real de lá também não muda
            # por município, ver CLAUDE.md Decisão 5).
            foto_path=self.d.get("_capa_foto") or str(ASSETS_DIR / "capa" / "mobilidade-capa.jpg"),
            logo_path=str(ASSETS_DIR / "logos" / "fnp-logo.png"),
            lado="dir",
            destaques=destaques,
            palavra_capa="MOBI",
            palavra_mosaico="MOBI",
        )

    # ─── Página 2: Apresentação + KPIs + Mortalidade 2024 ────────────────────

    def _pag_problema_mortalidade(self, c, n):
        self._avisar_se_ausente("problema", "Apresentação do tema")
        x, y = self._topo_pagina(
            c, n, "esq", "SEGURANÇA VIÁRIA", "SEGURANÇA VIÁRIA",
            "Por que isso\nimporta para a cidade",
        )
        problema = self.d.get("problema") or {}
        citacao = problema.get("citacao") or (
            "Cada sinistro de trânsito custa vidas, leitos hospitalares e "
            "recursos que a cidade poderia empregar em outras prioridades "
            "de saúde pública."
        )
        draw_destaque_box(c, "DESTAQUE", citacao, x, y - 62, CONTENT_W, h=78, font_size=14)
        y -= 154

        pop = (self.d.get("populacao") or {}).get("valor")
        frota = self.d.get("frota") or {}
        frota_atual = (frota.get("atual") or {}).get("total")
        cresc_frota = (frota.get("evolucao_pct") or {}).get("2003_2025", {}).get("total")
        mortes_serie = self.d.get("mortes_serie_historica") or {}
        anos_m = mortes_serie.get("anos") or []
        totais_m = mortes_serie.get("total") or []
        mortes_ultimo_ano = totais_m[-1] if totais_m else None

        cards = [
            ("População", _fmt_int(pop), "hab."),
            ("Frota atual", _fmt_int(frota_atual), "veículos"),
            ("Cresc. da frota · 2003–2025", _fmt_pct(cresc_frota), ""),
            ("Mortes no trânsito", _fmt_int(mortes_ultimo_ano),
             str(anos_m[-1]) if anos_m else ""),
        ]
        # Grid 2×2 (não 1×4): com só ~4 caracteres de sobra por card numa
        # fileira de 4, tanto o rótulo quanto valor+unidade estouram a
        # largura (ver CLAUDE.md/lição do draw_kpi_box). 2×2 dobra a largura
        # útil de cada card.
        card_w = (CONTENT_W - 12) / 2
        card_h = 54
        gap_v = 10
        for i, (label, valor, unidade) in enumerate(cards):
            col, row = i % 2, i // 2
            cx = x + col * (card_w + 12)
            cy = y - 46 - row * (card_h + gap_v)
            draw_kpi_box(c, label, valor, unidade, cx, cy, w=card_w, h=card_h)
        y -= 46 + 2 * (card_h + gap_v) + 22

        # Mortalidade 2024 (era página separada) ----------------------------
        self._avisar_se_ausente("mortalidade_2024", "Taxa de mortalidade 2024")
        draw_eyebrow(c, "TAXA DE MORTALIDADE · 2024", x, y, color=BLUE)
        y -= 16
        draw_body(
            c,
            "Óbitos por 100 mil hab., comparados com o recorte metropolitano, "
            "cidades de mesmo porte, o estado, o Brasil e as capitais. "
            "Fonte: SIM/DATASUS. Elaboração: FNP.",
            x, y, CONTENT_W, size=9,
        )
        y -= 26

        dados = self.d.get("mortalidade_2024") or {}
        linhas_labels = [
            ("total", "Total"),
            ("motociclistas", "Motociclistas"),
            ("pedestres", "Pedestres"),
            ("ciclistas", "Ciclistas"),
        ]
        headers = ["MODO", "MUNICÍPIO", "RM", "PORTE", "ESTADO", "BRASIL", "CAPITAIS"]
        col_w = [CONTENT_W * w for w in (0.17, 0.15, 0.13, 0.14, 0.14, 0.14, 0.13)]
        rows = []
        for chave, label in linhas_labels:
            linha = dados.get(chave) or {}
            rows.append([
                label,
                _fmt_taxa(linha.get("municipio")),
                _fmt_taxa(linha.get("rm")),
                _fmt_taxa(linha.get("porte")),
                _fmt_taxa(linha.get("estado")),
                _fmt_taxa(linha.get("brasil")),
                _fmt_taxa(linha.get("capitais")),
            ])
        draw_table(c, headers, rows, col_w, x, y, highlight_col=1)
        y -= len(rows) * 18 + 26
        draw_caption(c, "Leitura: quanto menor a taxa, melhor a posição do município.", x, y)
        y -= 22

        total_mort = dados.get("total") or {}
        brasil_pos, brasil_total = total_mort.get("brasil_pos"), total_mort.get("brasil_total")
        if brasil_pos and brasil_total:
            # Posição 1 = menor taxa = melhor (confirmado na fonte, aba
            # "metodologia" de indicadores_sim_relatorio.xlsx) — pct aqui já
            # nasce na orientação "maior = melhor", pronto pro verde/vermelho
            # de draw_percentual_bar sem inverter nada.
            pct_melhor = (brasil_total - brasil_pos) / brasil_total * 100
            y = draw_percentual_bar(
                c, pct_melhor,
                f"Taxa de mortalidade melhor que {pct_melhor:.0f}% dos municípios do Brasil",
                x, y, CONTENT_W,
            )
        draw_decoracao_rodape(c, "esq", y, forcar_fina=True)

    # ─── Página 3: Série de mortes + distribuição por modo + causas ─────────

    def _pag_serie_mortes_causas(self, c, n):
        self._avisar_se_ausente("mortes_serie_historica", "Série histórica de mortes")
        x, y = self._topo_pagina(
            c, n, "dir", "MORTES NO TRÂNSITO", "MORTES NO TRÂNSITO",
            "Evolução e causas\nde morte",
        )
        serie = self.d.get("mortes_serie_historica") or {}
        anos = serie.get("anos") or []
        if anos:
            series = [
                {"nome": "Total", "valores": serie.get("total"), "cor": BLUE_DARK},
                {"nome": "Motociclistas", "valores": serie.get("motociclistas"), "cor": RED_BURNT},
                {"nome": "Pedestres", "valores": serie.get("pedestres"), "cor": BLUE},
                {"nome": "Ciclistas", "valores": serie.get("ciclistas"), "cor": GREEN},
            ]
            series = [s for s in series if s["valores"]]
            y = draw_line_chart(
                c, series=series, categorias=anos,
                x=x, y=y, w=CONTENT_W, h=185,
            )
            y -= 12
            draw_caption(c, "Fonte: SIM/DATASUS, tratamento próprio. Elaboração: FNP.", x, y)
            y -= 26
        else:
            draw_body(c, "Série histórica ainda não disponível para este município.",
                      x, y - 20, CONTENT_W)
            y -= 60

        # Distribuição por modo (donut) — último ano disponível ----------------
        ultimo_ano = anos[-1] if anos else None
        segmentos = []
        if ultimo_ano:
            cores_modo = {"motociclistas": RED_BURNT, "pedestres": BLUE, "ciclistas": GREEN}
            for chave, cor in cores_modo.items():
                valores = serie.get(chave) or []
                if valores and valores[-1] is not None:
                    segmentos.append({
                        "label": chave.capitalize(), "valor": valores[-1], "cor": cor,
                    })
        if segmentos:
            draw_eyebrow(c, f"DISTRIBUIÇÃO POR MODO · {ultimo_ano}", x, y, color=BLUE)
            donut_cy = y - 16 - 44
            draw_donut_chart(
                c, segmentos, x + 48, donut_cy, raio=44,
                legenda_x=x + 120, legenda_y=y - 24,
            )
            y = donut_cy - 44 - 24

        # Ranking de causas de morte -------------------------------------------
        self._avisar_se_ausente("ranking_causas_morte", "Ranking de causas de morte")
        ranking = self.d.get("ranking_causas_morte") or {}
        posicoes = ranking.get("posicao_acidentes_transito") or {}
        if posicoes:
            draw_eyebrow(c, "CAUSAS DE MORTE", x, y, color=BLUE)
            y -= 16
            draw_body(
                c,
                "Posição dos \"acidentes de trânsito\" no ranking de causas de "
                # "or 'SMS'", não .get(..., 'SMS') — a chave pode existir com
                # `null` (ver SCHEMA.md, "Duas armadilhas do motor"), e nesse
                # caso o default do .get() nunca entra em ação.
                f"morte do município, por ano (fonte: {ranking.get('fonte') or 'SMS'}).",
                x, y, CONTENT_W, size=9,
            )
            y -= 30
            anos_ordenados = sorted(posicoes.keys())
            # "or 20", não .get(..., 20): com total_causas=None e posicoes
            # preenchido, o .get() com default não entra em ação e
            # draw_ranking_item recebe `total=None`, que quebra em
            # f"{None:,}" (TypeError) — não é só um valor errado, derruba a
            # geração do PDF inteiro.
            total_causas = ranking.get("total_causas") or 20
            for ano in anos_ordenados:
                draw_ranking_item(c, int(posicoes[ano]), f"Acidentes de trânsito · {ano}",
                                  total_causas, x, y, w=CONTENT_W)
                y -= 32

        draw_decoracao_rodape(c, "dir", y)

    # ─── Página 4: Internações (tabela + série histórica) ────────────────────

    def _pag_internacoes(self, c, n):
        self._avisar_se_ausente("internacoes_2025", "Internações por sinistro")
        x, y = self._topo_pagina(
            c, n, "esq", "INTERNAÇÕES", "INTERNAÇÕES",
            "Internações por\nsinistro de trânsito",
        )
        draw_body(
            c,
            "Taxa por 100 mil hab., SIH/SIA · dados sujeitos a revisão. Coleta "
            "em andamento: valores em branco (\"n/d\") serão preenchidos "
            "conforme os dados forem consolidados.",
            x, y, CONTENT_W, size=9,
        )
        y -= 28

        dados = self.d.get("internacoes_2025") or {}
        linhas_labels = [
            ("total", "Total"),
            ("motociclistas", "Motociclistas"),
            ("pedestres", "Pedestres"),
            ("ciclistas", "Ciclistas"),
        ]
        headers = ["MODO", "MUNICÍPIO", "PORTE", "ESTADO", "BRASIL"]
        col_w = [CONTENT_W * w for w in (0.28, 0.18, 0.20, 0.17, 0.17)]
        rows = []
        for chave, label in linhas_labels:
            linha = dados.get(chave) or {}
            rows.append([
                label,
                _fmt_taxa(linha.get("municipio")),
                _fmt_taxa(linha.get("porte")),
                _fmt_taxa(linha.get("estado")),
                _fmt_taxa(linha.get("brasil")),
            ])
        draw_table(c, headers, rows, col_w, x, y, highlight_col=1)
        y -= len(rows) * 18 + 26
        draw_caption(c, "Fonte: SIH/SIA · DATASUS. Elaboração: FNP.", x, y)
        y -= 30

        # Série histórica de internações (hachura a gestão do prefeito atual) --
        draw_eyebrow(c, "EVOLUÇÃO DAS INTERNAÇÕES", x, y, color=BLUE)
        y -= 16
        serie = self.d.get("internacoes_serie_historica") or {}
        anos = serie.get("anos") or []
        if anos and serie.get("total"):
            gestao = serie.get("gestao_atual") or {}
            faixa = None
            if gestao.get("inicio") in anos:
                i0 = anos.index(gestao["inicio"])
                i1 = anos.index(gestao["fim"]) if gestao.get("fim") in anos else len(anos) - 1
                faixa = (i0, i1)
            y = draw_line_chart(
                c, series=[{"nome": "Internações", "valores": serie.get("total"), "cor": BLUE_DARK}],
                categorias=anos, x=x, y=y, w=CONTENT_W, h=185,
                faixa_destaque=faixa, faixa_label="Gestão atual" if faixa else None,
                legenda=False,
            )
            y -= 12
            draw_caption(c, "Faixa destacada: gestão do prefeito atual. Fonte: SIH/DATASUS. Elaboração: FNP.", x, y)
            y -= 20
        else:
            y = draw_body(
                c,
                "Série histórica de internações ainda não disponível: "
                "coleta de dados em andamento (ver CLAUDE.md, seção "
                "Pendências).",
                x, y - 6, CONTENT_W,
            )

        draw_decoracao_rodape(c, "esq", y, forcar_fina=True)

    # ─── Página 5: Metodologia + encerramento/QR ─────────────────────────────

    def _pag_metodologia_encerramento(self, c, n):
        x, y = self._topo_pagina(
            c, n, "dir", "METODOLOGIA", "DE ONDE VÊM OS DADOS",
            "Fontes, tratamento\ne o que fazer com isso",
        )
        passos = (self.d.get("metodologia") or {}).get("passos") or [
            "Mortes no trânsito: Sistema de Informação sobre Mortalidade "
            "(SIM/DATASUS), classificadas por modo (pedestre, ciclista, "
            "motociclista) a partir da causa básica do óbito.",
            "Internações por sinistro: Sistema de Informações Hospitalares "
            "e Sistema de Informações Ambulatoriais (SIH/SIA, DATASUS).",
            "Frota de veículos: Registro Nacional de Veículos Automotores "
            "(RENAVAM/DENATRAN), evolução histórica por tipo de veículo.",
            "Comparações (recorte metropolitano, mesmo porte, estado, "
            "Brasil, capitais): mesma fonte e ano de referência do "
            "indicador do município, para manter a comparação justa.",
            "Custo hospitalar e mapa por bairro: dado em coleta. Ver "
            "CLAUDE.md, seção Pendências, para o estado atual.",
        ]
        # Coluna de texto mais estreita que CONTENT_W — sobra espaço à
        # direita pro bloco de QR (draw_qr_bloco), como o rodapé metodológico
        # do IFEM reserva espaço pro diagrama ao lado do texto.
        col_texto_w = CONTENT_W * 0.62
        y_inicio_passos = y
        for i, passo in enumerate(passos, start=1):
            self._selo_numerado(c, i, x + 9, y - 5)
            y = draw_body(c, passo, x + 26, y, col_texto_w - 26, size=9.5) - 16

        leitos = self.d.get("leitos_uti_hipotetico") or {}
        nota = leitos.get("nota")
        if nota:
            # draw_destaque_box trunca silenciosamente após 2 linhas — feito
            # pra citação curta, não pra um parágrafo. Título curto no box +
            # texto completo em draw_body logo abaixo evita perder conteúdo
            # sem aviso nenhum (mesma lição de CLAUDE.md — quase repeti o
            # erro ao consolidar esta página).
            y -= 6
            draw_destaque_box(
                c, "SE NÃO HOUVESSE SINISTROS DE TRÂNSITO",
                "Quantos leitos de UTI a cidade ganharia?",
                x, y - 50, col_texto_w, h=58, font_size=13,
            )
            y -= 66
            draw_body(c, nota, x + 8, y, col_texto_w - 16, size=8.5)

        # Bloco de QR, ao lado dos passos (mesma altura do início do texto)
        qr_x = x + col_texto_w + 20
        qr_w = CONTENT_W - col_texto_w - 20
        y_qr = draw_qr_bloco(c, self.d.get("url", self.URL_PADRAO), qr_x, y_inicio_passos, qr_w, h=170)

        # Rodapé decorativo só abaixo da coluna MAIS CURTA das duas (texto x
        # QR) — nunca sobrepor o card de QR, que também pode terminar mais
        # baixo que o texto dependendo do tamanho da nota dos leitos de UTI.
        draw_decoracao_rodape(c, "dir", min(y, y_qr), forcar_fina=True)
