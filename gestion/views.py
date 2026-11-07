# Vistas del panel de gestion.
# El personal del festival (usuarios con is_staff) maneja todo desde aqui
# con formularios, sin entrar al admin de Django.

import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, ProtectedError
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from votaciones.models import Edicion, Categoria, Votacion, Opcion, Voto
from .forms import (EdicionForm, CategoriaForm, VotacionForm, OpcionForm,
                    FiltroVotosForm, InformeForm)


# Decorador que usamos en todas las vistas del panel:
# pide que el usuario haya iniciado sesion y que sea personal del festival.
def solo_personal(vista):
    @login_required
    def revisar(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'No tiene permiso para entrar al panel de gestión.')
            return redirect('inicio')
        return vista(request, *args, **kwargs)
    return revisar


# Funciones de ayuda para no repetir el mismo codigo en cada modelo

def guardar_formulario(request, clase_form, instancia, titulo, volver):
    """Muestra y procesa un formulario de crear o editar."""
    if request.method == 'POST':
        form = clase_form(request.POST, instance=instancia)
        if form.is_valid():
            objeto = form.save()
            if instancia is None:
                messages.success(request, f'Se creó correctamente: {objeto}')
            else:
                messages.success(request, f'Se guardaron los cambios de: {objeto}')
            return redirect(volver)
    else:
        form = clase_form(instance=instancia)
    return render(request, 'gestion/formulario.html', {
        'form': form, 'titulo': titulo, 'volver': volver,
    })


def eliminar_objeto(request, objeto, aviso, volver):
    """Pide confirmación y elimina. Si el objeto ya tiene votos, MySQL no
    deja borrarlo (on_delete=PROTECT) y se muestra un mensaje."""
    if request.method == 'POST':
        nombre = str(objeto)
        try:
            objeto.delete()
            messages.success(request, f'Se eliminó: {nombre}')
        except ProtectedError:
            messages.error(
                request,
                f'No se puede eliminar "{nombre}" porque ya tiene votos registrados. '
                'Si ya no debe recibir votos, cierre la votación en lugar de eliminarla.'
            )
        return redirect(volver)
    return render(request, 'gestion/eliminar.html', {
        'objeto': objeto, 'aviso': aviso, 'volver': volver,
    })


# Inicio del panel

@solo_personal
def panel(request):
    contexto = {
        'total_ediciones': Edicion.objects.count(),
        'total_categorias': Categoria.objects.count(),
        'total_votaciones': Votacion.objects.count(),
        'total_opciones': Opcion.objects.count(),
        'total_votos': Voto.objects.count(),
        'total_usuarios': User.objects.count(),
        'ultimos_votos': Voto.objects.select_related('usuario', 'categoria', 'opcion', 'edicion')[:5],
    }
    return render(request, 'gestion/panel.html', contexto)


# Ediciones

@solo_personal
def ediciones(request):
    lista = Edicion.objects.annotate(num_categorias=Count('categorias'))
    return render(request, 'gestion/ediciones.html', {'ediciones': lista})


@solo_personal
def edicion_crear(request):
    return guardar_formulario(request, EdicionForm, None, 'Nueva edición del festival', 'gestion_ediciones')


@solo_personal
def edicion_editar(request, id):
    edicion = get_object_or_404(Edicion, id=id)
    return guardar_formulario(request, EdicionForm, edicion, f'Modificar edición {edicion.anio}', 'gestion_ediciones')


@solo_personal
def edicion_eliminar(request, id):
    edicion = get_object_or_404(Edicion, id=id)
    aviso = 'Se eliminarán también todas sus categorías, votaciones y opciones.'
    return eliminar_objeto(request, edicion, aviso, 'gestion_ediciones')


# Categorías

@solo_personal
def categorias(request):
    lista = (Categoria.objects.select_related('edicion')
             .annotate(num_votaciones=Count('votaciones', distinct=True), num_votos=Count('votos', distinct=True))
             .order_by('-edicion__anio', 'nombre'))
    return render(request, 'gestion/categorias.html', {'categorias': lista})


@solo_personal
def categoria_crear(request):
    return guardar_formulario(request, CategoriaForm, None, 'Nueva categoría', 'gestion_categorias')


@solo_personal
def categoria_editar(request, id):
    categoria = get_object_or_404(Categoria, id=id)
    return guardar_formulario(request, CategoriaForm, categoria, f'Modificar categoría: {categoria.nombre}', 'gestion_categorias')


@solo_personal
def categoria_eliminar(request, id):
    categoria = get_object_or_404(Categoria, id=id)
    aviso = 'Se eliminarán también sus votaciones y opciones.'
    return eliminar_objeto(request, categoria, aviso, 'gestion_categorias')


# Votaciones (subeventos)

@solo_personal
def votaciones(request):
    lista = (Votacion.objects.select_related('categoria__edicion')
             .annotate(num_opciones=Count('opciones', distinct=True), num_votos=Count('votos', distinct=True))
             .order_by('-categoria__edicion__anio', 'categoria__nombre', 'titulo'))
    return render(request, 'gestion/votaciones.html', {'votaciones': lista})


@solo_personal
def votacion_crear(request):
    return guardar_formulario(request, VotacionForm, None, 'Nueva votación', 'gestion_votaciones')


@solo_personal
def votacion_editar(request, id):
    votacion = get_object_or_404(Votacion, id=id)
    return guardar_formulario(request, VotacionForm, votacion, f'Modificar votación: {votacion.titulo}', 'gestion_votaciones')


