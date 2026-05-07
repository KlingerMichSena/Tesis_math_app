#CODIGO USANDO DIFERENCIAS FINITAS
import numpy as np

def ejecutar_simulacion_df(params):
    # Extraer variables del diccionario provenientes de la interfaz
    phi = params['phi']
    k1 = params['k1']
    k2 = params['k2']
    Tmax = params['Tmax']
    dt = params['dt']
    Sw_inj = params['Sw_inj']
    Sw_ini = params['Sw_ini']
    Sw_star = params['Sw_star']
    window_size = params['window_size'] #Tamaño de ventana para suavizado
     
    # -------------------------------
    # PARÁMETROS Y CONDICIONES INICIALES
    # -------------------------------
    Swc = 0.2
    Sgr = 0.18
    mu_w = 1e-3
    mu_g = 2e-5
    A = 400
    theta_s = 3.2e-4

    u1 = 2.93e-6
    u2 = 1.465e-6

    L = 0.10
    Nx = 200
    x = np.linspace(0, L, Nx)
    dx = L / Nx
    Nt = int(Tmax / dt)

    Sw1_all = np.ones((Nt, Nx)) * Sw_ini
    Sw2_all = np.ones((Nt, Nx)) * Sw_ini
    Sw1_all[0, 0] = Sw_inj
    Sw2_all[0, 0] = Sw_inj

    diff_coef_Sw1 = 0.001 * dx**2 / dt
    diff_coef_Sw2 = 0.001 * dx**2 / dt

    # -------------------------------
    # FUNCIONES AUXILIARES
    # -------------------------------
    def nD_eq(Sw):
        return np.where(Sw > Sw_star, np.tanh(A * (Sw - Sw_star)), 0.0)

    def krw(Sw):
        base = np.clip((Sw - Swc)/(1 - Swc - Sgr), 0.0, None)
        return np.where(Sw <= Swc, 0.0, 0.2 * base**4.2)

    def krg0(Sw):
        base = np.clip((1 - Sw - Sgr)/(1 - Swc - Sgr), 0.0, None)
        return np.where(Sw >= 1 - Sgr, 0.0, 0.94 * base**1.3)

    def MRF(nD):
        return np.clip(18500 * nD + 1, 1, 1e6)

    def krg(Sw, nD):
        return krg0(Sw) / MRF(nD)

    def fw(Sw, nD, k):
        lw = k * krw(Sw) / mu_w
        lg = k * krg(Sw, nD) / mu_g
        return lw / (lw + lg + 1e-12)

    def estimar_frente(Sw, x_arr, valor=0.5):
        idx = np.where(Sw >= valor)[0]
        if len(idx) == 0 or idx[0] == 0:
            return 0.0
        i = idx[0]
        x0, x1 = x_arr[i-1], x_arr[i]
        y0, y1 = Sw[i-1], Sw[i]
        return x0 + (valor - y0) * (x1 - x0) / (y1 - y0)
        
    def suavizar_con_bordes(datos, window_size):
        if len(datos) < window_size or window_size < 2:
            return datos
        pad_izq = window_size // 2
        pad_der = window_size - 1 - pad_izq
        datos_padded = np.pad(datos, (pad_izq, pad_der), mode='edge')
        return np.convolve(datos_padded, np.ones(window_size)/window_size, mode='valid')

    # -------------------------------
    # SIMULACIÓN
    # -------------------------------
    tiempos = [0.0]

    for step in range(1, Nt):
        t = step * dt
        tiempos.append(t)
        
        Sw1 = Sw1_all[step-1]
        Sw2 = Sw2_all[step-1]

        nD1 = nD_eq(Sw1)
        nD2 = nD_eq(Sw2)
        fw1 = fw(Sw1, nD1, k1)
        fw2 = fw(Sw2, nD2, k2)

        Sw1_new = Sw1.copy()
        Sw2_new = Sw2.copy()

        # Vectorización (reemplaza el ciclo for para acelerar)
        Sw1_new[1:-1] = Sw1[1:-1] + dt * (
            - u1 * (fw1[1:-1] - fw1[:-2]) / dx
            - theta_s * (Sw1[1:-1] - Sw2[1:-1])
            + diff_coef_Sw1 * (Sw1[2:] - 2*Sw1[1:-1] + Sw1[:-2]) / dx**2
        ) / phi

        Sw2_new[1:-1] = Sw2[1:-1] + dt * (
            - u2 * (fw2[1:-1] - fw2[:-2]) / dx
            + theta_s * (Sw1[1:-1] - Sw2[1:-1])
            + diff_coef_Sw2 * (Sw2[2:] - 2*Sw2[1:-1] + Sw2[:-2]) / dx**2
        ) / phi

        # Condiciones de frontera
        Sw1_new[0] = Sw_inj
        Sw2_new[0] = Sw_inj
        Sw1_new[-1] = Sw1_new[-2]
        Sw2_new[-1] = Sw2_new[-2]

        Sw1_all[step] = Sw1_new
        Sw2_all[step] = Sw2_new

    Sw1_final = Sw1_all[-1]
    Sw2_final = Sw2_all[-1]

    # -------------------------------
    # VELOCIDADES PROMEDIO DEL FRENTE
    # -------------------------------
    valor_frente = (Sw_inj + Sw_ini) / 2
    posiciones_sw1 = [estimar_frente(Sw1_all[i], x, valor_frente) for i in range(Nt)]
    posiciones_sw2 = [estimar_frente(Sw2_all[i], x, valor_frente) for i in range(Nt)]

    # -------------------------------
    # Velocidades promedio del frente
    # -------------------------------
    velocidad_sw1 = np.diff(posiciones_sw1) / dt
    velocidad_sw2 = np.diff(posiciones_sw2) / dt
    
    vent_vel = min(150, len(velocidad_sw1))
    if vent_vel > 0:
        velocidad_sw1_suave = suavizar_con_bordes(velocidad_sw1, vent_vel)
        velocidad_sw2_suave = suavizar_con_bordes(velocidad_sw2, vent_vel)
    else:
        velocidad_sw1_suave = velocidad_sw1
        velocidad_sw2_suave = velocidad_sw2

    # -------------------------------
    # CÁLCULO DE VELOCIDAD TEÓRICA
    # -------------------------------
    fw_inj1 = fw(Sw_inj, nD_eq(Sw_inj), k1)
    fw_ini1 = fw(Sw_ini, nD_eq(Sw_ini), k1)
    v1_teo = (u1 / phi) * (fw_inj1 - fw_ini1) / (Sw_inj - Sw_ini)

    fw_inj2 = fw(Sw_inj, nD_eq(Sw_inj), k2)
    fw_ini2 = fw(Sw_ini, nD_eq(Sw_ini), k2)
    v2_teo = (u2 / phi) * (fw_inj2 - fw_ini2) / (Sw_inj - Sw_ini)

    velocidad_teorica_global = (v1_teo + v2_teo) / 2
    
    x_teorico = velocidad_teorica_global * np.array(tiempos)

    # Error absoluto
    pos_sw1 = np.array(posiciones_sw1)
    pos_sw2 = np.array(posiciones_sw2)
    x_teo = np.array(x_teorico)

    error_sw1 = np.abs(pos_sw1 - x_teo)
    error_sw2 = np.abs(pos_sw2 - x_teo)

    # -------------------------------
    # RETORNO DE RESULTADOS
    # -------------------------------
    return {
        'x': np.real(x).tolist(),
        'Sw1': np.real(Sw1_final).tolist(),
        'Sw2': np.real(Sw2_final).tolist(),
        'tiempos': np.real(tiempos).tolist(),
        'posiciones_sw1': np.real(posiciones_sw1).tolist(),
        'posiciones_sw2': np.real(posiciones_sw2).tolist(),
        'x_teorico': np.real(x_teorico).tolist(),
        'error_sw1': np.real(error_sw1).tolist(),
        'error_sw2': np.real(error_sw2).tolist(),
        'velocidad_sw1': np.real(velocidad_sw1_suave).tolist(),
        'velocidad_sw2': np.real(velocidad_sw2_suave).tolist(),
        'tiempos_v': np.real(tiempos[1:]).tolist(),
        'velocidad_teorica_global': float(np.real(velocidad_teorica_global))
    }