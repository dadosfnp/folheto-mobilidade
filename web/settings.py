"""
Configuração do back-office Django — ferramenta interna, rodada localmente
pela equipe da FNP via `python manage.py runserver`, só pra listar
municípios e gerar/baixar o PDF. Sem edição de dado nenhuma (ver
CLAUDE.md, Decisão 4) — os dados só mudam via
`tools/dados_tratados_para_json.py` ou edição direta do arquivo. Nunca é
exposta publicamente (a distribuição pública é a Parte 2 — site estático
em docs/ — não este app).

Sem banco de dados: `DATABASES = {}` é suficiente — o Django cai no backend
"dummy" e os `system checks`/`runserver` não exigem migração (verificado
antes de assumir isto, ver plano de implementação). Os dados continuam em
`data/mobilidade/*.json`, nunca em tabela.
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # raiz do repositório

# Ferramenta local, sem login e sem sessão: esta chave não protege segredo
# nenhum — só assina o token CSRF do formulário. Não é credencial real.
SECRET_KEY = "folheto-mobilidade-uso-local-apenas"
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

INSTALLED_APPS = [
    "django.contrib.staticfiles",  # serve o CSS da lista de municípios
    "web.municipios",
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
]

ROOT_URLCONF = "web.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {},
    }
]

DATABASES = {}

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
