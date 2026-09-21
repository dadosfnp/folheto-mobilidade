#!/usr/bin/env python
"""Utilitário de linha de comando do Django — back-office de edição de
dados do Folheto Mobilidade. Ver CLAUDE.md, Decisão 4."""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Não consegui importar o Django. Ele está instalado e ativado "
            "no seu ambiente virtual? Rode: pip install -r requirements.txt"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
