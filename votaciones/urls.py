from django.urls import path

from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('edicion/<int:anio>/', views.detalle_edicion, name='detalle_edicion'),
    path('categoria/<int:id>/', views.detalle_categoria, name='detalle_categoria'),
    path('votacion/<int:id>/', views.detalle_votacion, name='detalle_votacion'),
    # registro de votos (solo POST, con CSRF y sesión iniciada)
    path('votacion/<int:id>/confirmar/', views.confirmar_voto, name='confirmar_voto'),
    path('votacion/<int:id>/votar/', views.registrar, name='registrar_voto'),
    path('mis-votos/', views.mis_votos, name='mis_votos'),
    # API GET de consulta
    path('api/categorias/', views.api_categorias, name='api_categorias'),
]
