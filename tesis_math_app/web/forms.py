from django import forms
from django.contrib.auth.forms import AuthenticationForm

class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizamos el campo 'username' para que funcione como un campo de email.
        self.fields['username'].label = "Correo Electrónico"
        # Reemplazamos el widget por un EmailInput para asegurar el tipo de campo HTML.
        # Esto es más limpio que modificar el atributo 'input_type' de una instancia.
        self.fields['username'].widget = forms.EmailInput(attrs={
            'class': 'form-control mb-2', 'placeholder': 'correo@ejemplo.com', 'autofocus': True
        })
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Contraseña'})


class SimuladorForm(forms.Form):
    METODOS = [
        ('CN', 'Crank-Nicolson'),
        ('DF', 'Diferencias Finitas'),
    ]
    
    metodo = forms.ChoiceField(
        choices=METODOS, 
        label="Método de Cálculo",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Campos de entrada
    k1 = forms.FloatField(label='Permeabilidad Capa 1 (k1)', initial=2e-11, widget=forms.TextInput)
    k2 = forms.FloatField(label='Permeabilidad Capa 2 (k2)', initial=10e-12, widget=forms.TextInput)
    t_max = forms.IntegerField(label='Tiempo Máximo (s)', initial=5000)
    dt = forms.FloatField(label='Paso de tiempo (dt)', initial=1.0, widget=forms.TextInput)
    sw_inj = forms.FloatField(label='Saturación Inyección', initial=0.372, widget=forms.TextInput)
    sw_ini = forms.FloatField(label='Saturación Inicial', initial=0.72, widget=forms.TextInput)
    phi = forms.FloatField(label='Porosidad (phi)', initial=0.25, widget=forms.TextInput)
    sw_star = forms.FloatField(label='Saturación Crítica (Sw*)', initial=0.37, widget=forms.TextInput)
    window_size = forms.IntegerField(label='Tamaño de Ventana (window_size)', 
                                    initial=12,
                                    help_text='Tamaño de ventana para suavizado de nD'
                                    )
    
