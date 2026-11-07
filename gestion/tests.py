# Pruebas del panel de gestion
# Ejecutar con: python manage.py test gestion -v 2

from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from votaciones.models import Edicion, Categoria, Votacion, Opcion, Voto


class PruebasPanel(TestCase):

    def setUp(self):
        ahora = timezone.now()
        self.edicion = Edicion.objects.create(anio=2027, nombre='Festival 2027',
                                              fecha_inicio=ahora.date(), fecha_fin=ahora.date())
        self.categoria = Categoria.objects.create(edicion=self.edicion, nombre='Acordeón Profesional')
        self.votacion = Votacion.objects.create(categoria=self.categoria, titulo='Final', estado='abierta',
                                                fecha_inicio=ahora - timedelta(days=1),
                                                fecha_cierre=ahora + timedelta(days=5))
        self.opcion = Opcion.objects.create(votacion=self.votacion, nombre='Participante A')

        self.personal = User.objects.create_user('asistente', password='Clave-prueba-123', is_staff=True)
        self.votante = User.objects.create_user('votante', password='Clave-prueba-123')

    def test_votante_normal_no_entra_al_panel(self):
        self.client.login(username='votante', password='Clave-prueba-123')
        respuesta = self.client.get('/gestion/')
        self.assertRedirects(respuesta, '/')

    def test_sin_sesion_pide_login(self):
        respuesta = self.client.get('/gestion/categorias/')
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn('/usuarios/login/', respuesta.url)

    def test_crear_edicion_con_formulario(self):
        self.client.login(username='asistente', password='Clave-prueba-123')
        self.client.post('/gestion/ediciones/nueva/', {
            'anio': 2028, 'nombre': 'Festival 2028',
            'fecha_inicio': '2028-04-26', 'fecha_fin': '2028-04-30',
        })
        self.assertTrue(Edicion.objects.filter(anio=2028).exists())

    def test_edicion_con_fechas_al_reves_se_rechaza(self):
        self.client.login(username='asistente', password='Clave-prueba-123')
        self.client.post('/gestion/ediciones/nueva/', {
            'anio': 2029, 'nombre': 'Mal', 'fecha_inicio': '2029-04-30', 'fecha_fin': '2029-04-01',
        })
        self.assertFalse(Edicion.objects.filter(anio=2029).exists())

    def test_crear_y_modificar_categoria(self):
        self.client.login(username='asistente', password='Clave-prueba-123')
        self.client.post('/gestion/categorias/nueva/', {
            'edicion': self.edicion.id, 'nombre': 'Canción Inédita', 'descripcion': '',
        })
        nueva = Categoria.objects.get(nombre='Canción Inédita')
        self.client.post(f'/gestion/categorias/{nueva.id}/editar/', {
            'edicion': self.edicion.id, 'nombre': 'Canción Inédita 2027', 'descripcion': 'cambiada',
        })
        nueva.refresh_from_db()
        self.assertEqual(nueva.nombre, 'Canción Inédita 2027')

    def test_categoria_repetida_se_rechaza(self):
        self.client.login(username='asistente', password='Clave-prueba-123')
        self.client.post('/gestion/categorias/nueva/', {
            'edicion': self.edicion.id, 'nombre': 'acordeón profesional', 'descripcion': '',
        })
        self.assertEqual(Categoria.objects.filter(edicion=self.edicion).count(), 1)

    def test_votacion_con_cierre_antes_del_inicio_se_rechaza(self):
        self.client.login(username='asistente', password='Clave-prueba-123')
        self.client.post('/gestion/votaciones/nueva/', {
            'categoria': self.categoria.id, 'titulo': 'Mala', 'descripcion': '',
            'fecha_inicio': '2027-04-30T10:00', 'fecha_cierre': '2027-04-01T10:00', 'estado': 'abierta',
        })
        self.assertFalse(Votacion.objects.filter(titulo='Mala').exists())

    def test_cerrar_votacion(self):
        self.client.login(username='asistente', password='Clave-prueba-123')
        self.client.post(f'/gestion/votaciones/{self.votacion.id}/estado/')
        self.votacion.refresh_from_db()
        self.assertEqual(self.votacion.estado, 'cerrada')

    def test_eliminar_opcion_sin_votos(self):
        self.client.login(username='asistente', password='Clave-prueba-123')
        self.client.post(f'/gestion/opciones/{self.opcion.id}/eliminar/')
        self.assertFalse(Opcion.objects.filter(id=self.opcion.id).exists())

    def test_no_se_elimina_opcion_con_votos(self):
        Voto.objects.create(usuario=self.votante, edicion=self.edicion, categoria=self.categoria,
                            votacion=self.votacion, opcion=self.opcion)
        self.client.login(username='asistente', password='Clave-prueba-123')
        self.client.post(f'/gestion/opciones/{self.opcion.id}/eliminar/')
        self.assertTrue(Opcion.objects.filter(id=self.opcion.id).exists())

    def test_consulta_de_votos(self):
        Voto.objects.create(usuario=self.votante, edicion=self.edicion, categoria=self.categoria,
                            votacion=self.votacion, opcion=self.opcion)
        self.client.login(username='asistente', password='Clave-prueba-123')
        respuesta = self.client.get('/gestion/votos/', {'usuario': 'votante'})
        self.assertContains(respuesta, 'Participante A')

    def test_descargar_informe(self):
        Voto.objects.create(usuario=self.votante, edicion=self.edicion, categoria=self.categoria,
                            votacion=self.votacion, opcion=self.opcion)
        self.client.login(username='asistente', password='Clave-prueba-123')
        respuesta = self.client.post('/gestion/informe/', {'edicion': self.edicion.id, 'tipo': 'resultados'})
        self.assertEqual(respuesta['Content-Type'], 'text/csv; charset=utf-8')
        contenido = respuesta.content.decode('utf-8-sig')
        self.assertIn('Participante A;1', contenido)

    def test_dar_permiso_de_personal(self):
        self.client.login(username='asistente', password='Clave-prueba-123')
        self.client.post(f'/gestion/usuarios/{self.votante.id}/personal/')
        self.votante.refresh_from_db()
        self.assertTrue(self.votante.is_staff)
