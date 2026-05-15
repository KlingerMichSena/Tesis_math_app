from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    """
    Manager para el modelo de usuario personalizado donde el email es el identificador único.
    """
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(_('El campo Email es obligatorio'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    ROL_CHOICES = (
        ('ESTUDIANTE', 'Estudiante'),
        ('PROFESOR', 'Profesor'),
    )
    # Eliminamos el campo username que viene por defecto en AbstractUser
    username = None
    
    # Campos personalizados
    email = models.EmailField(_('email address'), unique=True)
    nombres = models.CharField(max_length=100, blank=False, null=False)
    apellidos = models.CharField(max_length=100, blank=False, null=False)
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='ESTUDIANTE')

    # Indicamos que el campo 'email' será el usado para el login
    USERNAME_FIELD = 'email'
    # Campos requeridos al crear un usuario por consola (createsuperuser)
    REQUIRED_FIELDS = ['nombres', 'apellidos']

    objects = CustomUserManager()

    def __str__(self):
        return self.email
