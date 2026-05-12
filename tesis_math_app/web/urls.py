from django.urls import path
from . import views

urlpatterns = [
    # Esta URL corresponderá a /simulador/ y mostrará la interfaz principal
    path('simulador/', views.index, name='simulador'),
]
