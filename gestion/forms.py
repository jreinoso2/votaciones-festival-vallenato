from django import forms

from votaciones.models import Edicion, Categoria, Votacion, Opcion


# Los campos de fecha usan los controles de fecha del navegador
class CampoFecha(forms.DateInput):
    input_type = 'date'


class CampoFechaHora(forms.DateTimeInput):
    input_type = 'datetime-local'


class EdicionForm(forms.ModelForm):
    class Meta:
        model = Edicion
        fields = ['anio', 'nombre', 'fecha_inicio', 'fecha_fin']
        widgets = {
            'fecha_inicio': CampoFecha(format='%Y-%m-%d'),
            'fecha_fin': CampoFecha(format='%Y-%m-%d'),
        }

    def clean(self):
        datos = super().clean()
        inicio = datos.get('fecha_inicio')
        fin = datos.get('fecha_fin')
        if inicio and fin and fin < inicio:
            self.add_error('fecha_fin', 'La fecha de finalización no puede ser antes de la fecha de inicio.')
        return datos


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['edicion', 'nombre', 'descripcion']
        widgets = {'descripcion': forms.Textarea(attrs={'rows': 3})}

    def clean(self):
        datos = super().clean()
        edicion = datos.get('edicion')
        nombre = datos.get('nombre')
        # no dejamos dos categorías con el mismo nombre en la misma edición
        if edicion and nombre:
            repetida = Categoria.objects.filter(edicion=edicion, nombre__iexact=nombre)
            if self.instance.pk:
                repetida = repetida.exclude(pk=self.instance.pk)
            if repetida.exists():
                self.add_error('nombre', 'Ya existe una categoría con ese nombre en esta edición.')
        return datos


class VotacionForm(forms.ModelForm):
    class Meta:
        model = Votacion
        fields = ['categoria', 'titulo', 'descripcion', 'fecha_inicio', 'fecha_cierre', 'estado']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'fecha_inicio': CampoFechaHora(format='%Y-%m-%dT%H:%M'),
            'fecha_cierre': CampoFechaHora(format='%Y-%m-%dT%H:%M'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].queryset = Categoria.objects.select_related('edicion').order_by('-edicion__anio', 'nombre')

    def clean(self):
        datos = super().clean()
        inicio = datos.get('fecha_inicio')
        cierre = datos.get('fecha_cierre')
        if inicio and cierre and cierre <= inicio:
            self.add_error('fecha_cierre', 'La fecha de cierre debe ser posterior a la fecha de inicio.')
        return datos


class OpcionForm(forms.ModelForm):
    class Meta:
        model = Opcion
        fields = ['votacion', 'nombre', 'descripcion']
        widgets = {'descripcion': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['votacion'].queryset = Votacion.objects.select_related('categoria__edicion').order_by('-categoria__edicion__anio', 'titulo')
        # para que en la lista se vea a qué categoría y edición pertenece cada votación
        self.fields['votacion'].label_from_instance = (
            lambda v: f'{v.titulo} ({v.categoria.nombre} - {v.categoria.edicion.anio})'
        )


class FiltroVotosForm(forms.Form):
    """Formulario para filtrar la consulta de votos."""
    edicion = forms.ModelChoiceField(queryset=Edicion.objects.all(), required=False, empty_label='Todas')
    categoria = forms.ModelChoiceField(queryset=Categoria.objects.select_related('edicion'), required=False, empty_label='Todas')
    usuario = forms.CharField(required=False, max_length=150, label='Nombre de usuario')


class InformeForm(forms.Form):
    """Formulario para descargar el informe de votaciones."""
    TIPOS = [
        ('resultados', 'Resultados (total de votos por opción)'),
        ('votos', 'Detalle de todos los votos'),
    ]
    edicion = forms.ModelChoiceField(queryset=Edicion.objects.all(), empty_label=None, label='Edición')
    tipo = forms.ChoiceField(choices=TIPOS, label='Tipo de informe')

