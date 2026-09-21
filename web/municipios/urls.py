from django.urls import path

from . import views

app_name = "municipios"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("<slug:slug>/preview/", views.preview_pdf, name="preview_pdf"),
    path("<slug:slug>/pdf/", views.baixar_pdf, name="baixar_pdf"),
]
