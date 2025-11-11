from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Prefetch, Count
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required 
from django.contrib.auth.views import LoginView as BaseLoginView 
from django.contrib.auth import logout as auth_logout
from django.http import Http404, HttpResponseRedirect
from decimal import Decimal, InvalidOperation
from .models import Producto, Categoria, Etiqueta, DetalleProducto
from .forms import ( 
    ProductoForm, CategoriaForm, EtiquetaForm, DetalleProductoFormset,
    ProductoFilterForm, CustomUserCreationForm
)
from django.views.generic import ( 
    ListView,
    DetailView,
    UpdateView,
    DeleteView,
    CreateView,
    TemplateView,
)


# ============================================================== #
#            FUNCIONES DE PRUEBA DE PERMISOS (PARA FBVs)         #
# ============================================================== #

# Permite Crear/Modificar/Reportar (CRU) a Administradores y Gestión
def is_admin_or_gestion_cr_update(user):
    """Permite el acceso a vistas de Creación, Reportes y Modificación."""
    allowed_groups = ['Administradores', 'Gestión']
    return user.groups.filter(name__in=allowed_groups).exists() or user.is_superuser

# Permite ELIMINAR (D) solo a Administradores
def is_admin_only_delete(user):
    """Permite el acceso a vistas de Eliminación."""
    return user.groups.filter(name='Administradores').exists() or user.is_superuser


# ========================================= # 
# MANIPULACIÓN ERROR 404, 403 Y HOME (FBV)  #
# ========================================= #

## Manipulador de Errores 404 Personalizado ##
def error_404_handler(request, exception):
    """ Muestra la página de error 404 al no existe una página """
    return render(request, 'error_404.html', {}, status=404)

## Manipulador de Errores 403 Personzalizado ##
def error_403_handler(request, exception):
    """ Muestra la página de error 403 (Acceso Denegado). """
    return render(request, 'error_403.html', {}, status=403)


## Página Inicial Home ##
def home(request):
    """ Muestra la página de bienvenida """
    context = {
        'titulo': 'Bienvenido al Gestor de Productos.'
    }
    return render(request, 'producto/home.html', context)


# ==================== # 
# CRUD Producto (FBV)  #
# ==================== #

## READ (Lista de Productos) ##
def lista_productos(request):
    """ Muestra la lista de todos los productos """
    
    productos = Producto.objects.select_related('categoria','detalles').prefetch_related('etiquetas').order_by('-fecha_creacion')
    
    filter_form = ProductoFilterForm(request.GET) 
    
    if filter_form.is_valid():
        
        cleaned_data = filter_form.cleaned_data
        
        nombre = cleaned_data.get('nombre')
        categoria = cleaned_data.get('categoria') 
        precio_min_str = cleaned_data.get('precio_min') 
        
        if nombre:
            productos = productos.filter(nombre__icontains=nombre.strip())

        if categoria: 
            productos = productos.filter(categoria=categoria)

        if precio_min_str and precio_min_str.strip():
            try:
                precio_min_decimal = Decimal(precio_min_str.strip())
                if precio_min_decimal <= 0:
                    messages.error(request, "El precio mínimo debe ser un valor mayor a cero.", extra_tags='danger')
                    pass 
                else:
                    productos = productos.filter(precio__gt=precio_min_decimal)
            except InvalidOperation:
                messages.error(request, "El precio mínimo ingresado no es un número válido.", extra_tags='danger')
                pass
            
    productos = productos.order_by('-fecha_creacion')

    context = {
        'productos': productos,
        'titulo': 'Catálogo de Productos',
        'filter_form': filter_form,
    }
    return render(request, 'producto/productos/producto_lista.html' , context)

