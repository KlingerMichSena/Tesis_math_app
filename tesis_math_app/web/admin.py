from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    # Campos que se muestran en la lista de usuarios
    list_display = ('email', 'nombres', 'apellidos', 'rol', 'is_staff', 'is_active',)
    # Campos por los que se puede buscar
    search_fields = ('email', 'nombres', 'apellidos',)
    # Filtros en la barra lateral
    list_filter = ('rol', 'is_staff', 'is_active',)
    
    # Campos que se muestran en el formulario de edición de usuario
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información Personal', {'fields': ('nombres', 'apellidos', 'rol')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas Importantes', {'fields': ('last_login', 'date_joined')}),
    )
    ordering = ('email',)

admin.site.register(CustomUser, CustomUserAdmin)
