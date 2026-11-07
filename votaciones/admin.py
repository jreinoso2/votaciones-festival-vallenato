from django.contrib import admin
from django.db.models import Count

from .models import Edicion, Categoria, Votacion, Opcion, Voto


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
    list_display = ['nombre', 'votacion', 'total_votos']
    list_filter = ['votacion']

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(num_votos=Count('votos'))

    @admin.display(description='total de votos', ordering='num_votos')
    def total_votos(self, obj):
        return obj.num_votos


# Consulta administrativa de los votos.
# Es de solo lectura: el administrador no puede crear ni modificar votos a mano,
# así los datos que ve son exactamente los registrados por los usuarios en MySQL.
@admin.register(Voto)
class VotoAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'edicion', 'categoria', 'votacion', 'opcion', 'fecha']
    list_filter = ['edicion', 'categoria', 'votacion']
    search_fields = ['usuario__username', 'opcion__nombre']
    readonly_fields = ['usuario', 'edicion', 'categoria', 'votacion', 'opcion', 'fecha']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
