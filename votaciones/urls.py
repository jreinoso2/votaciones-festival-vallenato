from django.urls import path

from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('edicion/<int:anio>/', views.detalle_edicion, name='detalle_edicion'),
    path('categoria/<int:id>/', views.detalle_categoria, name='detalle_categoria'),
    path('votacion/<int:id>/', views.detalle_votacion, name='detalle_votacion'),
]
