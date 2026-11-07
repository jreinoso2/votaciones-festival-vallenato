from django.conf import settings
from django.db import models
from django.utils import timezone

# Estructura de datos del sistema:
# EDICIÓN  ->  CATEGORÍA  ->  VOTACIÓN  ->  OPCIÓN
# Cada modelo tiene una llave foránea (ForeignKey) hacia el anterior.


class Edicion(models.Model):
    """Edición anual del Festival (por ejemplo la de 2027)."""
    anio = models.PositiveIntegerField('año', unique=True)
    nombre = models.CharField(max_length=150)
    fecha_inicio = models.DateField('fecha de inicio')
    fecha_fin = models.DateField('fecha de finalización')

    class Meta:
        verbose_name = 'edición'
        verbose_name_plural = 'ediciones'
        ordering = ['-anio']

    def __str__(self):
        return f'{self.nombre} ({self.anio})'


class Categoria(models.Model):
    """Categoría que pertenece a una edición."""
    edicion = models.ForeignKey(Edicion, on_delete=models.CASCADE, related_name='categorias')
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField('descripción', blank=True)

    class Meta:
        verbose_name = 'categoría'
        verbose_name_plural = 'categorías'

    def __str__(self):
        return f'{self.nombre} - {self.edicion.anio}'


class Votacion(models.Model):
    """Votación asociada a una categoría."""
    ESTADOS = [
        ('abierta', 'Abierta'),
        ('cerrada', 'Cerrada'),
    ]

    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='votaciones')
    titulo = models.CharField('título', max_length=200)
    descripcion = models.TextField('descripción', blank=True)
    fecha_inicio = models.DateTimeField('fecha de inicio')
    fecha_cierre = models.DateTimeField('fecha de cierre')
    estado = models.CharField(max_length=10, choices=ESTADOS, default='cerrada')

    class Meta:
        verbose_name = 'votación'
        verbose_name_plural = 'votaciones'

    def __str__(self):
        return self.titulo

    def esta_habilitada(self):
        """La votación acepta votos si está marcada como abierta
        y la fecha actual está entre la fecha de inicio y la de cierre."""
        ahora = timezone.now()
        return self.estado == 'abierta' and self.fecha_inicio <= ahora <= self.fecha_cierre


class Opcion(models.Model):
    """Opción participante de una votación."""
    votacion = models.ForeignKey(Votacion, on_delete=models.CASCADE, related_name='opciones')
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField('descripción', blank=True)

    class Meta:
        verbose_name = 'opción'
        verbose_name_plural = 'opciones'

    def __str__(self):
        return self.nombre

class Voto(models.Model):
    """Voto emitido por un usuario.

    Regla de negocio: un usuario solo puede votar UNA vez por categoría
    y edición, aunque la categoría tenga varias votaciones (subeventos).
    La regla se garantiza en la base de datos con la restricción
    'voto_unico_usuario_categoria_edicion' (índice UNIQUE en MySQL),
    y además se valida en la vista antes de guardar.
    """
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='votos')
    edicion = models.ForeignKey(Edicion, on_delete=models.PROTECT, related_name='votos', verbose_name='edición')
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='votos', verbose_name='categoría')
    votacion = models.ForeignKey(Votacion, on_delete=models.PROTECT, related_name='votos', verbose_name='votación')
    opcion = models.ForeignKey(Opcion, on_delete=models.PROTECT, related_name='votos', verbose_name='opción')
    fecha = models.DateTimeField('fecha del voto', auto_now_add=True)

    class Meta:
        verbose_name = 'voto'
        verbose_name_plural = 'votos'
        ordering = ['-fecha']
        constraints = [
            models.UniqueConstraint(
                fields=['usuario', 'categoria', 'edicion'],
                name='voto_unico_usuario_categoria_edicion',
            ),
        ]

    def __str__(self):
        return f'{self.usuario} - {self.categoria.nombre} - {self.opcion}'
