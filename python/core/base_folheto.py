"""
Classe-base FolhetoFNP.

Cada tema (COSIP, IFEM, …) cria uma subclasse e implementa apenas
`construir_paginas()` — uma lista de callables que recebem (canvas, n_pagina)
e desenham uma página. Toda a infraestrutura (PDF, fontes, output) fica aqui.
"""
from pathlib import Path
from typing import Callable
from reportlab.lib.pagesizes import A3
from reportlab.pdfgen import canvas as rl_canvas

from .tokens import PAGE_SIZE, OUTPUT_DIR
from .fonts import register_fonts


PageFn = Callable[[rl_canvas.Canvas, int], None]

TAMANHOS_VALIDOS = ("A4", "A3")


class FolhetoFNP:
    """
    Classe-base para todos os folhetos FNP.

    Subclasses devem definir:
      - `titulo_publicacao`: ex. "IFEM · ÍNDICE DE FINANCIAMENTO DE EQUIDADE MUNICIPAL"
      - método `construir_paginas() -> list[PageFn]`: ordem das páginas.

    Subclasses NÃO devem reescrever `gerar()`.
    """

    titulo_publicacao: str = "FNP — FOLHETO INSTITUCIONAL"

    def __init__(self, dados: dict, output_path: Path | None = None, tamanho: str = "A4"):
        self.d = dados
        # Sistema de coordenadas interno — SEMPRE A4 (`PAGE_SIZE`), mesmo
        # gerando em A3. Nenhum componente/tema precisa saber do tamanho
        # físico: `gerar()` escala o canvas inteiro na hora de desenhar (ver
        # abaixo), não redesenha nada em coordenadas maiores. Isso evita
        # reescrever STRIPE_W/MARGIN/CONTENT_W (e todo `components.py`) para
        # aceitar um tamanho de página variável.
        self.W, self.H = PAGE_SIZE
        self.tamanho = tamanho if tamanho in TAMANHOS_VALIDOS else "A4"
        self.output_path = output_path or self._default_output()
        register_fonts()

    def _output_name(self) -> tuple[str, str]:
        """Subclasse pode sobrescrever pra adaptar ao seu schema. Default lê (nome, uf) da raiz."""
        return self.d.get("nome", "folheto"), self.d.get("uf", "")

    def _default_output(self) -> Path:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        nome, uf = self._output_name()
        nome = (nome or "folheto").replace(" ", "_")
        sufixo = f"_{uf}" if uf else ""
        # Sufixo de tamanho só quando NÃO é o padrão — preserva o nome de
        # arquivo já em uso por quem gera em A4 (a maioria).
        sufixo_tamanho = "_A3" if self.tamanho == "A3" else ""
        return OUTPUT_DIR / f"{self.__class__.__name__}_{nome}{sufixo}{sufixo_tamanho}.pdf"

    def construir_paginas(self) -> list[PageFn]:
        """Subclasse implementa. Retorna lista ordenada de funções de página."""
        raise NotImplementedError("Subclasses devem implementar construir_paginas()")

    def gerar(self) -> Path:
        """Gera o PDF completo. Retorna o caminho do arquivo.

        Em A3, o canvas físico é o tamanho real de A3 e cada página é
        desenhada com uma escala uniforme aplicada (`c.scale`) — o mesmo
        design pensado para A4, ampliado proporcionalmente pro papel maior
        (prática comum de impressão: pôster A3 = A4 escalado, não um
        redesenho). A escala usa a proporção real ISO A3/A4 em cada eixo
        (~1.4142, ligeiramente diferente entre x/y por causa do
        arredondamento em cm da norma — diferença desprezível, < 0,01%)."""
        if self.tamanho == "A3":
            pagesize_fisico = A3
            fator_x, fator_y = A3[0] / self.W, A3[1] / self.H
        else:
            pagesize_fisico = (self.W, self.H)
            fator_x = fator_y = 1.0

        c = rl_canvas.Canvas(str(self.output_path), pagesize=pagesize_fisico)

        for n, page_fn in enumerate(self.construir_paginas(), start=1):
            c.saveState()
            c.scale(fator_x, fator_y)
            page_fn(c, n)
            c.restoreState()
            c.showPage()

        c.save()
        return self.output_path
