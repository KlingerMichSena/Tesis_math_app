from django.shortcuts import render
from .forms import SimuladorForm
from core.simulador import ejecutar_simulacion

# Create your views here.
def index(request):
    # Inicializamos el formulario con los datos que vengan por POST o vacíos
    form = SimuladorForm(request.POST or None)
    resultados = None
    mensaje = None

    if request.method == 'POST' and form.is_valid():
        metodo_elegido = form.cleaned_data['metodo']
        
        if metodo_elegido == 'CN':
            # Ejecutamos Crank-Nicolson (Punto 1)
            params = {
                'k1': form.cleaned_data['k1'],
                'k2': form.cleaned_data['k2'],
                'Tmax': form.cleaned_data['t_max'],
                'dt': form.cleaned_data['dt'],
                'Sw_inj': form.cleaned_data['sw_inj'],
                'Sw_ini': form.cleaned_data['sw_ini'],
            }
            resultados = ejecutar_simulacion(params)
        else:
            mensaje = "El método de Diferencias Finitas está en desarrollo."

    return render(request, 'web/index.html', {
        'form': form, 
        'resultados': resultados,
        'mensaje': mensaje
    })