"""
CLI unificada: gera folhetos de qualquer tema a partir de JSON de dados.

Uso:
    python python/gerar.py --tema mobilidade --dados data/mobilidade/campinas.json
    python python/gerar.py --tema mobilidade --lote "data/mobilidade/*.json"

Para listar os temas disponíveis:
    python python/gerar.py --listar

Adicionar um tema novo: ver python/temas/__init__.py.
"""
import argparse
import glob
import json
import sys
from pathlib import Path

# Permite executar tanto como módulo (-m) quanto como script direto.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from temas import TEMAS  # noqa: E402

ROOT_DIR = Path(__file__).resolve().parent.parent


def carregar_json(path: str) -> dict:
    """Carrega arquivo de dados validando o JSON."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Arquivo de dados não encontrado: {p}")
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def _companheiros_disponiveis(dados_path: str, tema: str) -> dict[str, Path]:
    """
    Descobre os JSONs "companheiros" (ex.: `_metodologia.json`) — conteúdo
    compartilhado entre todos os municípios de um tema, nunca específico de
    um só. Convenção: qualquer arquivo começando com `_` numa das camadas
    abaixo, na ordem em que cada uma VENCE a anterior:

      1. `data/<tema>/` — fallback versionado no repo. É a fonte da verdade
         para companheiros que são conteúdo editorial e não saem de nenhum
         script (ex.: um texto de metodologia escrito à mão).
      2. Pasta do próprio --dados — onde caem companheiros gerados por um
         script de ingestão (ex.: agregados nacionais calculados junto com
         os municípios).

    Retorna {chave_sem_underscore_nem_extensao: caminho}.
    """
    achados: dict[str, Path] = {}
    camadas = [
        ROOT_DIR / "data" / tema,
        Path(dados_path).resolve().parent,
    ]
    for pasta in camadas:
        if not pasta.is_dir():
            continue
        for p in sorted(pasta.glob("_*.json")):
            achados[p.stem.lstrip("_")] = p  # última camada vence
    return achados


def gerar_um(tema: str, dados_path: str, tamanho: str = "A4") -> Path:
    if tema not in TEMAS:
        raise ValueError(
            f"Tema '{tema}' desconhecido. Disponíveis: {', '.join(TEMAS.keys())}"
        )
    Cls = TEMAS[tema]
    dados = carregar_json(dados_path)

    for chave, caminho in _companheiros_disponiveis(dados_path, tema).items():
        with caminho.open(encoding="utf-8") as f:
            dados[chave] = json.load(f)

    folheto = Cls(dados, tamanho=tamanho)
    out = folheto.gerar()
    print(f"[OK] {out}")
    return out


def _filtra_por_populacao(arquivos: list[str], minimo: int) -> list[str]:
    """
    Mantém só os municípios acima de `minimo` habitantes.

    Lê `populacao.valor` de cada JSON. Arquivo sem esse campo é descartado com
    aviso: melhor faltar no lote do que gerar um folheto de município que não
    deveria entrar no recorte.
    """
    selecionados = []
    for arq in arquivos:
        try:
            with open(arq, encoding="utf-8") as f:
                pop = (json.load(f).get("populacao") or {}).get("valor")
        except (OSError, json.JSONDecodeError) as e:
            print(f"[aviso] ignorando {Path(arq).name}: {e}", file=sys.stderr)
            continue
        if pop and pop > minimo:
            selecionados.append(arq)
    return selecionados


def main():
    parser = argparse.ArgumentParser(description="Gerador de folhetos FNP unificado")
    parser.add_argument("--tema",   type=str, help=f"Tema do folheto: {', '.join(TEMAS.keys())}")
    parser.add_argument("--dados",  type=str, help="Caminho do JSON de dados")
    parser.add_argument("--lote",   type=str, help="Glob de JSONs (ex.: 'data/ifem/*.json')")
    parser.add_argument("--pop-minima", type=int, default=None, metavar="N",
                        help="no lote, só municípios com população acima de N")
    parser.add_argument("--tamanho", type=str, default="A4", choices=("A4", "A3"),
                        help="tamanho físico do PDF — A3 escala o mesmo design (padrão: A4)")
    parser.add_argument("--listar", action="store_true", help="Lista temas registrados")
    args = parser.parse_args()

    if args.listar:
        print("Temas disponíveis:")
        for nome, cls in TEMAS.items():
            print(f"  - {nome:8s} -> {cls.__name__}")
        return

    if not args.tema:
        parser.error("--tema é obrigatório (use --listar para ver disponíveis)")

    if args.lote:
        arquivos = sorted(glob.glob(args.lote))
        # Companheiros compartilhados (_metodologia, _problema…) não são municípios.
        arquivos = [a for a in arquivos if not Path(a).name.startswith("_")]
        if not arquivos:
            sys.exit(f"Nenhum arquivo casou com o padrão: {args.lote}")

        if args.pop_minima:
            arquivos = _filtra_por_populacao(arquivos, args.pop_minima)
            if not arquivos:
                sys.exit(f"Nenhum município acima de {args.pop_minima:,} habitantes.")
            print(f"{len(arquivos)} município(s) acima de {args.pop_minima:,} habitantes.\n")

        total, falhas = len(arquivos), 0
        for i, arq in enumerate(arquivos, 1):
            try:
                gerar_um(args.tema, arq, tamanho=args.tamanho)
            except Exception as e:
                falhas += 1
                print(f"✗ Erro em {arq}: {e}", file=sys.stderr)
            if total > 20 and i % 50 == 0:
                print(f"    ... {i}/{total}", file=sys.stderr)
        if total > 1:
            print(f"\nConcluído: {total - falhas}/{total} folhetos"
                  + (f" ({falhas} falha(s))" if falhas else ""))
    elif args.dados:
        gerar_um(args.tema, args.dados, tamanho=args.tamanho)
    else:
        parser.error("Use --dados <arquivo.json> ou --lote <glob>")


if __name__ == "__main__":
    main()