## READ (Detalle de Producto) ##
def detalle_producto(request, pk):
    """ Muestra el detalle de un producto específico, incluyendo si es favorito """
    producto = get_object_or_404(
        Producto.objects.select_related('categoria','detalles').prefetch_related('etiquetas', 'usuarios_favoritos'),
        pk=pk
    )
    
    es_favorito = False
    if request.user.is_authenticated:
        es_favorito = producto.usuarios_favoritos.filter(pk=request.user.pk).exists()
    
    context = {
        'producto': producto,
        'titulo': f"Detalle: {producto.nombre}",
        'es_favorito': es_favorito, 
    }
    return render(request, 'producto/productos/producto_detalle.html', context)

## ACCIÓN: TOGGLE FAVORITO ##
@login_required 
def toggle_favorito(request, pk):
    """ Añade o elimina un Producto de la lista de favoritos del usuario actual. """
    producto = get_object_or_404(Producto, pk=pk)
    user = request.user
    
    if request.method == 'POST': 
        
        if producto in user.productos_favoritos.all():
            user.productos_favoritos.remove(producto)
            if 'next' in request.POST and request.POST['next'] == 'perfil_personal':
                messages.warning(request, f'"{producto.nombre}" ha sido quitado de tu lista de favoritos.')
                return redirect('perfil_personal')
            
            messages.warning(request, f'"{producto.nombre}" ha sido quitado de favoritos.')
        else:
            user.productos_favoritos.add(producto)
            messages.success(request, f'"{producto.nombre}" ha sido añadido a favoritos.')
        
        return redirect('detalle_producto', pk=pk)
    
    raise Http404("Método no permitido. Solo POST.")


## CREATE (Crear Nuevo Producto) ##
@login_required 
@permission_required('producto.add_producto', raise_exception=True)
@transaction.atomic
def crear_producto(request):
    """ Maneja la creación de un nuevo producto usando ProductoForm """
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        formset = DetalleProductoFormset(request.POST)

        if form.is_valid() and formset.is_valid():
            producto_nuevo = form.save()
            formset.instance = producto_nuevo
            formset.save()

            messages.success(request, f'Producto "{producto_nuevo.nombre}" ha sido creado.')
            return redirect('lista_productos')

        messages.error(request, 'Error al crear el producto. Revise los datos.', extra_tags='danger') # Aseguramos el color rojo

    else:
        form = ProductoForm()
        formset = DetalleProductoFormset(instance=Producto())

    context = {
        'form': form,
        'formset':formset,
        'titulo': 'Crear Nuevo Producto'
    }
    return render(request, 'producto/formulario.html', context)

## UPDATE (Editar Producto) ##
@login_required 
@permission_required('producto.change_producto', raise_exception=True) 
@transaction.atomic
def editar_producto(request, pk):
    """ Maneja la edición de un producto usando ProductoForm """
    producto = get_object_or_404(
        Producto.objects.select_related('categoria', 'detalles').prefetch_related('etiquetas'), 
        pk=pk
    )

    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        formset = DetalleProductoFormset(request.POST, instance=producto)

        if form.is_valid() and formset.is_valid():
            form.save() 
            formset.save() 

            messages.success(request, f'Producto "{producto.nombre}" ha sido actualizado.')
            return redirect('detalle_producto', pk=producto.pk)

        messages.error(request, "Error al actualizar el producto. Revise los datos.", extra_tags='danger')

    else:
        form = ProductoForm(instance=producto)
        formset = DetalleProductoFormset(instance=producto)
    
    context = {
        'form': form,
        'formset':formset,
        'titulo': f'Editar Producto: "{producto.nombre}"'
    }
    return render(request, 'producto/formulario.html', context)

## DELETE (Eliminar Producto) ##
@login_required 
@permission_required('producto.delete_producto', raise_exception=True) 
def eliminar_producto(request, pk):
    """ Maneja la eliminación de un nuevo producto usando ProductoForm """
    producto = get_object_or_404(
        Producto.objects.select_related('categoria', 'detalles').prefetch_related('etiquetas'), 
        pk=pk
    )

    if request.method == 'POST':
        nombre_producto = producto.nombre
        producto.delete()
        messages.warning(request, f'Producto "{nombre_producto}" ha sido eliminado permanentemente.')
        return redirect('lista_productos')

    context = {
        'producto': producto,
        'titulo': f'Eliminar: "{producto.nombre}"' 
    }
    return render(request, 'producto/productos/producto_eliminar.html', context)

