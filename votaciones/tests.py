"""Pruebas funcionales CP-01 a CP-10 de la Entrega 3.

Ejecutar con:
    python manage.py test votaciones -v 2

Django crea una base de datos MySQL temporal (test_votaciones_festival),
corre las pruebas y la borra al final. No toca los datos reales.
"""

import json
import threading
from datetime import timedelta
from unittest import mock

from django.contrib.auth.models import User
from django.db import connection
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from .models import Edicion, Categoria, Votacion, Opcion, Voto


def crear_datos():
    """Escenario de prueba: una edición con dos categorías abiertas
    (una con dos subeventos) y una categoría cerrada."""
    ahora = timezone.now()
    edicion = Edicion.objects.create(anio=2027, nombre='Festival de prueba',
                                     fecha_inicio=ahora.date(), fecha_fin=ahora.date())
    d = {'edicion': edicion}

    d['cat_acordeon'] = Categoria.objects.create(edicion=edicion, nombre='Acordeón Profesional')
    d['vot_eliminatoria'] = Votacion.objects.create(
        categoria=d['cat_acordeon'], titulo='Eliminatoria', estado='abierta',
        fecha_inicio=ahora - timedelta(days=1), fecha_cierre=ahora + timedelta(days=10))
    d['vot_final'] = Votacion.objects.create(
        categoria=d['cat_acordeon'], titulo='Final', estado='abierta',
        fecha_inicio=ahora - timedelta(days=1), fecha_cierre=ahora + timedelta(days=10))
    d['op_a'] = Opcion.objects.create(votacion=d['vot_eliminatoria'], nombre='Participante A')
    d['op_b'] = Opcion.objects.create(votacion=d['vot_eliminatoria'], nombre='Participante B')
    d['op_final'] = Opcion.objects.create(votacion=d['vot_final'], nombre='Finalista A')

    d['cat_cancion'] = Categoria.objects.create(edicion=edicion, nombre='Canción Inédita')
    d['vot_cancion'] = Votacion.objects.create(
        categoria=d['cat_cancion'], titulo='Canción favorita', estado='abierta',
        fecha_inicio=ahora - timedelta(days=1), fecha_cierre=ahora + timedelta(days=10))
    d['op_cancion'] = Opcion.objects.create(votacion=d['vot_cancion'], nombre='Canción A')

    d['cat_piqueria'] = Categoria.objects.create(edicion=edicion, nombre='Piqueria')
    d['vot_cerrada'] = Votacion.objects.create(
        categoria=d['cat_piqueria'], titulo='Piquería', estado='cerrada',
        fecha_inicio=ahora - timedelta(days=1), fecha_cierre=ahora + timedelta(days=10))
    d['op_cerrada'] = Opcion.objects.create(votacion=d['vot_cerrada'], nombre='Piquero A')

    # abierta en el estado, pero su fecha de cierre ya pasó
    d['vot_vencida'] = Votacion.objects.create(
        categoria=d['cat_piqueria'], titulo='Piquería vencida', estado='abierta',
        fecha_inicio=ahora - timedelta(days=10), fecha_cierre=ahora - timedelta(days=1))
    d['op_vencida'] = Opcion.objects.create(votacion=d['vot_vencida'], nombre='Piquero B')

    d['usuario'] = User.objects.create_user('votante', password='Clave-prueba-123')
    d['admin'] = User.objects.create_superuser('admin_prueba', password='Clave-prueba-123')
    return d


