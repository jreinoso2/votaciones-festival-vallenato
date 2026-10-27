from django.db import models

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

# El modelo Voto se agrega en la siguiente entrega.