## REPORTE SQL RAW: Productos y Etiquetas Asociadas - Usa permiso personalizado ##
@login_required 
@permission_required('producto.can_view_raw_reports', raise_exception=True) 
def reporte_productos_etiquetas(request):
    """ Ejecuta una consulta SQL RAW para unir Productos y Etiquetas """
    titulo = "Auditoria de Clasificación por Etiquetas"
    
    sql_query = """
SELECT 
    Prod.id AS id, 
    Prod.nombre AS producto_nombre,
    Prod.precio As producto_precio, 
    Cat.nombre AS categoria_nombre, 
    Prod.fecha_actualizacion AS fecha_actualizacion,
    GROUP_CONCAT(Etiq.nombre ORDER BY Etiq.nombre SEPARATOR ', ') AS etiqueta_nombres 
FROM 
    producto_producto Prod  
INNER JOIN 
    producto_producto_etiquetas Prod_Etiq ON Prod.id = Prod_Etiq.producto_id
INNER JOIN 
    producto_etiqueta Etiq ON Prod_Etiq.etiqueta_id = Etiq.id
INNER JOIN 
    producto_categoria Cat ON Prod.categoria_id = Cat.id
GROUP BY 
    Prod.id, Prod.nombre, Prod.precio, Cat.nombre, Prod.fecha_actualizacion
ORDER BY 
    Cat.nombre, Prod.nombre;
"""
    productos_raw = Producto.objects.raw(sql_query)

    context = {
        'reporte': productos_raw,
        'titulo': titulo,
    }
    return render(request, 'producto/reporte_raw.html', context)


# ====================== # 
# CRUD CATEGORIA (CBV)   #
# ====================== #

## READ (Lista de Categorias) ##
class CategoriaListView(ListView):
    model = Categoria
    template_name = 'producto/categorias/categoria_lista.html'
    context_object_name = 'lista_categorias'
    ordering = ['nombre']
    
    def get_queryset(self):
        queryset = Categoria.objects.annotate(total_productos=Count('productos'))
        return queryset.order_by('-total_productos', 'nombre')

## READ (Detalle de Categoria) ##
class CategoriaDetailView(DetailView):
    model = Categoria
    template_name = 'producto/listado_relacionado.html' 
    context_object_name = 'entidad'

    def get_queryset(self):
        return Categoria.objects.prefetch_related('productos__categoria', 'productos__detalles')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["productos_relacionados"] = self.object.productos.all().select_related('categoria', 'detalles').prefetch_related('etiquetas')
        context['entidad_tipo'] = 'Categoria'
        return context
    
## CREATE (Crear Nueva Categoria) ##
class CategoriaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'producto/formulario.html' 
    success_url = reverse_lazy('lista_categorias')
    permission_required = 'producto.add_categoria' # Permiso nativo
    raise_exception = True # Mostrar 403 si falla

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Nueva Categoria'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Categoría "{form.instance.nombre}" creada con éxito.')
        return response

## UPDATE (Editar Categoria) ##
class CategoriaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'producto/formulario.html' 
    success_url = reverse_lazy('lista_categorias')
    permission_required = 'producto.change_categoria' # Permiso nativo

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Categoría: "{self.object.nombre}"'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Categoría "{self.object.nombre}" actualizada con éxito.')
        return response

## DELETE (Eliminar Categoria) ##
class CategoriaDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Categoria
    template_name = 'producto/categorias/categoria_eliminar.html'
    context_object_name = 'categoria'
    success_url = reverse_lazy('lista_categorias')
    permission_required = 'producto.delete_categoria' # Permiso nativo

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Categoría: "{self.object.nombre}"'
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        nombre_categoria = self.object.nombre
        messages.warning(request, f'Categoría "{nombre_categoria}" eliminada permanentemente.')
        self.object.delete()
        return HttpResponseRedirect(self.get_success_url())


