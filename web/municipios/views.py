from django.http import FileResponse, Http404
from django.views.decorators.http import require_POST
from django.shortcuts import render

from . import armazenamento, geracao


def _carregar_ou_404(slug: str) -> dict:
    try:
        return armazenamento.carregar(slug)
    except armazenamento.MunicipioNaoEncontrado:
        raise Http404(f"Município '{slug}' não encontrado.")
    except ValueError as e:
        raise Http404(str(e))


def lista(request):
    municipios = armazenamento.listar_municipios()
    for m in municipios:
        if "erro" in m:
            continue
        # Nome do arquivo de saída só depende de nome/uf (ver
        # FolhetoFNP._default_output) — não precisa recarregar os dados
        # inteiros só pra saber se o PDF existe.
        pdf = geracao.caminho_pdf({"nome": m["nome"], "uf": m["uf"]})
        m["pdf_existe"] = pdf.exists()
        m["pdf_desatualizado"] = m["pdf_existe"] and pdf.stat().st_mtime < m["mtime_json"]
    return render(request, "municipios/lista.html", {"municipios": municipios})


@require_POST
def gerar(request, slug):
    caminho = armazenamento.caminho(slug)
    if not caminho.exists():
        raise Http404(f"Município '{slug}' não encontrado.")
    try:
        pdf, avisos = geracao.gerar_pdf(caminho)
        erro = None
    except Exception as e:
        pdf, avisos, erro = None, [], str(e)
    return render(request, "municipios/resultado.html", {
        "slug": slug, "pdf": pdf, "avisos": avisos, "erro": erro,
    })


def baixar_pdf(request, slug):
    dados = _carregar_ou_404(slug)
    pdf = geracao.caminho_pdf(dados)
    if not pdf.exists():
        raise Http404('PDF ainda não gerado para este município. Use "Gerar PDF".')
    return FileResponse(open(pdf, "rb"), as_attachment=True,
                         filename=pdf.name, content_type="application/pdf")
