from django.urls import path

from . import views

# Todas estas rutas quedan debajo de /gestion/
urlpatterns = [
    path('', views.panel, name='gestion_panel'),

    path('ediciones/', views.ediciones, name='gestion_ediciones'),
    path('ediciones/nueva/', views.edicion_crear, name='gestion_edicion_crear'),
    path('ediciones/<int:id>/editar/', views.edicion_editar, name='gestion_edicion_editar'),
    path('ediciones/<int:id>/eliminar/', views.edicion_eliminar, name='gestion_edicion_eliminar'),

    path('categorias/', views.categorias, name='gestion_categorias'),
    path('categorias/nueva/', views.categoria_crear, name='gestion_categoria_crear'),
    path('categorias/<int:id>/editar/', views.categoria_editar, name='gestion_categoria_editar'),
    path('categorias/<int:id>/eliminar/', views.categoria_eliminar, name='gestion_categoria_eliminar'),

    path('votaciones/', views.votaciones, name='gestion_votaciones'),
    path('votaciones/nueva/', views.votacion_crear, name='gestion_votacion_crear'),
    path('votaciones/<int:id>/editar/', views.votacion_editar, name='gestion_votacion_editar'),
    path('votaciones/<int:id>/eliminar/', views.votacion_eliminar, name='gestion_votacion_eliminar'),
    path('votaciones/<int:id>/estado/', views.votacion_cambiar_estado, name='gestion_votacion_estado'),

    path('opciones/', views.opciones, name='gestion_opciones'),
    path('opciones/nueva/', views.opcion_crear, name='gestion_opcion_crear'),
    path('opciones/<int:id>/editar/', views.opcion_editar, name='gestion_opcion_editar'),
    path('opciones/<int:id>/eliminar/', views.opcion_eliminar, name='gestion_opcion_eliminar'),

    path('votos/', views.votos, name='gestion_votos'),
    path('resultados/', views.resultados, name='gestion_resultados'),
    path('informe/', views.informe, name='gestion_informe'),

    path('usuarios/', views.usuarios, name='gestion_usuarios'),
    path('usuarios/<int:id>/personal/', views.usuario_cambiar_personal, name='gestion_usuario_personal'),
]
