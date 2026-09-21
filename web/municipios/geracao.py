"""
Ponte para o motor de geração de PDF existente (`python/`). Não reimplementa
nada — chama `gerar_um`, exatamente como `python/gerar.py` faz na linha de
comando, para herdar de graça o carregamento dos "companheiros" `_*.json`
(ver `gerar.py::_companheiros_disponiveis`).

`python/` não é um pacote Python formal (sem `__init__.py`) — o próprio
`gerar.py` se resolve inserindo a si mesmo no `sys.path`; fazemos o mesmo
aqui do lado Django.
"""
from __future__ import annotations

import contextlib
import io
import sys
import threading
from pathlib import Path

from django.conf import settings

_PYTHON_DIR = Path(settings.BASE_DIR) / "python"
if str(_PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(_PYTHON_DIR))

from gerar import gerar_um  # noqa: E402
from temas import TEMAS  # noqa: E402

TEMA = "mobilidade"
URL_PADRAO = TEMAS[TEMA].URL_PADRAO

# `gerar_um` escreve em `sys.stderr`, que é estado global do processo —
# sem a trava, dois "Gerar PDF" simultâneos (runserver é multithread por
# padrão) poderiam cruzar avisos de um município com os de outro.
_trava = threading.Lock()


def caminho_pdf(dados: dict) -> Path:
    """Onde o PDF deste município vai parar, sem gerar nada — só instancia
    a classe do tema e lê `output_path` (mesma regra de nome usada por
    `.gerar()`). Útil pra saber se já existe PDF e comparar `mtime`."""
    return TEMAS[TEMA](dados).output_path


def gerar_pdf(dados_path: Path) -> tuple[Path, list[str]]:
    """Gera o PDF reaproveitando `gerar_um` (não a classe direto — é ele
    quem carrega os companheiros `_*.json`). Retorna (caminho_do_pdf,
    avisos) — os avisos são a mesma coisa que hoje só aparece no console de
    quem roda `python python/gerar.py`; aqui vão para a tela também
    (degradação nunca deve ser silenciosa, ver CLAUDE.md)."""
    buf = io.StringIO()
    with _trava:
        try:
            with contextlib.redirect_stderr(buf):
                pdf = gerar_um(TEMA, str(dados_path))
        finally:
            sys.stderr.write(buf.getvalue())
    avisos = [l for l in buf.getvalue().splitlines() if l.strip()]
    return pdf, avisos
