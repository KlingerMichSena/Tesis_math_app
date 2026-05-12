"""
URL configuration for tesis_math_app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.contrib.auth import views as auth_views
from web.forms import CustomAuthenticationForm

urlpatterns = [
    path('admin/', admin.site.urls),

    # 1. La ruta raíz ahora muestra la vista de login de Django.
    #    Usará tu plantilla 'web/login.html'.
    path('', auth_views.LoginView.as_view(
        template_name='web/login.html',
        authentication_form=CustomAuthenticationForm
    ), name='login'),

    # 2. Ruta para el proceso de logout.
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # 3. Incluimos las URLs de la app 'web' (como /simulador/).
    path('', include('web.urls')),
    
    # Aquí puedes agregar las rutas para 'registro' y 'recuperar_contrasena'
    # path('registro/', views.registro_view, name='registro'),
    # path('recuperar-contrasena/', views.recuperar_view, name='recuperar_contrasena'),
]
