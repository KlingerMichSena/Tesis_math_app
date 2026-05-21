import plotly.graph_objects as go
from plotly.offline import plot
import json
from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import SimuladorForm, CustomUserCreationForm
from core.simulador import ejecutar_simulacion
from core.df_simulador import ejecutar_simulacion_df

def register_view(request):
    # Si el usuario ya está autenticado, lo redirigimos al simulador
    #if request.user.is_authenticated:
     #   return redirect('simulador')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Cuenta creada exitosamente! Ahora puedes iniciar sesión.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'web/register.html', {'form': form})

@login_required
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
            'window_size': form.cleaned_data['window_size'],
            'paso_animacion': form.cleaned_data['paso_animacion'],
        }
        
        # Ejecutar modelo matemático
        if form.cleaned_data['metodo'] == 'CN':
            res = ejecutar_simulacion(params)
        else:
            res = ejecutar_simulacion_df(params)
        
        # Excluir los datos de animación del JSON para descarga, que es muy pesado.
        datos_para_descarga = {k: v for k, v in res.items() if k != 'animation_frames'}
        datos_json = json.dumps(datos_para_descarga)
        
        # Crear la gráfica con Plotly
        fig = go.Figure()

        # --- Lógica para Gráfica Animada ---
        animation_frames = res.get('animation_frames', [])
        if animation_frames:
            # Usar el primer cuadro como estado inicial de la gráfica
            initial_frame_data = animation_frames[0]
            fig.add_trace(go.Scatter(x=res['x'], y=initial_frame_data['Sw1'], name='Capa 1 (Sw1)', line=dict(color='#4DD161')))
            fig.add_trace(go.Scatter(x=res['x'], y=initial_frame_data['Sw2'], name='Capa 2 (Sw2)', line=dict(color='#4DBDD1')))

            # Crear los cuadros (frames) para la animación
            frames = []
            for frame_data in animation_frames:
                frame = go.Frame(
                    data=[
                        go.Scatter(x=res['x'], y=frame_data['Sw1']),
                        go.Scatter(x=res['x'], y=frame_data['Sw2'])
                    ],
                    name=f"{frame_data['t']:.1f}" # Nombre del cuadro, usado por el slider
                )
                frames.append(frame)
            fig.frames = frames

            # Configurar los botones de Play/Pause y el slider
            fig.update_layout(
                updatemenus=[{
                    'type': 'buttons',
                    'buttons': [
                        {'label': 'Play', 'method': 'animate', 'args': [None, {'frame': {'duration': 50, 'redraw': True}, 'fromcurrent': True, 'transition': {'duration': 0}}]},
                        {'label': 'Pause', 'method': 'animate', 'args': [[None], {'frame': {'duration': 0, 'redraw': False}, 'mode': 'immediate'}]}
                    ],
                    'direction': 'left', 'pad': {'r': 10, 't': 70}, 'showactive': False, 'x': 0.1, 'xanchor': 'right', 'y': 0, 'yanchor': 'top'
                }],
                sliders=[{
                    'active': 0,
                    'steps': [{'label': f.name + 's', 'method': 'animate', 'args': [[f.name], {'frame': {'duration': 100, 'redraw': True}, 'mode': 'immediate'}]} for f in fig.frames],
                    'transition': {'duration': 10},
                    'currentvalue': {'prefix': 'Tiempo: ', 'visible': True, 'xanchor': 'right'},
                    'pad': {'t': 20, 'b': 10},
                    'len': 0.9, 'x': 0.05, 'y': 0, 'yanchor': 'top'
                }]
            )
        else:
            # Fallback si no hay datos de animación
            fig.add_trace(go.Scatter(x=res['x'], y=res['Sw1'], name='Capa 1 (Sw1)', line=dict(color='#4DD161')))
            fig.add_trace(go.Scatter(x=res['x'], y=res['Sw2'], name='Capa 2 (Sw2)', line=dict(color='#4DBDD1')))
        
        fig.update_layout(
            title="Perfiles de Frente (Animado)",
            xaxis_title="Distancia [m]",
            yaxis_title="Saturación (Sw)",
            template="plotly_white",
            # Asegurar que los ejes no cambien durante la animación
            xaxis={'range': [0, res['x'][-1]]},
            yaxis={'range': [min(params['Sw_inj'], params['Sw_ini']) - 0.1, max(params['Sw_inj'], params['Sw_ini']) + 0.1]}
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
            template="plotly_white",
            xaxis_range=[0, params['Tmax']] # Limitar el eje X al tiempo máximo de la simulación
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