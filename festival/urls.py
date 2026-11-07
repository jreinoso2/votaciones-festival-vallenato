from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('usuarios/', include('usuarios.urls')),
    # panel para el personal del festival (con formularios propios)
    path('gestion/', include('gestion.urls')),
    path('', include('votaciones.urls')),
]
