from django.contrib import admin
from django.contrib.auth.admin import UserAdmin 
from django.contrib.auth.models import User, Group 
from .models import Producto, Categoria, Etiqueta, DetalleProducto

# --- 1. INLINES (Componentes Anidados) ---

class DetalleProductoInline(admin.StackedInline):
    """Permite editar DetalleProducto directamente en la página de Producto (Relación 1:1)."""
    model = DetalleProducto
    fields = ('dimensiones', 'peso')

class ProductoEtiquetaInline(admin.TabularInline):
    """Permite añadir/quitar Etiquetas directamente en la página de Producto (Relación M:M)."""
    model = Producto.etiquetas.through 
    extra = 1 

# --- 2. CONFIGURACIÓN DEL MODELO PRODUCTO ---

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    # Listado en la tabla principal
    list_display = ('nombre', 'precio', 'mostrar_etiquetas', 'categoria', 'fecha_creacion', 'es_costoso')
    # Filtros laterales y búsqueda
    list_filter = ('categoria', 'etiquetas', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion')
    ordering = ('-fecha_creacion',)
    
    # Inlines para editar relaciones
    inlines = [DetalleProductoInline, ProductoEtiquetaInline]
    
    # MÉTODO PARA MOSTRAR LAS ETIQUETAS (para la columna list_display)
    def mostrar_etiquetas(self, obj):
        """Muestra todas las etiquetas de un producto separadas por comas."""
        return ", ".join([e.nombre for e in obj.etiquetas.all()])
    mostrar_etiquetas.short_description = 'Etiquetas'

    # Columna personalizada para el listado
    def es_costoso(self, obj):
        return obj.precio > 500.00 
    es_costoso.boolean = True 


# --- 3. CONFIGURACIÓN DE LOS MODELOS SECUNDARIOS ---

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'id')
    search_fields = ('nombre',)

@admin.register(Etiqueta)
class EtiquetaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'id')
    search_fields = ('nombre',)
    
    
# --- 4. CONFIGURACIÓN DE USUARIOS Y GRUPOS (SEGURIDAD Y PERMISOS) ---

class CustomUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ('get_groups',) 
    
    # Redefinición de fieldsets para evitar duplicidad y mantener el control
    fieldsets = (
        (None, {'fields': ('username', 'password')}), 
        ('Información Personal', {'fields': ('first_name', 'last_name', 'email')}),
        ('Estatus', {'fields': ('is_active', 'is_staff', 'is_superuser')}), 
        ('Roles de Grupo y Permisos', {
            'fields': ('groups', 'user_permissions',), 
            'classes': ('collapse',),
        }), 
    )
    
    # filter_horizontal activa las flechas para Grupos y Permisos
    filter_horizontal = ('groups', 'user_permissions')

    def get_groups(self, obj):
        return ", ".join([g.name for g in obj.groups.all()])
    get_groups.short_description = 'Grupos Asignados'

# Clase para forzar las flechas en la asignación de permisos de GRUPO
class CustomGroupAdmin(admin.ModelAdmin):
    filter_horizontal = ('permissions',) 
    fieldsets = (
        (None, {'fields': ('name',)}),
        ('Permisos', {'fields': ('permissions',)})
    )


# 5. REGISTRO FINAL DE SEGURIDAD
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

admin.site.unregister(Group)
admin.site.register(Group, CustomGroupAdmin)