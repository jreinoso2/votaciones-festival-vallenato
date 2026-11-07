"""Carga datos de prueba ficticios para demostrar el módulo de votaciones.

Uso:
    python manage.py cargar_datos_demo

Se puede ejecutar varias veces: no duplica registros (usa update_or_create).
Los nombres de participantes son ficticios.
"""

from datetime import date, datetime, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from votaciones.models import Edicion, Categoria, Votacion, Opcion


def fecha_hora(anio, mes, dia, hora=23, minuto=59):
    return timezone.make_aware(datetime(anio, mes, dia, hora, minuto))


class Command(BaseCommand):
    help = 'Crea ediciones, categorías, votaciones, opciones y usuarios de prueba (datos ficticios).'

    @transaction.atomic
    def handle(self, *args, **options):
        # La votación del público se abre de forma anticipada (desde hoy)
        # y cierra el 30 de abril de 2027, al terminar el Festival.
        apertura = timezone.now() - timedelta(days=1)
        cierre_2027 = fecha_hora(2027, 4, 30)

        e2027, _ = Edicion.objects.update_or_create(anio=2027, defaults={
            'nombre': 'Festival de la Leyenda Vallenata',
            'fecha_inicio': date(2027, 4, 26),
            'fecha_fin': date(2027, 4, 30),
        })
        e2026, _ = Edicion.objects.update_or_create(anio=2026, defaults={
            'nombre': 'Festival de la Leyenda Vallenata',
            'fecha_inicio': date(2026, 4, 27),
            'fecha_fin': date(2026, 5, 1),
        })

        # (edición, categoría, descripción, [(votación, estado, inicio, cierre, [opciones])])
        datos = [
            (e2027, 'Acordeón Profesional', 'Concurso principal de acordeoneros profesionales.', [
                ('Acordeonero favorito del público', 'abierta', apertura, cierre_2027,
                 ['Participante A', 'Participante B', 'Participante C']),
                ('Final - acordeonero favorito', 'abierta', apertura, cierre_2027,
                 ['Finalista A', 'Finalista B']),
            ]),
            (e2027, 'Canción Vallenata Inédita', 'Canciones originales presentadas en el Festival.', [
                ('Canción inédita favorita', 'abierta', apertura, cierre_2027,
                 ['Canción A', 'Canción B', 'Canción C', 'Canción D']),
            ]),
            (e2027, 'Piqueria', 'Duelo de versos improvisados.', [
                ('Mejor piquería del público', 'cerrada', apertura, cierre_2027,
                 ['Piquero A', 'Piquero B']),
            ]),
            (e2027, 'Acordeón Aficionado', 'Acordeoneros no profesionales.', [
                ('Aficionado favorito del público', 'abierta', apertura, cierre_2027,
                 ['Aficionado A', 'Aficionado B']),
            ]),
            (e2027, 'Cumbia', 'Agrupaciones de cumbia invitadas.', [
                ('Agrupación de cumbia favorita', 'abierta', apertura, cierre_2027,
                 ['Agrupación A', 'Agrupación B', 'Agrupación C']),
            ]),
            (e2026, 'Acordeón Profesional', 'Concurso principal de la edición anterior.', [
                ('Acordeonero favorito 2026', 'cerrada', fecha_hora(2026, 4, 1, 8, 0), fecha_hora(2026, 4, 30),
                 ['Participante X', 'Participante Y']),
            ]),
        ]

        for edicion, nombre_cat, descripcion, votaciones in datos:
            categoria, _ = Categoria.objects.update_or_create(
                edicion=edicion, nombre=nombre_cat, defaults={'descripcion': descripcion})
            for titulo, estado, inicio, cierre, opciones in votaciones:
                votacion, _ = Votacion.objects.update_or_create(
                    categoria=categoria, titulo=titulo,
                    defaults={'estado': estado, 'fecha_inicio': inicio, 'fecha_cierre': cierre},
                )
                for nombre_op in opciones:
                    Opcion.objects.get_or_create(votacion=votacion, nombre=nombre_op)

        # Usuarios votantes de prueba (contraseña ficticia, solo para la demostración)
        for username in ['votante1', 'votante2']:
            usuario, creado = User.objects.get_or_create(username=username)
            if creado:
                usuario.set_password('Festival2027*')
                usuario.save()

        self.stdout.write(self.style.SUCCESS(
            f'Datos de prueba listos: {Edicion.objects.count()} ediciones, '
            f'{Categoria.objects.count()} categorías, {Votacion.objects.count()} votaciones, '
            f'{Opcion.objects.count()} opciones. Usuarios de prueba: votante1 / votante2 '
            f'(contraseña Festival2027*).'
        ))
