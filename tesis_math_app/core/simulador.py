
# In[1]:
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import clear_output
from scipy.linalg import solve_banded

# Encapsulamos todo en una función que recibe un diccionario de parámetros
def ejecutar_simulacion(params):
    # Extraer variables del diccionario (usando valores por defecto del script original)
    phi = params.get('phi', 0.25)
    k1 = params.get('k1', 2e-11)
    k2 = params.get('k2', 10e-12)
    Tmax = params.get('Tmax', 5000)
    dt = params.get('dt', 1)
    Sw_inj = params.get('Sw_inj', 0.372)
     
    # -------------------------------
    # PARÁMETROS Y CONDICIONES INICIALES
    # -------------------------------
    phi = 0.25
    Swc = 0.2
    Sgr = 0.18
    mu_w = 1e-3
    mu_g = 2e-5
    k1 = 2e-11
    k2 = 10e-12
    Sw_star = 0.37
    A = 400
    sigma = 0.03
    c = 0.01
    d = 5e-3
    theta_s = 3.2e-4

    u1 = 2.93e-6
    u2 = 1.465e-6

    L = 0.10
    Nx = 200
    x = np.linspace(0, L, Nx)
    dx = L / Nx
    Tmax = 5000
    dt = 1
    Nt = int(Tmax / dt)

    Sw_inj = 0.372
    Sw_ini = 0.72

    # Saturaciones
    Sw1 = np.ones(Nx) * Sw_ini
    Sw2 = np.ones(Nx) * Sw_ini
    Sw1[0] = Sw_inj
    Sw2[0] = Sw_inj

    # Coeficientes de difusión artificial
    a = 1e-7 # esto pesa mas que la reguarización por media movil.
    D1 = a * dx**2 / dt
    D2 = a * dx**2 / dt

    # --- NUEVAS VARIABLES PARA VELOCIDAD Y TIEMPO ---
    posiciones_sw1 = []
    posiciones_sw2 = []
    tiempos = []
    valor_frente = (Sw_inj + Sw_ini) / 2

    # -------------------------------
    # FUNCIONES AUXILIARES
    # -------------------------------
    def nD_eq(Sw):
        return np.where(Sw > Sw_star, np.tanh(A * (Sw - Sw_star)), 0.0)

    def krw(Sw):
        return np.where(Sw <= Swc, 0.0, 0.2 * ((Sw - Swc)/(1 - Swc - Sgr))**4.2)

    def krg0(Sw):
        return np.where(Sw >= 1 - Sgr, 0.0, 0.94 * ((1 - Sw - Sgr)/(1 - Swc - Sgr))**1.3)

    def MRF(nD):
        return np.clip(18500 * nD + 1, 1, 1e6)

    def krg(Sw, nD):
        return krg0(Sw) / MRF(nD)

    def fw(Sw, nD, k):
        lw = k * krw(Sw) / mu_w
        lg = k * krg(Sw, nD) / mu_g
        return lw / (lw + lg + 1e-12)

    def suavizar_nD(nD, window_size=12):
        nD_suave = nD.copy()
        for i in range(1, len(nD) - 1):
            ini = max(0, i - window_size // 2)
            fin = min(len(nD), i + window_size // 2 + 1)
            nD_suave[i] = np.mean(nD[ini:fin])
        return nD_suave

    def construir_matriz_CN(Nx, D, phi, dt, dx):
        alpha = D * dt / (2 * phi * dx**2)
        A_mat = np.zeros((3, Nx))
        A_mat[0, 1:] = -alpha
        A_mat[1, :] = 1 + 2 * alpha
        A_mat[2, :-1] = -alpha
        A_mat[1, 0] = 1.0
        A_mat[0, 1] = 0.0
        A_mat[2, -1] = 0.0
        A_mat[1, -1] = 1.0
        return A_mat

    def construir_rhs_CN(Sw_old, adv, D, phi, dt, dx):
        alpha = D * dt / (2 * phi * dx**2)
        rhs = Sw_old.copy()
        for i in range(1, Nx - 1):
            rhs[i] += dt * adv[i] / phi
            rhs[i] += alpha * (Sw_old[i+1] - 2*Sw_old[i] + Sw_old[i-1])
        rhs[0] = Sw_inj
        rhs[-1] = Sw_old[-1]
        return rhs

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
    # CÁLCULO DE VELOCIDAD TEÓRICA
    # -------------------------------
    fw_inj1 = fw(Sw_inj, nD_eq(Sw_inj), k1)
    fw_ini1 = fw(Sw_ini, nD_eq(Sw_ini), k1)
    v1_teo = (u1 / phi) * (fw_inj1 - fw_ini1) / (Sw_inj - Sw_ini)

    fw_inj2 = fw(Sw_inj, nD_eq(Sw_inj), k2)
    fw_ini2 = fw(Sw_ini, nD_eq(Sw_ini), k2)
    v2_teo = (u2 / phi) * (fw_inj2 - fw_ini2) / (Sw_inj - Sw_ini)

    velocidad_teorica_global = (v1_teo + v2_teo) / 2

    # -------------------------------
    # SIMULACIÓN
    # -------------------------------
    for step in range(Nt):
        t = step * dt

        nD1 = nD_eq(Sw1)
        nD2 = nD_eq(Sw2)
        nD1s = suavizar_nD(nD1, window_size=1)
        nD2s = suavizar_nD(nD2, window_size=1)

        fw1 = fw(Sw1, nD1, k1)
        fw2 = fw(Sw2, nD2, k2)

        adv1 = np.zeros(Nx)
        adv2 = np.zeros(Nx)
        for i in range(1, Nx):
            adv1[i] = -u1 * (fw1[i] - fw1[i-1]) / dx - theta_s * (Sw1[i] - Sw2[i])
            adv2[i] = -u2 * (fw2[i] - fw2[i-1]) / dx + theta_s * (Sw1[i] - Sw2[i])

        A1 = construir_matriz_CN(Nx, D1, phi, dt, dx)
        b1 = construir_rhs_CN(Sw1, adv1, D1, phi, dt, dx)

        A2 = construir_matriz_CN(Nx, D2, phi, dt, dx)
        b2 = construir_rhs_CN(Sw2, adv2, D2, phi, dt, dx)

        Sw1 = solve_banded((1, 1), A1, b1)
        Sw2 = solve_banded((1, 1), A2, b2)

        Sw1[0] = Sw_inj
        Sw2[0] = Sw_inj

        # Seguimiento de la posición
        posiciones_sw1.append(estimar_frente(Sw1, x, valor_frente))
        posiciones_sw2.append(estimar_frente(Sw2, x, valor_frente))
        tiempos.append(t)

        # Animación
        if step % 200 == 0 and step > 0:
            clear_output(wait=True)

            # Suavizar perfiles
            vent_espacial = 20
            Sw1_suave = suavizar_con_bordes(Sw1, vent_espacial)
            Sw2_suave = suavizar_con_bordes(Sw2, vent_espacial)
            nD1_suave = suavizar_con_bordes(nD1s, vent_espacial)
            nD2_suave = suavizar_con_bordes(nD2s, vent_espacial)

            # Calcular y suavizar velocidad
            v1_bruta = np.diff(posiciones_sw1) / dt
            v2_bruta = np.diff(posiciones_sw2) / dt

            vent_vel = min(150, len(v1_bruta))
            if vent_vel > 0:
                v1_suave = suavizar_con_bordes(v1_bruta, vent_vel)
                v2_suave = suavizar_con_bordes(v2_bruta, vent_vel)
                tiempos_v = tiempos[1:]
            else:
                v1_suave, v2_suave, tiempos_v = [], [], []

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 4))

            # Panel 1: Perfiles
            ax1.plot(x, Sw1_suave, label='Sw1', color='blue')
            ax1.plot(x, Sw2_suave, label='Sw2', color='green')
            ax1.plot(x, nD1_suave, label='nD1', color='orange', linestyle='--')
            ax1.plot(x, nD2_suave, label='nD2', color='red', linestyle='--')
            ax1.set_title(f"Perfiles t = {t:.1f} s")
            ax1.set_xlabel("x [m]")
            ax1.set_xlim(0, L)
            ax1.set_ylim(0, 1.1)
            ax1.set_ylabel("Sw, nD")
            ax1.legend()
            ax1.grid()

            # Panel 2: Velocidad
            if len(v1_suave) > 0:
                ax2.plot(tiempos_v, v1_suave, label='Velocidad Sw1', color='blue')
                ax2.plot(tiempos_v, v2_suave, label='Velocidad Sw2', color='green')

            # AGREGADO: LÍNEA DE VELOCIDAD TEÓRICA
            ax2.axhline(velocidad_teorica_global, color='black', linestyle='--', linewidth=2, label='Velocidad Teórica')

            ax2.set_title("Velocidad Promedio de Frentes")
            ax2.set_xlabel("t [s]")
            ax2.set_ylim(0, 4800)
            ax2.set_ylabel("v [m/s]")
            ax2.set_ylim(-1e-5, 5e-5)
            ax2.legend()
            ax2.grid()

            plt.tight_layout()
            #plt.show()

    # -------------------------------
    # VELOCIDADES PROMEDIO DEL FRENTE
    # -------------------------------
    velocidad_sw1 = np.diff(posiciones_sw1) / dt
    velocidad_sw2 = np.diff(posiciones_sw2) / dt
    promedio_v_sw1 = np.mean(velocidad_sw1)
    promedio_v_sw2 = np.mean(velocidad_sw2)
    velocidad_promedio = (promedio_v_sw1 + promedio_v_sw2) / 2

    print("-" * 45)
    print(f"Velocidad teórica global esperada: {velocidad_teorica_global:.4e} m/s")
    print(f"Velocidad promedio del frente en capa 1: {promedio_v_sw1:.4e} m/s")
    print(f"Velocidad promedio del frente en capa 2: {promedio_v_sw2:.4e} m/s")
    print(f"Velocidad promedio del sistema:          {velocidad_promedio:.4e} m/s")
    print("-" * 45)

    # -------------------------------
    # GRÁFICA DISTANCIA vs TIEMPO
    # -------------------------------
    # Línea teórica: x = v * t
    x_teorico = velocidad_teorica_global * np.array(tiempos)

    # Convertir a arrays (por seguridad)
    pos_sw1 = np.array(posiciones_sw1)
    pos_sw2 = np.array(posiciones_sw2)
    x_teo = np.array(x_teorico)

    # Error absoluto
    error_sw1 = np.abs(pos_sw1 - x_teo)
    error_sw2 = np.abs(pos_sw2 - x_teo)

    plt.figure(figsize=(8,5))

    plt.plot(tiempos, posiciones_sw1, label='Frente capa 1 (Sw1)', color='blue')
    plt.plot(tiempos, posiciones_sw2, label='Frente capa 2 (Sw2)', color='green')
    plt.plot(tiempos, x_teorico, '--', label='Modelo teórico', color='black')

    plt.title("Evolución de la distancia del frente")
    plt.xlabel("Tiempo [s]")
    plt.ylabel("Distancia del frente [m]")
    plt.legend()
    plt.grid()

    #plt.show()

    # -------------------------------
    # ERROR NUMERICO
    # -------------------------------

    plt.figure(figsize=(8,5))

    plt.plot(tiempos, error_sw1, label='Error capa 1 (Sw1)')
    plt.plot(tiempos, error_sw2, label='Error capa 2 (Sw2)')

    plt.title("Error numérico del frente")
    plt.xlabel("Tiempo [s]")
    plt.ylabel("Error absoluto [m]")
    plt.legend()
    plt.grid()

    #plt.show()

    #print("Error máximo Sw1:", np.max(error_sw1))
    #print("Error máximo Sw2:", np.max(error_sw2))

    #print("Error promedio Sw1:", np.mean(error_sw1))
    #print("Error promedio Sw2:", np.mean(error_sw2))

#RETORNO DE RESULTADOS (Lo que recibirá Django)
    return {
        'x': x.tolist(),
        'Sw1': Sw1.tolist(),
        'Sw2': Sw2.tolist(),
        'tiempos': tiempos,
        'posiciones_sw1': posiciones_sw1,
        'posiciones_sw2': posiciones_sw2,
        'x_teorico': x_teorico.tolist(),
        'error_sw1': error_sw1.tolist()
    }