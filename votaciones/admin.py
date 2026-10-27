from django.contrib import admin

from .models import Edicion, Categoria, Votacion, Opcion


# Las opciones se agregan desde la misma pantalla de la votación
class OpcionInline(admin.TabularInline):
    model = Opcion
    extra = 2


@admin.register(Edicion)
class EdicionAdmin(admin.ModelAdmin):
    list_display = ['anio', 'nombre', 'fecha_inicio', 'fecha_fin']


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'edicion']
    list_filter = ['edicion']


@admin.register(Votacion)
class VotacionAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'categoria', 'fecha_inicio', 'fecha_cierre', 'estado']
    list_filter = ['estado', 'categoria__edicion']
    inlines = [OpcionInline]


@admin.register(Opcion)
class OpcionAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'votacion']
    list_filter = ['votacion']