@solo_personal
def votacion_eliminar(request, id):
    votacion = get_object_or_404(Votacion, id=id)
    aviso = 'Se eliminarán también sus opciones.'
    return eliminar_objeto(request, votacion, aviso, 'gestion_votaciones')


@solo_personal
@require_POST
def votacion_cambiar_estado(request, id):
    """Botón rápido para abrir o cerrar una votación."""
    votacion = get_object_or_404(Votacion, id=id)
    votacion.estado = 'cerrada' if votacion.estado == 'abierta' else 'abierta'
    votacion.save()
    messages.success(request, f'La votación "{votacion.titulo}" ahora está {votacion.get_estado_display().lower()}.')
    return redirect('gestion_votaciones')


# Opciones

@solo_personal
def opciones(request):
    lista = (Opcion.objects.select_related('votacion__categoria__edicion')
             .annotate(num_votos=Count('votos'))
             .order_by('-votacion__categoria__edicion__anio', 'votacion__titulo', 'nombre'))
    return render(request, 'gestion/opciones.html', {'opciones': lista})


@solo_personal
def opcion_crear(request):
    return guardar_formulario(request, OpcionForm, None, 'Nueva opción', 'gestion_opciones')


@solo_personal
def opcion_editar(request, id):
    opcion = get_object_or_404(Opcion, id=id)
    return guardar_formulario(request, OpcionForm, opcion, f'Modificar opción: {opcion.nombre}', 'gestion_opciones')


@solo_personal
def opcion_eliminar(request, id):
    opcion = get_object_or_404(Opcion, id=id)
    return eliminar_objeto(request, opcion, '', 'gestion_opciones')


# Consulta de votos y resultados (solo lectura: los votos no se editan)

@solo_personal
def votos(request):
    form = FiltroVotosForm(request.GET or None)
    lista = Voto.objects.select_related('usuario', 'edicion', 'categoria', 'votacion', 'opcion')
    if form.is_valid():
        if form.cleaned_data['edicion']:
            lista = lista.filter(edicion=form.cleaned_data['edicion'])
        if form.cleaned_data['categoria']:
            lista = lista.filter(categoria=form.cleaned_data['categoria'])
        if form.cleaned_data['usuario']:
            lista = lista.filter(usuario__username__icontains=form.cleaned_data['usuario'])
    return render(request, 'gestion/votos.html', {'form': form, 'votos': lista})


def calcular_resultados(edicion):
    """Total de votos por opción de una edición, agrupado por categoría."""
    return (Opcion.objects.filter(votacion__categoria__edicion=edicion)
            .select_related('votacion__categoria')
            .annotate(total=Count('votos'))
            .order_by('votacion__categoria__nombre', 'votacion__titulo', '-total', 'nombre'))


@solo_personal
def resultados(request):
    lista_ediciones = Edicion.objects.all()
    anio = request.GET.get('edicion')
    if anio and anio.isdigit():
        edicion = get_object_or_404(Edicion, anio=int(anio))
    else:
        edicion = lista_ediciones.first()
    filas = calcular_resultados(edicion) if edicion else []
    return render(request, 'gestion/resultados.html', {
        'ediciones': lista_ediciones, 'edicion': edicion, 'filas': filas,
    })


@solo_personal
def informe(request):
    """Formulario para descargar el informe en CSV (se abre en Excel)."""
    if request.method == 'POST':
        form = InformeForm(request.POST)
        if form.is_valid():
            edicion = form.cleaned_data['edicion']
            tipo = form.cleaned_data['tipo']
            respuesta = HttpResponse(content_type='text/csv; charset=utf-8')
            respuesta['Content-Disposition'] = f'attachment; filename="informe_{tipo}_{edicion.anio}.csv"'
            respuesta.write('﻿')  # para que Excel muestre bien las tildes
            escritor = csv.writer(respuesta, delimiter=';')

            if tipo == 'resultados':
                escritor.writerow(['Edición', 'Categoría', 'Votación', 'Opción', 'Total de votos'])
                for opcion in calcular_resultados(edicion):
                    escritor.writerow([edicion.anio, opcion.votacion.categoria.nombre,
                                       opcion.votacion.titulo, opcion.nombre, opcion.total])
            else:
                escritor.writerow(['Fecha', 'Usuario', 'Edición', 'Categoría', 'Votación', 'Opción'])
                for voto in Voto.objects.filter(edicion=edicion).select_related('usuario', 'categoria', 'votacion', 'opcion'):
                    escritor.writerow([voto.fecha.strftime('%d/%m/%Y %H:%M'), voto.usuario.username, edicion.anio,
                                       voto.categoria.nombre, voto.votacion.titulo, voto.opcion.nombre])
            return respuesta
    else:
        form = InformeForm()
    return render(request, 'gestion/informe.html', {'form': form})


# Usuarios: el personal puede dar o quitar el permiso de "personal del festival"

@solo_personal
def usuarios(request):
    lista = User.objects.annotate(num_votos=Count('votos')).order_by('username')
    return render(request, 'gestion/usuarios.html', {'usuarios': lista})


@solo_personal
@require_POST
def usuario_cambiar_personal(request, id):
    usuario = get_object_or_404(User, id=id)
    if usuario == request.user:
        messages.error(request, 'No puede quitarse a sí mismo el permiso de personal.')
    elif usuario.is_superuser:
        messages.error(request, 'Al administrador principal no se le pueden cambiar los permisos desde aquí.')
    else:
        usuario.is_staff = not usuario.is_staff
        usuario.save()
        if usuario.is_staff:
            messages.success(request, f'{usuario.username} ahora es personal del festival.')
        else:
            messages.success(request, f'{usuario.username} ya no es personal del festival.')
    return redirect('gestion_usuarios')
