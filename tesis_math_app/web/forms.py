from django import forms

class SimuladorForm(forms.Form):
    METODOS = [
        ('CN', 'Crank-Nicolson'),
        ('DF', 'Diferencias Finitas (Próximamente)'),
    ]
    
    metodo = forms.ChoiceField(
        choices=METODOS, 
        label="Método de Cálculo",
        widget=forms.Select(attrs={'class': 'form-select', 'onchange': 'this.form.submit()'})
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
    
