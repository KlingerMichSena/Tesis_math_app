import plotly.graph_objects as go
from plotly.offline import plot
import json
from django.shortcuts import render
from .forms import SimuladorForm
from core.simulador import ejecutar_simulacion

def index(request):
    form = SimuladorForm(request.POST or None)
    grafica_html = None
    grafica_velocidad_html = None

    if request.method == 'POST' and form.is_valid():
        params = {
            'k1': form.cleaned_data['k1'],
            'k2': form.cleaned_data['k2'],
            'Tmax': form.cleaned_data['t_max'],
            'dt': form.cleaned_data['dt'],
            'Sw_inj': form.cleaned_data['sw_inj'],
            'Sw_ini': form.cleaned_data['sw_ini'],
            'phi': form.cleaned_data['phi'],
            'Sw_star': form.cleaned_data['sw_star'],
            'window_size': form.cleaned_data['window_size']
        }
        
        # Ejecutar modelo matemático
        res = ejecutar_simulacion(params)
        
        # Crear la gráfica con Plotly
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=res['x'], y=res['Sw1'], name='Capa 1 (Sw1)', line=dict(color='#4DD161')))
        fig.add_trace(go.Scatter(x=res['x'], y=res['Sw2'], name='Capa 2 (Sw2)', line=dict(color='#4DBDD1')))
        
        fig.update_layout(
            title="Perfiles de frende",
            xaxis_title="Distancia [m]",
            yaxis_title="Saturación (Sw)",
            template="plotly_white"
        )

        # Convertir la figura a HTML para insertarla en el template
        grafica_html = plot(fig, output_type='div', include_plotlyjs=False)

        # Crear la gráfica de Velocidad Promedio con Plotly
        fig_vel = go.Figure()
        fig_vel.add_trace(go.Scatter(x=res['tiempos_v'], y=res['velocidad_sw1'], name='Velocidad Capa 1', line=dict(color='blue')))
        fig_vel.add_trace(go.Scatter(x=res['tiempos_v'], y=res['velocidad_sw2'], name='Velocidad Capa 2', line=dict(color='green')))
        
        # Línea de velocidad teórica (Línea horizontal recta de inicio a fin)
        fig_vel.add_trace(go.Scatter(x=[res['tiempos_v'][0], res['tiempos_v'][-1]], 
                                     y=[res['velocidad_teorica_global'], res['velocidad_teorica_global']], 
                                     name='Velocidad Teórica', mode='lines', line=dict(color='black', dash='dash')))
        
        fig_vel.update_layout(
            title="Velocidad Promedio de Frentes",
            xaxis_title="Tiempo [s]",
            yaxis_title="Velocidad (v) [m/s]",
            template="plotly_white"
        )
        grafica_velocidad_html = plot(fig_vel, output_type='div', include_plotlyjs=False)

    return render(request, 'web/index.html', {
        'form': form,
        'grafica': grafica_html
        'grafica': grafica_html,
        'grafica_velocidad': grafica_velocidad_html
    })