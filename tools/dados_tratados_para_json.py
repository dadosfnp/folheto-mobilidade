"""
Lê os dados tratados pela equipe (SIM/SIH já agregados em `data/external/`,
extração original em `data/raw/`) e escreve os JSONs de município em
`data/mobilidade/<slug>.json`, batendo campo a campo com `SCHEMA.md`.

Fontes usadas (todas em `data/external/`, geradas fora deste repo — ver
`data/raw/README` para a extração original):
  - populacao_anual.xlsx           -> populacao.valor / populacao.ano
  - area_municipal_2024.xlsx       -> area_km2
  - indicadores_frota.xlsx         -> frota.evolucao_pct (sheet
                                       'crescimento_frota') e frota.atual
                                       (sheet 'serie_frota', ano mais recente)
  - indicadores_sim_relatorio.xlsx -> mortalidade_2024 (sheet
                                       'comparativo_municipios', ano=2024) e
                                       mortes_serie_historica (sheet
                                       'serie_historica')
  - indicadores_sih_relatorio.xlsx -> internacoes_2025 (sheet
                                       'comparativo_municipios', ano mais
                                       recente) e internacoes_serie_historica
                                       (sheet 'serie_historica', modo=total)

Campos do SCHEMA.md que NENHUMA dessas fontes cobre — ficam `null` de
propósito, nunca estimados:
  - ranking_causas_morte           (precisa de dado da Secretaria Municipal
                                     de Saúde, não é DATASUS agregado)
  - internacoes_serie_historica.gestao_atual (início/fim do mandato do
                                     prefeito atual — dado político, não
                                     fiscal/de saúde; preencher à mão ou
                                     pelo formulário Django quando souber)
  - problema.citacao, metodologia, _capa_foto, custo_hospitalar,
    internacoes_por_bairro         (fora do escopo desta fonte de dados)

Uso:
    python tools/dados_tratados_para_json.py                    # todos os pilotos
    python tools/dados_tratados_para_json.py --municipio campinas
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
EXTERNAL_DIR = ROOT / "data" / "external"
DIR_DADOS = ROOT / "data" / "mobilidade"

URL_PADRAO = "https://fnp.org.br/mobilidade"

# Pilotos deste projeto (ver CLAUDE.md). Adicionar aqui quando o escopo
# crescer — nada no resto do script depende de serem só dois.
PILOTOS = {
    "campinas": {"id_municipio": 3509502, "nome": "Campinas", "uf": "SP"},
    "montes_claros": {"id_municipio": 3143302, "nome": "Montes Claros", "uf": "MG"},
}

MODOS = ("total", "motociclistas", "pedestres", "ciclistas")
PERIODOS_FROTA = ("2003_2010", "2011_2020", "2021_2025", "2003_2025")
_PERIODO_PARA_CHAVE = {"2003-2010": "2003_2010", "2011-2020": "2011_2020",
                       "2021-2025": "2021_2025", "2003-2025": "2003_2025"}
_MODO_FROTA_PARA_SCHEMA = {"frota_total": "total", "automoveis": "automoveis",
                           "motocicletas": "motocicletas"}


def _n(v):
    """NaN/NaT do pandas -> None do Python (json.dumps não entende NaN)."""
    return None if pd.isna(v) else v


def _round1(v):
    v = _n(v)
    return None if v is None else round(float(v), 1)


def _int_ou_none(v):
    v = _n(v)
    return None if v is None else int(v)


class FontesAusentes(Exception):
    pass


def _carregar_planilhas() -> dict[str, pd.DataFrame | pd.ExcelFile]:
    obrigatorias = {
        "populacao": EXTERNAL_DIR / "populacao_anual.xlsx",
        "area": EXTERNAL_DIR / "area_municipal_2024.xlsx",
        "frota": EXTERNAL_DIR / "indicadores_frota.xlsx",
        "sim": EXTERNAL_DIR / "indicadores_sim_relatorio.xlsx",
        "sih": EXTERNAL_DIR / "indicadores_sih_relatorio.xlsx",
    }
    faltando = [str(p) for p in obrigatorias.values() if not p.exists()]
    if faltando:
        raise FontesAusentes(
            "Arquivo(s) não encontrado(s) em data/external/: " + ", ".join(faltando)
        )
    return {
        "populacao": pd.read_excel(obrigatorias["populacao"]),
        "area": pd.read_excel(obrigatorias["area"]),
        "frota_crescimento": pd.read_excel(obrigatorias["frota"], sheet_name="crescimento_frota"),
        "frota_serie": pd.read_excel(obrigatorias["frota"], sheet_name="serie_frota"),
        "sim_comparativo": pd.read_excel(obrigatorias["sim"], sheet_name="comparativo_municipios"),
        "sim_serie": pd.read_excel(obrigatorias["sim"], sheet_name="serie_historica"),
        "sih_comparativo": pd.read_excel(obrigatorias["sih"], sheet_name="comparativo_municipios"),
        "sih_serie": pd.read_excel(obrigatorias["sih"], sheet_name="serie_historica"),
    }


def _populacao(fontes, id_muni: int) -> dict:
    df = fontes["populacao"]
    sub = df[df.code_muni == id_muni].sort_values("Ano")
    if sub.empty:
        print(f"[aviso] população: município {id_muni} não encontrado em populacao_anual.xlsx", file=sys.stderr)
        return {"valor": None, "ano": None}
    ultimo = sub.iloc[-1]
    return {"valor": int(ultimo.Populacao), "ano": int(ultimo.Ano)}


def _area(fontes, id_muni: int):
    df = fontes["area"]
    sub = df[df.id_municipio == id_muni]
    if sub.empty:
        print(f"[aviso] área: município {id_muni} não encontrado em area_municipal_2024.xlsx", file=sys.stderr)
        return None
    return round(float(sub.iloc[0].area_km2), 1)


def _frota(fontes, id_muni: int) -> dict:
    cresc = fontes["frota_crescimento"]
    sub = cresc[cresc.id_municipio == id_muni]
    evolucao = {p: {"total": None, "automoveis": None, "motocicletas": None} for p in PERIODOS_FROTA}
    for _, row in sub.iterrows():
        periodo = _PERIODO_PARA_CHAVE.get(row.periodo)
        modo = _MODO_FROTA_PARA_SCHEMA.get(row.modo)
        if periodo and modo:
            evolucao[periodo][modo] = _round1(row.crescimento_acumulado)

    serie = fontes["frota_serie"]
    sub_serie = serie[serie.id_municipio == id_muni]
    atual = {"total": None, "automoveis": None, "motocicletas": None}
    if not sub_serie.empty:
        ano_mais_recente = sub_serie.ano.max()
        linha_atual = sub_serie[sub_serie.ano == ano_mais_recente]
        for _, row in linha_atual.iterrows():
            modo = _MODO_FROTA_PARA_SCHEMA.get(row.modo)
            if modo:
                atual[modo] = _int_ou_none(row.frota)
    else:
        print(f"[aviso] frota: município {id_muni} sem série em indicadores_frota.xlsx", file=sys.stderr)

    return {"evolucao_pct": evolucao, "atual": atual}


def _mortalidade_2024(fontes, id_muni: int) -> dict:
    df = fontes["sim_comparativo"]
    sub = df[(df.id_municipio == id_muni) & (df.ano == 2024)]
    resultado = {}
    for modo in MODOS:
        linha = sub[sub.modo == modo]
        if linha.empty:
            print(f"[aviso] mortalidade_2024: {id_muni}, modo '{modo}' ausente", file=sys.stderr)
            resultado[modo] = {
                "municipio": None,
                "rm": None, "rm_pos": None, "rm_total": None,
                "porte": None, "porte_pos": None, "porte_total": None,
                "estado": None, "estado_pos": None, "estado_total": None,
                "brasil": None, "brasil_pos": None, "brasil_total": None,
                "capitais": None, "capitais_pos": None, "capitais_total": None,
            }
            continue
        row = linha.iloc[0]
        resultado[modo] = {
            "municipio": _round1(row.taxa_municipio),
            "rm": _round1(row.taxa_recorte_metropolitano),
            "rm_pos": _int_ou_none(row.rank_recorte), "rm_total": _int_ou_none(row.n_recorte),
            "porte": _round1(row.taxa_mesmo_porte),
            "porte_pos": _int_ou_none(row.rank_porte), "porte_total": _int_ou_none(row.n_porte),
            "estado": _round1(row.taxa_estado),
            "estado_pos": _int_ou_none(row.rank_estado), "estado_total": _int_ou_none(row.n_estado),
            "brasil": _round1(row.taxa_brasil),
            "brasil_pos": _int_ou_none(row.rank_brasil), "brasil_total": _int_ou_none(row.n_brasil),
            "capitais": _round1(row.taxa_capitais),
            "capitais_pos": _int_ou_none(row.rank_capitais), "capitais_total": _int_ou_none(row.n_capitais),
        }
    return resultado


def _mortes_serie_historica(fontes, id_muni: int) -> dict:
    df = fontes["sim_serie"]
    sub = df[df.id_municipio == id_muni]
    if sub.empty:
        print(f"[aviso] mortes_serie_historica: município {id_muni} sem série no SIM", file=sys.stderr)
        return {"anos": [], "total": [], "motociclistas": [], "pedestres": [], "ciclistas": []}
    anos = sorted(sub.ano.unique().tolist())
    serie = {"anos": [int(a) for a in anos]}
    for modo in MODOS:
        por_ano = sub[sub.modo == modo].set_index("ano")["obitos"]
        serie[modo] = [_int_ou_none(por_ano.get(a)) for a in anos]
    return serie


def _internacoes_2025(fontes, id_muni: int) -> dict:
    df = fontes["sih_comparativo"]
    sub_muni = df[df.id_municipio == id_muni]
    if sub_muni.empty:
        print(f"[aviso] internacoes: município {id_muni} sem dado no SIH", file=sys.stderr)
        return {m: {"municipio": None, "porte": None, "estado": None, "brasil": None} for m in MODOS}
    ano_mais_recente = int(sub_muni.ano.max())
    sub = sub_muni[sub_muni.ano == ano_mais_recente]
    resultado = {}
    for modo in MODOS:
        linha = sub[sub.modo == modo]
        if linha.empty:
            resultado[modo] = {"municipio": None, "porte": None, "estado": None, "brasil": None}
            continue
        row = linha.iloc[0]
        resultado[modo] = {
            "municipio": _round1(row.taxa_municipio),
            "porte": _round1(row.taxa_mesmo_porte),
            "estado": _round1(row.taxa_estado),
            "brasil": _round1(row.taxa_brasil),
        }
    return resultado, ano_mais_recente


def _internacoes_serie_historica(fontes, id_muni: int) -> dict:
    df = fontes["sih_serie"]
    sub = df[(df.id_municipio == id_muni) & (df.modo == "total")].sort_values("ano")
    if sub.empty:
        print(f"[aviso] internacoes_serie_historica: município {id_muni} sem série no SIH", file=sys.stderr)
        return {"anos": [], "total": [], "gestao_atual": {"inicio": None, "fim": None}}
    return {
        "anos": [int(a) for a in sub.ano],
        "total": [_int_ou_none(v) for v in sub.internacoes],
        # Início/fim do mandato do prefeito atual não vem de nenhuma fonte
        # DATASUS/SENATRAN — é dado político, preencher à mão ou pelo
        # formulário Django quando confirmado.
        "gestao_atual": {"inicio": None, "fim": None},
    }


def montar_municipio(fontes, slug: str, config: dict) -> dict:
    id_muni = config["id_municipio"]
    internacoes, ano_internacoes = _internacoes_2025(fontes, id_muni)

    return {
        "_nota_proveniencia": (
            "Gerado por tools/dados_tratados_para_json.py a partir de data/external/ "
            "(populacao_anual.xlsx, area_municipal_2024.xlsx, indicadores_frota.xlsx, "
            "indicadores_sim_relatorio.xlsx, indicadores_sih_relatorio.xlsx) — nenhum "
            "valor foi estimado ou completado por fora dessas planilhas. Campos que "
            "essas fontes não cobrem (ranking_causas_morte, gestao_atual do prefeito, "
            "problema.citacao, metodologia, custo_hospitalar, internacoes_por_bairro) "
            "ficaram null de propósito — não são estimáveis a partir de SIM/SIH/SENATRAN."
        ),
        "nome": config["nome"],
        "uf": config["uf"],
        "populacao": _populacao(fontes, id_muni),
        "area_km2": _area(fontes, id_muni),
        "frota": _frota(fontes, id_muni),
        "mortalidade_2024": _mortalidade_2024(fontes, id_muni),
        "mortes_serie_historica": _mortes_serie_historica(fontes, id_muni),
        "internacoes_2025": internacoes,
        "internacoes_serie_historica": _internacoes_serie_historica(fontes, id_muni),
        "ranking_causas_morte": {
            "fonte": None,
            "total_causas": None,
            "_nota": "Não coberto por SIM/SIH/SENATRAN — precisa de dado da Secretaria "
                     "Municipal de Saúde local (como o exemplo de Fortaleza usou).",
            "posicao_acidentes_transito": {},
        },
        "leitos_uti_hipotetico": {
            "nota": "Pergunta orientadora do projeto (item 8 do briefing): se não houvesse "
                    "acidentes de trânsito, quantos leitos de UTI ficariam disponíveis para "
                    "outras doenças? Cálculo pendente do dado de internação consolidado."
        },
        "url": URL_PADRAO,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--municipio", choices=sorted(PILOTOS), action="append",
                   help="Gerar só este piloto (repetível). Sem isso, gera todos.")
    args = p.parse_args()

    try:
        fontes = _carregar_planilhas()
    except FontesAusentes as e:
        sys.exit(f"[erro] {e}")

    alvos = args.municipio or sorted(PILOTOS)
    DIR_DADOS.mkdir(parents=True, exist_ok=True)

    for slug in alvos:
        config = PILOTOS[slug]
        dados = montar_municipio(fontes, slug, config)
        destino = DIR_DADOS / f"{slug}.json"
        with destino.open("w", encoding="utf-8", newline="\n") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"[ok] {destino}")


if __name__ == "__main__":
    main()