class PruebasVotaciones(TestCase):

    def setUp(self):
        self.d = crear_datos()
        self.client.login(username='votante', password='Clave-prueba-123')

    def votar(self, votacion, opcion):
        url = reverse('registrar_voto', args=[votacion.id])
        return self.client.post(url, {'opcion': opcion.id}, follow=True)

    def test_cp01_voto_valido_se_registra(self):
        """CP-01: usuario autenticado elige una opción válida y se guarda en MySQL."""
        # paso de confirmación
        r = self.client.post(reverse('confirmar_voto', args=[self.d['vot_eliminatoria'].id]),
                             {'opcion': self.d['op_a'].id})
        self.assertContains(r, 'Confirmar voto')
        self.assertEqual(Voto.objects.count(), 0)  # todavía no se guarda
        # paso de registro
        r = self.votar(self.d['vot_eliminatoria'], self.d['op_a'])
        self.assertContains(r, 'Voto registrado')
        voto = Voto.objects.get()
        self.assertEqual(voto.usuario, self.d['usuario'])
        self.assertEqual(voto.opcion, self.d['op_a'])
        self.assertEqual(voto.categoria, self.d['cat_acordeon'])
        self.assertEqual(voto.edicion, self.d['edicion'])

    def test_cp02_segundo_voto_misma_categoria_rechazado(self):
        """CP-02: segundo voto en la misma categoría, con otra opción o en otro subevento."""
        self.votar(self.d['vot_eliminatoria'], self.d['op_a'])
        r1 = self.votar(self.d['vot_eliminatoria'], self.d['op_b'])   # otra opción
        r2 = self.votar(self.d['vot_final'], self.d['op_final'])      # otro subevento
        self.assertContains(r1, 'Usted ya votó')
        self.assertContains(r2, 'Usted ya votó')
        self.assertEqual(Voto.objects.filter(usuario=self.d['usuario'], categoria=self.d['cat_acordeon']).count(), 1)
        self.assertEqual(Voto.objects.get().opcion, self.d['op_a'])

    def test_cp03_voto_en_otra_categoria_permitido(self):
        """CP-03: después de votar en una categoría puede votar en otra diferente."""
        self.votar(self.d['vot_eliminatoria'], self.d['op_a'])
        r = self.votar(self.d['vot_cancion'], self.d['op_cancion'])
        self.assertContains(r, 'Voto registrado')
        self.assertEqual(Voto.objects.filter(usuario=self.d['usuario']).count(), 2)

    def test_cp04_usuario_no_autenticado_debe_iniciar_sesion(self):
        """CP-04: sin sesión se redirige al login y no se guarda nada."""
        anonimo = Client()
        for nombre in ['confirmar_voto', 'registrar_voto']:
            r = anonimo.post(reverse(nombre, args=[self.d['vot_eliminatoria'].id]), {'opcion': self.d['op_a'].id})
            self.assertEqual(r.status_code, 302)
            self.assertIn(reverse('login'), r['Location'])
        r = anonimo.get(reverse('mis_votos'))
        self.assertIn(reverse('login'), r['Location'])
        self.assertEqual(Voto.objects.count(), 0)

    def test_cp05_categoria_no_habilitada_rechazada(self):
        """CP-05: votación cerrada o fuera de fechas no acepta votos."""
        r1 = self.votar(self.d['vot_cerrada'], self.d['op_cerrada'])
        r2 = self.votar(self.d['vot_vencida'], self.d['op_vencida'])
        self.assertContains(r1, 'no está habilitada')
        self.assertContains(r2, 'no está habilitada')
        self.assertEqual(Voto.objects.count(), 0)

    def test_cp06_opcion_de_otra_categoria_rechazada(self):
        """CP-06: se envía a la votación de Acordeón una opción de Canción Inédita."""
        r = self.votar(self.d['vot_eliminatoria'], self.d['op_cancion'])
        self.assertContains(r, 'no pertenece a esta votación')
        # también una opción que no existe
        r = self.client.post(reverse('registrar_voto', args=[self.d['vot_eliminatoria'].id]),
                             {'opcion': 999999}, follow=True)
        self.assertContains(r, 'no existe')
        self.assertEqual(Voto.objects.count(), 0)

    def test_cp07_usuario_consulta_sus_votos(self):
        """CP-07: la página Mis votos muestra exactamente sus categorías votadas."""
        self.votar(self.d['vot_eliminatoria'], self.d['op_a'])
        self.votar(self.d['vot_cancion'], self.d['op_cancion'])
        # voto de otro usuario que NO debe aparecer
        otro = User.objects.create_user('otro', password='Clave-prueba-123')
        Voto.objects.create(usuario=otro, edicion=self.d['edicion'], categoria=self.d['cat_acordeon'],
                            votacion=self.d['vot_eliminatoria'], opcion=self.d['op_b'])
        r = self.client.get(reverse('mis_votos'))
        self.assertEqual(list(r.context['votos'].values_list('opcion__nombre', flat=True).order_by('id')),
                         ['Participante A', 'Canción A'])
        self.assertNotContains(r, 'Participante B')

    def test_cp08_administrador_consulta_votos(self):
        """CP-08: el admin lista los votos y coinciden con la base de datos."""
        self.votar(self.d['vot_eliminatoria'], self.d['op_a'])
        self.votar(self.d['vot_cancion'], self.d['op_cancion'])
        admin = Client()
        admin.login(username='admin_prueba', password='Clave-prueba-123')
        r = admin.get(reverse('admin:votaciones_voto_changelist'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['cl'].result_count, Voto.objects.count())
        self.assertContains(r, 'Participante A')
        self.assertContains(r, 'Canción A')
        # un usuario normal no puede entrar a la administración
        r = self.client.get(reverse('admin:votaciones_voto_changelist'))
        self.assertEqual(r.status_code, 302)

    def test_cp10_api_categorias_json(self):
        """CP-10: GET /api/categorias/ devuelve JSON con categorías y opciones reales."""
        r = Client().get('/api/categorias/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'application/json')
        datos = json.loads(r.content)
        self.assertEqual(datos['total'], Categoria.objects.count())
        acordeon = next(c for c in datos['categorias'] if c['nombre'] == 'Acordeón Profesional')
        self.assertEqual(acordeon['edicion']['anio'], 2027)
        opciones = [o['nombre'] for v in acordeon['votaciones'] for o in v['opciones']]
        self.assertEqual(sorted(opciones), ['Finalista A', 'Participante A', 'Participante B'])
        # filtro por edición y método no permitido
        self.assertEqual(json.loads(Client().get('/api/categorias/?edicion=1990').content)['total'], 0)
        self.assertEqual(Client().post('/api/categorias/').status_code, 405)

    def test_csrf_obligatorio(self):
        """Seguridad: un POST sin token CSRF es rechazado (403)."""
        cliente = Client(enforce_csrf_checks=True)
        cliente.login(username='votante', password='Clave-prueba-123')
        r = cliente.post(reverse('registrar_voto', args=[self.d['vot_eliminatoria'].id]), {'opcion': self.d['op_a'].id})
        self.assertEqual(r.status_code, 403)
        self.assertEqual(Voto.objects.count(), 0)

    def test_votar_por_get_no_permitido(self):
        """Seguridad: el voto solo se acepta por POST."""
        r = self.client.get(reverse('registrar_voto', args=[self.d['vot_eliminatoria'].id]))
        self.assertEqual(r.status_code, 405)


class PruebasConcurrencia(TransactionTestCase):
    """CP-09: solicitudes simultáneas. Se usa TransactionTestCase para que cada
    hilo trabaje con su propia conexión a MySQL y transacciones reales."""

    def setUp(self):
        self.d = crear_datos()

    def test_cp09_solicitudes_simultaneas_un_solo_voto(self):
        """Cinco solicitudes al mismo tiempo para la misma categoría: solo queda un voto."""
        hilos_listos = threading.Barrier(5)
        codigos = []
        opciones = [self.d['op_a'], self.d['op_b'], self.d['op_a'], self.d['op_final'], self.d['op_b']]
        votaciones = [self.d['vot_eliminatoria']] * 3 + [self.d['vot_final'], self.d['vot_eliminatoria']]

        def enviar(votacion, opcion):
            try:
                cliente = Client()
                cliente.login(username='votante', password='Clave-prueba-123')
                hilos_listos.wait()  # todos los hilos salen al mismo tiempo
                r = cliente.post(reverse('registrar_voto', args=[votacion.id]), {'opcion': opcion.id})
                codigos.append(r.status_code)
            finally:
                connection.close()

        hilos = [threading.Thread(target=enviar, args=(v, o)) for v, o in zip(votaciones, opciones)]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join()

        self.assertEqual(len(codigos), 5)  # ninguna solicitud produjo error 500
        self.assertEqual(Voto.objects.filter(usuario=self.d['usuario'], categoria=self.d['cat_acordeon']).count(), 1)

    def test_cp09_restriccion_unique_de_mysql(self):
        """Peor caso: las dos solicitudes pasan la validación de Django al mismo tiempo.
        Se simula desactivando la consulta previa; aun así MySQL rechaza el duplicado
        con el índice UNIQUE y la vista responde con un mensaje, no con un error."""
        cliente = Client()
        cliente.login(username='votante', password='Clave-prueba-123')
        with mock.patch('votaciones.servicios.ya_voto_en_categoria', return_value=False):
            r1 = cliente.post(reverse('registrar_voto', args=[self.d['vot_eliminatoria'].id]),
                              {'opcion': self.d['op_a'].id}, follow=True)
            r2 = cliente.post(reverse('registrar_voto', args=[self.d['vot_final'].id]),
                              {'opcion': self.d['op_final'].id}, follow=True)
        self.assertContains(r1, 'Voto registrado')
        self.assertContains(r2, 'El voto duplicado fue rechazado')
        self.assertEqual(Voto.objects.count(), 1)
