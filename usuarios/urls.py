from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('registro/', views.registro, name='registro'),
    # para el login y el logout usamos las vistas que ya trae Django
    path('login/', auth_views.LoginView.as_view(template_name='usuarios/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
