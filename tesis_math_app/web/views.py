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
    grafica_distancia_html = None
    grafica_error_html = None
    datos_json = None

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
        
        # Convertir resultados a JSON para descargarlos en frontend
        datos_json = json.dumps(res)
        
        # Crear la gráfica con Plotly
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=res['x'], y=res['Sw1'], name='Capa 1 (Sw1)', line=dict(color='#4DD161')))
        fig.add_trace(go.Scatter(x=res['x'], y=res['Sw2'], name='Capa 2 (Sw2)', line=dict(color='#4DBDD1')))
        
        fig.update_layout(
            title="Perfiles de Frente",
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

        # Crear la gráfica de Evolución de la distancia del frente con Plotly
        fig_dist = go.Figure()
        fig_dist.add_trace(go.Scatter(x=res['tiempos'], y=res['posiciones_sw1'], name='Frente capa 1 (Sw1)', line=dict(color='blue')))
        fig_dist.add_trace(go.Scatter(x=res['tiempos'], y=res['posiciones_sw2'], name='Frente capa 2 (Sw2)', line=dict(color='green')))
        fig_dist.add_trace(go.Scatter(x=res['tiempos'], y=res['x_teorico'], name='Modelo teórico', mode='lines', line=dict(color='black', dash='dash')))
        
        fig_dist.update_layout(
            title="Evolución de la distancia del frente",
            xaxis_title="Tiempo [s]",
            yaxis_title="Distancia del frente [m]",
            template="plotly_white"
        )
        
        grafica_distancia_html = plot(fig_dist, output_type='div', include_plotlyjs=False)

        # Crear la gráfica de Error Numérico con Plotly
        fig_error = go.Figure()
        fig_error.add_trace(go.Scatter(x=res['tiempos'], y=res['error_sw1'], name='Error capa 1 (Sw1)', line=dict(color='blue')))
        fig_error.add_trace(go.Scatter(x=res['tiempos'], y=res['error_sw2'], name='Error capa 2 (Sw2)', line=dict(color='green')))
        
        fig_error.update_layout(
            title="Error numérico del frente",
            xaxis_title="Tiempo [s]",
            yaxis_title="Error absoluto [m]",
            template="plotly_white"
        )
        
        grafica_error_html = plot(fig_error, output_type='div', include_plotlyjs=False)

    return render(request, 'web/index.html', {
        'form': form,
        'grafica': grafica_html,
        'grafica_velocidad': grafica_velocidad_html,
        'grafica_distancia': grafica_distancia_html,
        'grafica_error': grafica_error_html,
        'datos_json': datos_json
    })