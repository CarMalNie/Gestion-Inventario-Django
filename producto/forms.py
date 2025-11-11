from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from django.db import transaction
from django.forms import inlineformset_factory 
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper 
from crispy_forms.layout import Layout, Submit, Field
from .models import Producto, Categoria, Etiqueta, DetalleProducto


# Se define el nombre del grupo por defecto para los usuarios que se registran
DEFAULT_GROUP_NAME = 'Clientes' 


# ====================================================================== #
# DEFINICIÓN DEL FORMSET (Para la relación Uno a Uno de DetalleProducto) #
# ====================================================================== #
DetalleProductoFormset = inlineformset_factory(
    Producto, DetalleProducto, fields=['dimensiones', 'peso'], 
    extra=1, max_num=1, can_delete=False
)


# ================================== # 
# Formularios del CRUD (ModelForm)   #
# ================================== #

## Formulario Modelo "Producto" (FBV) ##
class ProductoForm(forms.ModelForm):

    class Meta:
        model = Producto
        fields = [
            'nombre', 'descripcion', 'precio', 'categoria', 'etiquetas',
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'row': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.html5_required = True
        self.helper.layout = Layout(
            Field('nombre', css_class='form-control'),
            Field('descripcion', css_class='form-control'),
            Field('precio', css_class='form-control'),
            Field('categoria', css_class='form-control'),
            Field('etiquetas', css_class='form-control'), 
            Submit('submit', 'Guardar Producto', css_class='btn btn-success mt-3')
        )

## Formulario Modelo Detalle Producto (Formset) ##
class DetalleProductoForm(forms.ModelForm):
    class Meta:
        model = DetalleProducto
        fields = ['dimensiones', 'peso']
        widgets = {
            'peso': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'})
        }

## Formulario Modelo "Categoria" (CBV) ##
class CategoriaForm(forms.ModelForm):

    class Meta:
        model = Categoria
        fields = ['nombre']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.html5_required = True
        self.helper.add_input (
            Submit('submit', 'Guardar Categoria', css_class='btn btn-primary')
        )

## Formulario Modelo "Etiqueta" (CBV) ##
class EtiquetaForm(forms.ModelForm):

    class Meta:
        model = Etiqueta
        fields = ['nombre']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.html5_required = True
        self.helper.add_input(
            Submit('submit', 'Guardar Etiqueta', css_class='btn btn-info')
        )


# ========================== # 
#  Consultas con ORM Django  #
# ========================== #

## Formulario Genérico para Búsqueda y Filtro (FBV) ##
class ProductoFilterForm(forms.Form):
    """ Filtro con Layout Vertical para Lista Productos """
    
    # Aplicamos las clases de Bootstrap aquí, en el widget.
    nombre = forms.CharField(
        label='Nombre', max_length=100, required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Buscar por nombre'}) # Clase aplicada
    )

    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all().order_by('nombre'),
        label='Filtrar por Categoría', required=False,
        empty_label="--- Todas las Categorías ---",
        widget=forms.Select(attrs={'class': 'form-select'}) # Clase aplicada
    )

    precio_min = forms.CharField(
        label='Precio Mayor que', required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Mínimo'}) # Clase aplicada
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.html5_required = True
        self.helper.form_method = 'get' 
        
        self.helper.add_input( 
            Submit('submit', 'Buscar / Filtrar', css_class='btn btn-secondary mt-3')
        )


# ================================== # 
#  Formulario Registro Usuario (CBV) #
# ================================== #

class CustomUserCreationForm(UserCreationForm):

    email = forms.EmailField(required=True, label='Correo Electrónico')
    first_name = forms.CharField(max_length=30, required=True, label='Nombre')
    last_name = forms.CharField(max_length=150, required=True, label='Apellido')
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name',) 
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Este correo electrónico ya está registrado.")
        return email

    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.save()

        try:
            cliente_group = Group.objects.get(name=DEFAULT_GROUP_NAME)
            user.groups.add(cliente_group)
        except Group.DoesNotExist:
            pass 
            
        return user