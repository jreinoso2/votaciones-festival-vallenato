"""Reglas de negocio del registro de votos.

Toda la validación se hace aquí, en el servidor, para que no dependa de lo
que envíe el navegador. La vista llama a estas funciones.
"""

from django.db import IntegrityError, transaction

from .models import Opcion, Voto


class VotoRechazado(Exception):
    """Se lanza cuando un voto no cumple alguna regla de negocio."""


def ya_voto_en_categoria(usuario, categoria):
    """True si el usuario ya tiene un voto en esa categoría (y su edición)."""
    return Voto.objects.filter(
        usuario=usuario, categoria=categoria, edicion=categoria.edicion
    ).exists()


def validar_voto(usuario, votacion, opcion_id):
    """Revisa todas las reglas antes de guardar y devuelve la opción elegida.

    1. El usuario debe haber iniciado sesión.
    2. La votación debe estar abierta y dentro de sus fechas.
    3. La opción debe pertenecer a esa votación (y por lo tanto a su
       categoría y edición).
    4. El usuario no puede haber votado antes en la misma categoría y edición.
    """
    if not usuario.is_authenticated:
        raise VotoRechazado('Debe iniciar sesión para votar.')

    if not votacion.esta_habilitada():
        raise VotoRechazado('Esta votación no está habilitada: está cerrada o fuera de las fechas permitidas.')

    try:
        opcion = Opcion.objects.select_related('votacion__categoria__edicion').get(id=int(opcion_id))
    except (TypeError, ValueError, Opcion.DoesNotExist):
        raise VotoRechazado('La opción seleccionada no existe.')

    if opcion.votacion_id != votacion.id:
        raise VotoRechazado('La opción seleccionada no pertenece a esta votación ni a esta categoría.')

    if ya_voto_en_categoria(usuario, votacion.categoria):
        raise VotoRechazado(
            f'Usted ya votó en la categoría "{votacion.categoria.nombre}" '
            f'de la edición {votacion.categoria.edicion.anio}. Solo se permite un voto por categoría.'
        )

    return opcion


def registrar_voto(usuario, votacion, opcion_id):
    """Valida y guarda el voto en MySQL.

    Si llegan dos solicitudes al mismo tiempo, las dos pueden pasar la
    validación anterior, pero MySQL solo acepta un registro gracias al
    índice UNIQUE (usuario, categoria, edicion). La segunda inserción produce
    IntegrityError, que aquí se convierte en un rechazo normal.
    """
    opcion = validar_voto(usuario, votacion, opcion_id)
    categoria = votacion.categoria
    try:
        with transaction.atomic():
            return Voto.objects.create(
                usuario=usuario,
                edicion=categoria.edicion,
                categoria=categoria,
                votacion=votacion,
                opcion=opcion,
            )
    except IntegrityError:
        raise VotoRechazado(
            f'Usted ya votó en la categoría "{categoria.nombre}". El voto duplicado fue rechazado.'
        )
