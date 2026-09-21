from django.http import FileResponse, Http404
from django.shortcuts import render

from . import armazenamento, geracao
from core.base_folheto import TAMANHOS_VALIDOS  # noqa: E402 — geracao.py já ajusta o sys.path


def lista(request):
    municipios = armazenamento.listar_municipios()
    for m in municipios:
        if "erro" in m:
            continue
        # Nome do arquivo de saída só depende de nome/uf (ver
        # FolhetoFNP._default_output) — não precisa recarregar os dados
        # inteiros só pra saber se o PDF existe. Só informativo agora: como
        # "Preview" e "Baixar PDF" sempre regeneram na hora (ver
        # `_gerar_e_servir`), não existe mais um estado "desatualizado" —
        # esse dot só diz se já foi gerado alguma vez.
        pdf = geracao.caminho_pdf({"nome": m["nome"], "uf": m["uf"]})
        m["pdf_existe"] = pdf.exists()
    return render(request, "municipios/lista.html", {"municipios": municipios})


def _gerar_e_servir(request, slug: str, *, inline: bool):
    """Gera o PDF na hora, sempre a partir do JSON atual, e devolve como
    resposta HTTP — nunca serve um arquivo potencialmente desatualizado do
    disco. `inline=True` abre no visualizador de PDF do próprio navegador
    (preview, nova aba); `inline=False` força o download. Substitui o botão
    "Gerar de novo" que existia antes: gerar deixou de ser um passo manual
    separado, é a mesma ação que ver/baixar (pedido do usuário — o PDF devia
    "atualizar automaticamente"). `?tamanho=A3` na URL gera em A3 (o mesmo
    design, escalado — ver core/base_folheto.py); qualquer outro valor cai
    em A4."""
    caminho = armazenamento.caminho(slug)
    if not caminho.exists():
        raise Http404(f"Município '{slug}' não encontrado.")
    tamanho = request.GET.get("tamanho", "A4")
    if tamanho not in TAMANHOS_VALIDOS:
        tamanho = "A4"
    try:
        pdf, avisos = geracao.gerar_pdf(caminho, tamanho=tamanho)
    except Exception as e:
        return render(request, "municipios/erro_geracao.html",
                       {"slug": slug, "erro": str(e)}, status=500)
    return FileResponse(open(pdf, "rb"), as_attachment=not inline,
                         filename=pdf.name, content_type="application/pdf")


def preview_pdf(request, slug):
    return _gerar_e_servir(request, slug, inline=True)


def baixar_pdf(request, slug):
    return _gerar_e_servir(request, slug, inline=False)
