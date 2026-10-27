from django.shortcuts import render, get_object_or_404

from .models import Edicion, Categoria, Votacion


# Página de inicio: lista de ediciones del Festival
def inicio(request):
    ediciones = Edicion.objects.all()
    return render(request, 'votaciones/inicio.html', {'ediciones': ediciones})


# Categorías de una edición
def detalle_edicion(request, anio):
    edicion = get_object_or_404(Edicion, anio=anio)
    categorias = edicion.categorias.all()
    return render(request, 'votaciones/edicion.html', {'edicion': edicion, 'categorias': categorias})


# Votaciones de una categoría
def detalle_categoria(request, id):
    categoria = get_object_or_404(Categoria, id=id)
    votaciones = categoria.votaciones.all()
    return render(request, 'votaciones/categoria.html', {'categoria': categoria, 'votaciones': votaciones})


# Detalle de una votación con sus opciones
def detalle_votacion(request, id):
    votacion = get_object_or_404(Votacion, id=id)
    opciones = votacion.opciones.all()
    return render(request, 'votaciones/votacion.html', {'votacion': votacion, 'opciones': opciones})
