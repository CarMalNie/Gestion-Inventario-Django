from django.core.validators import MinValueValidator
from django.urls import reverse
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User

class Categoria(models.Model):
    """ Representa la categoria a la que pertenece un producto """
    nombre = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name='Nombre de la Categoría'
    )

    def __str__(self):
        return self.nombre

    def get_absolute_url(self):
        # Util para la CBV DetailView que necesita una URL
        return reverse('detalle_categoria', kwargs={"pk": self.pk})
    
class Etiqueta(models.Model):
    """ Representa las etiquetas asociadas a los productos """
    nombre = models.CharField(max_length=100,
        unique=True,
        verbose_name='Nombre de la Etiqueta'
    )

    def __str__(self):
        return self.nombre

    def get_absolute_url(self):
        return reverse("detalle_etiqueta", kwargs={"pk": self.pk})

class Producto(models.Model):
    """ Representa un producto individual """
    nombre = models.CharField(max_length=200, verbose_name='Nombre del Producto', unique=True)
    descripcion = models.TextField(verbose_name='Descripción Detallada')
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio (USD)', validators=[MinValueValidator(0.01)])
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    # Relación Categoria (UNO) a Producto (MUCHOS) (ForeignKey)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        null=False,
        blank=False,
        related_name='productos',
        verbose_name='Categoria'
    )

    # Relación Producto (MUCHOS) a Etiqueta (MUCHOS) (ManyToManyField)
    etiquetas = models.ManyToManyField(
        Etiqueta,
        blank=False,
        related_name='productos_asociados',
        verbose_name='Etiquetas'
    )

    # Un producto puede ser favorito de muchos usuarios, y un usuario puede tener muchos favoritos.
    usuarios_favoritos = models.ManyToManyField(
        User,
        blank=True,
        related_name='productos_favoritos', # Permite acceder con user.productos_favoritos.all()
        verbose_name='Usuarios que lo tienen como favorito'
    )
    
    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        
        # Permisos personalizados
        permissions = [
            ("can_view_raw_reports", "Puede ver reportes SQL RAW (Gestión/Admin)"),
        ]

    def __str__(self):
        return self.nombre
    
    def get_absolute_url(self):
        return reverse("detalle_producto", kwargs={"pk": self.pk})


class DetalleProducto(models.Model):
    """ Contiene detalles únicos para CADA producto (Relación Uno a Uno) """
    dimensiones = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Dimensiones (ej. 10x20x30 cm)'
    )
    peso=models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Peso (kg)',
        validators=[MinValueValidator(Decimal('0.01'),
        message='El peso debe ser mayor a 0.00 kg. Ingrese un valor positivo.')
        ]
    )

    # Relación Producto (UNO) a Detalle (UNO) (OneToOneField)
    producto = models.OneToOneField(
        Producto,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='detalles',
        verbose_name='Detalles de Producto'
    )
    
    def __str__(self):
        return f"Detalle de {self.producto.nombre}"