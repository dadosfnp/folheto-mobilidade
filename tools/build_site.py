"""
Gera o índice do site estático de distribuição (`docs/`) a partir dos JSONs
em `data/mobilidade/` e dos PDFs em `output/`.

Adaptado de `tools/build_site.py` do folheto-ifem (mesmo padrão: PDFs
hospedados em GitHub Releases — grátis, sem limite de tamanho pra repo
público — este script só escreve o índice JSON que a página lê).
Diferenças deliberadas em relação ao original, ver CLAUDE.md Decisão 4:

  - lê direto `data/mobilidade/*.json` (este projeto ainda não tem um
    `export_folheto/` de pipeline de tratamento separado);
  - nunca inclui `exemplo_fortaleza.json` — é dado de validação de
    pipeline, não um município publicável (mesma regra que já rege o PDF,
    ver SCHEMA.md);
  - prefere o remoto `production` (org `dadosfnp`) sobre `origin` (fork
    pessoal `brunofnp`) ao auto-detectar owner/repo — a distribuição
    pública tem que apontar pro repo da organização.

Saída:
  docs/folhetos.json   — índice de municípios disponíveis (lido pela página)
  docs/index.html      — UI estática (já existe; este script só atualiza o JSON)

Uso típico:
    1) Subir os PDFs como assets de uma release no GitHub — ver
       tools/publicar_release.ps1.
    2) Rodar:
         python tools/build_site.py --release-tag v1
       (owner/repo são auto-detectados dos remotos git; sobrescreva com
        --owner / --repo se necessário.)
"""
import argparse
import json
import re
import subprocess
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIR_DADOS = ROOT / "data" / "mobilidade"
OUTPUT_DIR = ROOT / "output"
SITE_DIR = ROOT / "docs"

EXCLUIR_PREFIXOS = ("_", "exemplo_")  # "_*" = companheiros; "exemplo_*" = dado de validação, não oficial


def _strip_acentos(s: str) -> str:
    """GitHub Releases remove diacríticos do nome do asset no upload —
    replicado aqui ou o link da landing dá 404 (mesma armadilha documentada
    no folheto-ifem)."""
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _slug_release(nome: str, uf: str) -> str:
    """Nome do asset tal como o GitHub Releases efetivamente armazena."""
    base = _strip_acentos(nome).replace(" ", "_")
    base = re.sub(r"[^A-Za-z0-9._-]", ".", base)
    return f"FolhetoMobilidade_{base}_{uf}.pdf"


def _pdf_filename_local(nome: str, uf: str) -> str:
    """Nome do arquivo tal como o gerador escreve em output/ — com
    acentos (ver FolhetoFNP._default_output)."""
    return f"FolhetoMobilidade_{nome.replace(' ', '_')}_{uf}.pdf"


def _detectar_owner_repo() -> tuple[str | None, str | None]:
    """Lê os remotos git e devolve (owner, repo), preferindo `production`
    (org `dadosfnp`) sobre `origin` (fork pessoal) — ver CLAUDE.md, tabela
    de remotos: a distribuição pública é o repo da organização."""
    for remoto in ("production", "origin"):
        try:
            url = subprocess.check_output(
                ["git", "remote", "get-url", remoto],
                cwd=ROOT, text=True, stderr=subprocess.DEVNULL,
            ).strip()
        except Exception:
            continue
        m = re.search(r"github\.com[:/]([^/]+)/([^/.\s]+)(?:\.git)?$", url)
        if m:
            return m.group(1), m.group(2)
    return (None, None)


def _carregar_municipios() -> list[dict]:
    """Lê data/mobilidade/*.json, excluindo companheiros (_*.json) e o
    arquivo de exemplo (exemplo_*.json — nunca dado publicável, ver
    SCHEMA.md)."""
    municipios = []
    if not DIR_DADOS.is_dir():
        return municipios
    for jpath in sorted(DIR_DADOS.glob("*.json")):
        if jpath.name.startswith(EXCLUIR_PREFIXOS):
            continue
        try:
            with jpath.open(encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"[skip] {jpath.name}: {e}", file=sys.stderr)
            continue
        municipios.append(d)
    return municipios


def build(release_tag: str, owner: str, repo: str) -> None:
    SITE_DIR.mkdir(exist_ok=True)

    municipios = _carregar_municipios()
    pdfs_disponiveis = {p.name for p in OUTPUT_DIR.glob("FolhetoMobilidade_*.pdf")} if OUTPUT_DIR.is_dir() else set()

    base_release_url = f"https://github.com/{owner}/{repo}/releases/download/{release_tag}/"

    itens = []
    for d in municipios:
        nome, uf = d.get("nome"), d.get("uf")
        if not nome or not uf:
            continue
        fname_local = _pdf_filename_local(nome, uf)
        if fname_local not in pdfs_disponiveis:
            continue  # sem PDF gerado ainda — não entra no índice (nunca linka pra um 404)
        fname_release = _slug_release(nome, uf)
        taxa_mortalidade = ((d.get("mortalidade_2024") or {}).get("total") or {}).get("municipio")
        itens.append({
            "municipio": nome,
            "uf": uf,
            "populacao": (d.get("populacao") or {}).get("valor"),
            "taxa_mortalidade_total": taxa_mortalidade,
            "pdf": base_release_url + fname_release,
            "pdf_filename": fname_release,
        })

    # Cidades maiores primeiro — mesma convenção do folheto-ifem (as mais procuradas).
    itens.sort(key=lambda x: -(x["populacao"] or 0))

    indice = {
        "total": len(itens),
        "release_tag": release_tag,
        "owner": owner,
        "repo": repo,
        "atualizado": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "municipios": itens,
    }

    out_json = SITE_DIR / "folhetos.json"
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(indice, f, ensure_ascii=False, indent=2)

    print(f"[ok] {out_json} — {len(itens)} município(s)")
    if not itens:
        print("[aviso] índice vazio — nenhum município real com PDF gerado ainda "
              "(esperado até Campinas/Montes Claros terem dado e PDF).", file=sys.stderr)


def main():
    auto_owner, auto_repo = _detectar_owner_repo()

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--release-tag", required=True, help="Tag da release do GitHub que contém os PDFs (ex.: v1).")
    p.add_argument("--owner", default=auto_owner, help=f"Owner do repo no GitHub (auto: {auto_owner!r}).")
    p.add_argument("--repo", default=auto_repo, help=f"Nome do repo no GitHub (auto: {auto_repo!r}).")
    args = p.parse_args()

    if not args.owner or not args.repo:
        sys.exit("Owner/repo do GitHub não detectados (remotos 'production'/'origin' ausentes). Passe --owner e --repo.")

    build(release_tag=args.release_tag, owner=args.owner, repo=args.repo)


if __name__ == "__main__":
    main()
