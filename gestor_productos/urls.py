"""
URL configuration for gestor_productos project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings            # Necesario para manejar los archivos estáticos en desarrollo/simulación producción
from django.conf.urls.static import static  # Necesario para manejar los archivos estáticos en desarrollo/simulación producción

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('producto.urls'))
]

# Handler personalizado para el error 403. 
# Muestra la falta de permisos al intentar realizar una acción no autorizada
handler403 = 'producto.views.error_403_handler'

# Handler personalizado para el error 404. 
# Solo se activa automáticamente cuando DEBUG = False (entorno de producción)
handler404 = 'producto.views.error_404_handler'

# Bloque condicional para usar los archivos estáticos en el entorno de producción simulado/local (DEBUG=False)
if settings.DEBUG: 
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # Cuando DEBIG=False (simulando producción), debemos servir los estáticos y media manualmente
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)