# ====================== # 
# CRUD ETIQUETA (CBV)    #
# ====================== #

## READ (Lista de Etiquetas) ##
class EtiquetaListView(ListView):
    model = Etiqueta
    template_name = 'producto/etiquetas/etiqueta_lista.html'
    context_object_name = 'lista_etiquetas'
    ordering = ['nombre']

    def get_queryset(self):
        queryset = Etiqueta.objects.annotate(total_productos=Count('productos_asociados'))
        return queryset.order_by('-total_productos', 'nombre') 

## READ (Detalle de Etiqueta) ##
class EtiquetaDetailView(DetailView):
    model = Etiqueta
    template_name = 'producto/listado_relacionado.html' 
    context_object_name = 'entidad'

    def get_queryset(self):
        return Etiqueta.objects.prefetch_related('productos_asociados')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["productos_relacionados"] = self.object.productos_asociados.all().select_related('categoria', 'detalles').prefetch_related('etiquetas')
        context['entidad_tipo'] = 'Etiqueta'
        return context
    
## CREATE (Crear Nueva Etiqueta) ##
class EtiquetaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Etiqueta
    form_class = EtiquetaForm
    template_name = 'producto/formulario.html' 
    success_url = reverse_lazy('lista_etiquetas')
    permission_required = 'producto.add_etiqueta'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Nueva Etiqueta'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Etiqueta "{form.instance.nombre}" creada con éxito.')
        return response

## UPDATE (Editar Etiqueta) ##
class EtiquetaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Etiqueta
    form_class = EtiquetaForm
    template_name = 'producto/formulario.html'
    success_url = reverse_lazy('lista_etiquetas')
    permission_required = 'producto.change_etiqueta'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Etiqueta: "{self.object.nombre}"'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Etiqueta "{self.object.nombre}" actualizada con éxito.')
        return response

## DELETE (Eliminar Etiqueta) ##
class EtiquetaDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Etiqueta
    template_name = 'producto/etiquetas/etiqueta_eliminar.html'
    context_object_name = 'etiqueta'
    success_url = reverse_lazy('lista_etiquetas')
    permission_required = 'producto.delete_etiqueta'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar Etiqueta: "{self.object.nombre}"'
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        nombre_etiqueta = self.object.nombre
        messages.warning(request, f'Etiqueta "{nombre_etiqueta}" eliminada permanentemente.')
        self.object.delete()
        return HttpResponseRedirect(self.get_success_url())


# =============================== # 
#   AUTENTICACION/REGISTRO (CBV)  #
# =============================== #

class RegistroView(CreateView):
    """ Maneja el registro de nuevos usuarios. """
    form_class = CustomUserCreationForm
    template_name = 'producto/autenticacion/registro.html'
    success_url = reverse_lazy('login') 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Registro de Nuevo Usuario'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Se ha registrado "{form.instance.username}" exitosamente. ¡Inicia sesión ahora!')
        return response

# ============================================== # 
#   USUARIO AUTENTICADO/LOGEADO (CBV con Mixin)  #
# ============================================== #

class PerfilPersonalView(LoginRequiredMixin, TemplateView):
    """ Muestra la página privada del usuario. """
    template_name = 'producto/autenticacion/perfil_personal.html' 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        favoritos_queryset = user.productos_favoritos.all().select_related('categoria', 'detalles').prefetch_related('etiquetas')

        context['titulo'] = f'Bienvenido, {user.username}!'
        context['mensaje'] = 'Este es tu perfil personal y aquí gestionarás tus productos favoritos.'
        context['productos_favoritos'] = favoritos_queryset
        return context

class CustomLoginView(BaseLoginView):
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'{self.request.user.username}, ¡has iniciado sesión con éxito! Bienvenido a TechShop.')
        return response

def custom_logout(request):
    """ Cierra la sesión y añade el mensaje de despedida. """
    messages.info(request, "Tu sesión se ha cerrado exitosamente. ¡Vuelve pronto!")
    auth_logout(request) 
    return redirect('home')