from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_GET, require_POST

from .models import Edicion, Categoria, Votacion
from .servicios import VotoRechazado, registrar_voto, validar_voto, ya_voto_en_categoria


# Página de inicio: lista de ediciones del Festival
def inicio(request):
    ediciones = Edicion.objects.all()
    return render(request, 'votaciones/inicio.html', {'ediciones': ediciones})


# Categorías de una edición
def detalle_edicion(request, anio):
    edicion = get_object_or_404(Edicion, anio=anio)
    categorias = edicion.categorias.all()
    votadas = set()
    if request.user.is_authenticated:
        votadas = set(request.user.votos.filter(edicion=edicion).values_list('categoria_id', flat=True))
    return render(request, 'votaciones/edicion.html', {
        'edicion': edicion, 'categorias': categorias, 'votadas': votadas,
    })


# Votaciones de una categoría
def detalle_categoria(request, id):
    categoria = get_object_or_404(Categoria, id=id)
    votaciones = categoria.votaciones.all()
    voto = None
    if request.user.is_authenticated:
        voto = request.user.votos.filter(categoria=categoria, edicion=categoria.edicion).first()
    return render(request, 'votaciones/categoria.html', {
        'categoria': categoria, 'votaciones': votaciones, 'voto': voto,
    })


# Detalle de una votación con sus opciones y el formulario para votar
def detalle_votacion(request, id):
    votacion = get_object_or_404(Votacion.objects.select_related('categoria__edicion'), id=id)
    opciones = votacion.opciones.all()
    voto = None
    if request.user.is_authenticated:
        voto = request.user.votos.filter(categoria=votacion.categoria, edicion=votacion.categoria.edicion).first()
    return render(request, 'votaciones/votacion.html', {
        'votacion': votacion,
        'opciones': opciones,
        'voto': voto,
        'habilitada': votacion.esta_habilitada(),
    })


# Paso 1: el usuario eligió una opción. Se valida y se pide confirmación.
@login_required
def confirmar_voto(request, id):
    votacion = get_object_or_404(Votacion.objects.select_related('categoria__edicion'), id=id)
    # Si llega por GET (por ejemplo, cuando vuelve del login) no se hace nada:
    # se devuelve a la votación para que elija su opción otra vez.
    if request.method != 'POST':
        messages.info(request, 'Ya inició sesión. Ahora elija su opción y continúe con el voto.')
        return redirect('detalle_votacion', id=votacion.id)
    try:
        opcion = validar_voto(request.user, votacion, request.POST.get('opcion'))
    except VotoRechazado as error:
        messages.error(request, str(error))
        return redirect('detalle_votacion', id=votacion.id)
    return render(request, 'votaciones/confirmar.html', {'votacion': votacion, 'opcion': opcion})


# Paso 2: el usuario confirmó. Se valida otra vez y se guarda en MySQL.
@login_required
@require_POST
def registrar(request, id):
    votacion = get_object_or_404(Votacion.objects.select_related('categoria__edicion'), id=id)
    try:
        voto = registrar_voto(request.user, votacion, request.POST.get('opcion'))
    except VotoRechazado as error:
        messages.error(request, str(error))
        return redirect('detalle_votacion', id=votacion.id)
    messages.success(
        request,
        f'Voto registrado: "{voto.opcion.nombre}" en la categoría "{voto.categoria.nombre}" ({voto.edicion.anio}).',
    )
    return redirect('mis_votos')


# Historial de participación del usuario
@login_required
def mis_votos(request):
    votos = request.user.votos.select_related('edicion', 'categoria', 'votacion', 'opcion')
    return render(request, 'votaciones/mis_votos.html', {'votos': votos})


# API GET: categorías con sus votaciones y opciones, en JSON, leídas de MySQL.
# Filtro opcional: /api/categorias/?edicion=2027
@require_GET
def api_categorias(request):
    categorias = (
        Categoria.objects.select_related('edicion')
        .prefetch_related('votaciones__opciones')
        .order_by('-edicion__anio', 'id')
    )
    anio = request.GET.get('edicion')
    if anio:
        if not anio.isdigit():
            return JsonResponse({'error': 'El parámetro edicion debe ser un año numérico.'}, status=400)
        categorias = categorias.filter(edicion__anio=int(anio))

    datos = []
    for categoria in categorias:
        datos.append({
            'id': categoria.id,
            'nombre': categoria.nombre,
            'descripcion': categoria.descripcion,
            'edicion': {
                'id': categoria.edicion.id,
                'anio': categoria.edicion.anio,
                'nombre': categoria.edicion.nombre,
            },
            'votaciones': [
                {
                    'id': votacion.id,
                    'titulo': votacion.titulo,
                    'estado': votacion.estado,
                    'habilitada': votacion.esta_habilitada(),
                    'fecha_inicio': votacion.fecha_inicio.isoformat(),
                    'fecha_cierre': votacion.fecha_cierre.isoformat(),
                    'opciones': [
                        {'id': opcion.id, 'nombre': opcion.nombre, 'descripcion': opcion.descripcion}
                        for opcion in votacion.opciones.all()
                    ],
                }
                for votacion in categoria.votaciones.all()
            ],
        })

    return JsonResponse(
        {'total': len(datos), 'categorias': datos},
        json_dumps_params={'ensure_ascii': False, 'indent': 2},
    )
