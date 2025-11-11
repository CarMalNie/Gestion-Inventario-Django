from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.auth import logout as auth_logout

urlpatterns = [

    # Página Inicio "Home"
    path('', views.home, name='home'),

    # PRODUCTOS CRUD (usa FBV)
    path('productos/', views.lista_productos, name='lista_productos'), # READ Lista Producto
    path('productos/crear/', views.crear_producto, name='crear_producto'), # CREATE
    path('productos/<int:pk>/detalle/', views.detalle_producto, name='detalle_producto'), # READ Detalle Producto
    path('productos/<int:pk>/editar/', views.editar_producto, name='editar_producto'), # UPDATE
    path('productos/<int:pk>/eliminar/', views.eliminar_producto, name='eliminar_producto'), # DELETE

    # Ruta acción para Toggle Producto Favorito
    path('productos/<int:pk>/favorito/', views.toggle_favorito, name='toggle_favorito'),

    # Categorias CRUD (usa CBV)
    path('categorias/', views.CategoriaListView.as_view(), name='lista_categorias'), # READ Lista Categorias
    path('categorias/crear/', views.CategoriaCreateView.as_view(), name='crear_categoria'), # CREATE 
    path('categorias/<int:pk>/', views.CategoriaDetailView.as_view(), name='detalle_categoria'), # READ Detalle Categoria
    path('categorias/<int:pk>/editar/', views.CategoriaUpdateView.as_view(), name='editar_categoria'), # UPDATE
    path('categorias/<int:pk>/eliminar/', views.CategoriaDeleteView.as_view(), name='eliminar_categoria'), # DELETE

    # Etiquetas CRUD (usa CBV)
    path('etiquetas/', views.EtiquetaListView.as_view(), name='lista_etiquetas'), # READ Lista Etiquetas
    path('etiquetas/crear/', views.EtiquetaCreateView.as_view(), name='crear_etiqueta'), # CREATE
    path('etiquetas/<int:pk>/', views.EtiquetaDetailView.as_view(), name='detalle_etiqueta'), # READ Detalle Etiqueta
    path('etiquetas/<int:pk>/editar/', views.EtiquetaUpdateView.as_view(), name='editar_etiqueta'), # UPDATE
    path('etiquetas/<int:pk>/eliminar/', views.EtiquetaDeleteView.as_view(), name='eliminar_etiqueta'), # DELETE

    # Reporte SQL RAW
    path('reportes/productos-etiquetas/', views.reporte_productos_etiquetas, name='reporte_sql_etiquetas'),

    # URL para el Registro (CBV)
    path('registro/', views.RegistroView.as_view(), name='registro'),
    
    # URL para Login (CBV)
    path('login/', views.CustomLoginView.as_view(template_name='producto/autenticacion/login.html', form_class=AuthenticationForm ), name='login'),
    
    # URL para Logout (CBV)
    path('logout/', views.custom_logout, name='logout'),
    
    # URL para PERFIL PRIVADO
    path('perfil/', views.PerfilPersonalView.as_view(), name='perfil_personal'),

]