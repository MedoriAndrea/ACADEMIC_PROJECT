# Import delle librerie
import numpy as np
import sympy as sp
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
import matplotlib.animation as animation
from matplotlib.animation import PillowWriter
from matplotlib import gridspec
import dill

# Caricamento dello spazio di lavoro
with open('Spazio_di_Lavoro_Medori.pkl', 'rb') as file:
    reachable_points = dill.load(file)
# Caricamento funzionale (distanza dal fine corsa)
with open('W_q_numpy_functions_fine_corsa.pkl', 'rb') as file:
    dw_dq_func = dill.load(file)

# Lunghezza link
l1 = 0.065
l2 = 0.065
l3 = 0.03
d3 = 0.03
d4 = 0.105

# Parametri del manipolatore 
a = np.array([l1, l2, 0.0, l3])
q0 = np.array([0, 0, 0, 0])
d = np.array([0, 0, -d3, d4])
alpha = np.array([-np.pi/2, np.pi/2, -np.pi/2, 0])

#-----------------------------------------
# DEFINISCO LE FUNZIONI UTILI PER IL MAIN
#-----------------------------------------

#  FUNZIONE PER CALCOLARE MATRICI DI TRASFORMAZIONE DI D-H
def DH(d, a, alpha, theta):
    T = np.array([
        [np.cos(theta), -np.sin(theta)*np.cos(alpha), np.sin(theta)*np.sin(alpha), a*np.cos(theta)],
        [np.sin(theta), np.cos(theta)*np.cos(alpha), -np.cos(theta)*np.sin(alpha), a*np.sin(theta)],
        [0.0,           np.sin(alpha),               np.cos(alpha),               d],
        [0.0,           0.0,                         0.0,                         1.0]
    ])
    return T

Tb0 = DH(0, 0, np.pi/2, 0)

# FUNZIONE PER IL CALCOLO DELLO JACOBIANO

def Jacobian(q):
    # Trasformazioni DH relative tra giunti
    T01 = DH(d[0], a[0], alpha[0], q[0])
    T12 = DH(d[1], a[1], alpha[1], q[1])
    T23 = DH(d[2], a[2], alpha[2], q[2])
    T34 = DH(d[3], a[3], alpha[3], q[3])

    T0 = Tb0     
    T1 = np.matmul(T0, T01)
    T2 = np.matmul(T1, T12)
    T3 = np.matmul(T2, T23)
    T4 = np.matmul(T3, T34)

    # Vettori z degli assi di rotazione
    z0 = T0[:3, 2]
    z1 = T1[:3, 2]
    z2 = T2[:3, 2]
    z3 = T3[:3, 2]

    # Vettori posizione dei giunti 
    p0 = T0[:3, 3]
    p1 = T1[:3, 3]
    p2 = T2[:3, 3]
    p3 = T3[:3, 3]
    p_ee = T4[:3, 3]

    # Jacobiano parte lineare
    J = np.column_stack((
        np.cross(z0, p_ee - p0),
        np.cross(z1, p_ee - p1),
        np.cross(z2, p_ee - p2),
        np.cross(z3, p_ee - p3)
    ))

    return J

# FUNZIONE PER IL CALCOLO DELLA CINEMATICA DIRETTA

def dir_kin(Qd):
    T01 = DH(d[0], a[0], alpha[0], Qd[0])
    T12 = DH(d[1], a[1], alpha[1], Qd[1])
    T23 = DH(d[2], a[2], alpha[2], Qd[2])
    T34 = DH(d[3], a[3], alpha[3], Qd[3])

    Tb1 = np.matmul(Tb0, T01)
    Tb2 = np.matmul(Tb1, T12)
    Tb3 = np.matmul(Tb2, T23)
    Tb4 = np.matmul(Tb3, T34)

    p_1 = Tb1[:3, 3]
    p_2 = Tb2[:3, 3]
    p_3 = Tb3[:3, 3]
    p_ee = Tb4[:3, 3]

    joint_1 = p_1  
    joint_2 = p_2
    corner_point = p_3
    joint_3 = p_3 + d4 * Tb3[:3, 2]
    joint_4 = p_ee
    

    return p_1, p_2, p_3, p_ee, joint_1, joint_2, joint_3, joint_4, corner_point

# FUNZIONE PER IL CALCOLO DEL CENTRO DI UN ARCO DI CIRCONFERENZA

def center(p1, p2, radius):

    PM = (p1 + p2) / 2   # Calcola il punto medio tra p1 e p2
    p1p2 = p2 - p1    # Calcola il vettore che collega p1 a p2

    # Scegli un vettore ausiliario non parallelo a p1p2
    v = np.array([0, 0, 1]) 
    if np.allclose(np.cross(p1p2, v), 0):
        v = np.array([0, 1, 0])  # Se p1p2 è parallelo a Z, usa il vettore lungo Y

    # Calcola un vettore perpendicolare a p1p2 e v tramite il prodotto vettoriale
    perp_p1p2 = np.cross(p1p2, v)
    
    # Normalizza il vettore perpendicolare (diventa un vettore unitario)
    perp_p1p2 = perp_p1p2 / np.linalg.norm(perp_p1p2)

    # Calcolo la metà della lunghezza del segmento p1p2 
    half_p1p2_length = np.linalg.norm(p1p2) / 2

    # Se il raggio è troppo piccolo (minore della metà della distanza), non è possibile trovare un centro
    if radius <= half_p1p2_length:
        raise ValueError("\nNon è possibile trovare un centro con il raggio fornito \n")

    # Calcola la distanza tra il punto medio e il centro dell'arco
    dist = np.sqrt(radius**2 - half_p1p2_length**2)

    # Calcola il centro dell'arco come il punto medio più la distanza lungo il vettore perpendicolare
    C = PM + dist * perp_p1p2

    return C

# FUNZIONE PER PIANIFICRE UN ARCO DI CIRCONFERENZA NELLO SPAZIO OPERATIVO

def CircumferencePlanner(C, pi, pf, t0, tf, t, path):        
    rho = np.linalg.norm(pi - C) # raggio
    
    # Considerazioni geometriche (da arcsin passo a arctan per robustezza numerica)
    # tan(theta/2) = (d/2) / ( radice2 ( rho**2 - (d/2)**2 ) ) con d pari alla distanza tra pf e pi
    theta1 = 2 * np.arctan2(0.5 * np.linalg.norm(pf - pi), np.sqrt(rho**2 - (0.25 * np.linalg.norm(pf - pi)**2)))
    theta2 = 2 * np.pi - theta1
    short_arc = rho * min(theta1, theta2)
    long_arc = rho * max(theta1, theta2)

    if t <= t0:
        pd = pi
        pdot = np.zeros(3)
        
    elif t>=tf:
        pd = pf
        pdot = np.zeros(3)

    else :
        A = np.array([
            [t0**3, t0**2, t0, 1],
            [tf**3, tf**2, tf, 1],
            [ 3*t0**2, 2*t0, 1, 0],
            [ 3*tf**2, 2*tf, 1, 0],
        ])

        if path == "short":
            b = np.array([0, short_arc, 0, 0])
        elif path == "long":
            b = np.array([0, long_arc, 0, 0])
        else:
            raise ValueError("\nPercorso deve essere 'short' o 'long' \n")
        
        coeff = np.linalg.solve(A, b)
        # Polinomio di terzo grado per calcolare la posizione (s)
        s = coeff[0]*t**3 + coeff[1]*t**2 + coeff[2]*t + coeff[3]

        # Derivate prima del polinomio (velocità)
        sdot = 3*coeff[0]*t**2 + 2*coeff[1]*t + coeff[2]

        pd1 = np.array([
            rho * np.cos(s / rho),
            rho * np.sin(s / rho),
            0
        ])

        pd1dot = np.array([
            -np.sin(s / rho) * sdot,
             np.cos(s / rho) * sdot,
             0
        ])

        x1 = (pi - C) / rho
        z1_vect = np.cross(x1, (pf - C) / rho)
        z1 = z1_vect / np.linalg.norm(z1_vect)
        if path == "long":
            z1 = -z1
        y1 = np.cross(z1, x1)
        R = np.column_stack([x1, y1, z1])
        
        pd = C + np.matmul(R, pd1)
        pdot = np.matmul(R, pd1dot)
    return pd, pdot

# FUNZIONE PER CALCOLARSI I LIMITI DELLO SPAZIO DI LAVORO

def calculate_workspace_limits(workspace_points):
        x_min, x_max = float('inf'), -float('inf')
        y_min, y_max = float('inf'), -float('inf')
        z_min, z_max = float('inf'), -float('inf')

        for point in workspace_points:
            x, y, z = point
            # Aggiorno limiti con i valori minimi e massimi per tutti e 3 gli assi
            x_min = min(x_min, x)
            x_max = max(x_max, x)
            y_min = min(y_min, y)
            y_max = max(y_max, y)
            z_min = min(z_min, z)
            z_max = max(z_max, z)

        return (x_min, x_max), (y_min, y_max), (z_min, z_max)

# FUNZIONE PER VEDERE SE UN PUNTO APPARTIENE ALLO SPAZIO DI LAVORO

def is_point_in_workspace(point, workspace_limits):
    # Definire i limiti dello spazio di lavoro del robot
    x_min, x_max = workspace_limits[0]  
    y_min, y_max = workspace_limits[1] 
    z_min, z_max = workspace_limits[2]  
    if (x_min <= point[0] <= x_max) and (y_min <= point[1] <= y_max) and (z_min <= point[2] <= z_max):
        return True
    else:
        return False 

# FUNZIONE PER IL CALCOLO DELLA CINEMATICA INVERSA

def inv_kin(q, xd, xdot, k, method, ka, dw_dq_func, q_mean, q_max, q_min):
    # Calcoliamo lo Jacobiano J nella configurazione corrente q
    J = Jacobian(q)

    # Costruiamo le matrici DH per ciascun giunto e otteniamo Tb1–Tb4
    T01 = DH(d[0], a[0], alpha[0], q[0])
    T12 = DH(d[1], a[1], alpha[1], q[1])
    T23 = DH(d[2], a[2], alpha[2], q[2])
    T34 = DH(d[3], a[3], alpha[3], q[3])

    Tb1 = np.matmul(Tb0, T01)
    Tb2 = np.matmul(Tb1, T12)
    Tb3 = np.matmul(Tb2, T23)
    Tb4 = np.matmul(Tb3, T34)

    # Estraiamo la posizione attuale dell’end-effector
    p_ee = Tb4[:3, 3]

    # Calcoliamo l’errore di posizione e la sua norma
    e = xd - p_ee
    err = np.linalg.norm(e)

    # Termine di correzione per la velocità articolare
    K = k * np.eye(3)
    correction = xdot + np.matmul(K, e)

    # Inizializziamo Qdot e il contatore di iterazioni
    Qdot = np.zeros_like(q)

    if method == 'inverse':
        # Soluzione classica con pseudoinversa di J
        Qdot = np.matmul(np.linalg.pinv(J), correction)

    elif method == 'transpose':
        Qdot = np.matmul(J.T, correction)

    elif method == 'redundant':
        # Proiezione nello spazio nullo
        P = np.eye(4) - np.matmul(np.linalg.pinv(J), J)
        # Calcolo del gradiente dw/dq
        dw_dq_val = dw_dq_func(*np.concatenate([q, q_mean, q_max, q_min]))
        # Velocità articolare considerando la ridondanza
        Qdot = (np.matmul(np.linalg.pinv(J), correction) + ka * np.matmul(P, dw_dq_val))

    return Qdot, err

#-----------------------------------------
# INIZIO DEL MAIN
#-----------------------------------------

if __name__ == '__main__':

    q0 = np.array([0.0, 0.0, 0.0, 0.0])

    # Calcolo matrice di trasformazione tra base e end-effector
    T01 = DH(d[0], a[0], alpha[0], q0[0])
    T12 = DH(d[1], a[1], alpha[1], q0[1])
    T23 = DH(d[2], a[2], alpha[2], q0[2])
    T34 = DH(d[3], a[3], alpha[3], q0[3])
    Tb1 = np.matmul(Tb0,T01)
    Tb2 = np.matmul(Tb1,T12)
    Tb3 = np.matmul(Tb2,T23)
    Tb4 = np.matmul(Tb3,T34)

    # Estraggo gli assi e le posizioni delle varie terne
    x0_i = Tb0[:3,0]
    y0_i = Tb0[:3,1]
    z0_i = Tb0[:3,2]
    p0 = Tb0[:3,3]

    x1_i = Tb1[:3,0]
    y1_i = Tb1[:3,1]
    z1_i = Tb1[:3,2]
    p1 = Tb1[:3,3]

    x2_i = Tb2[:3,0]
    y2_i = Tb2[:3,1]
    z2_i = Tb2[:3,2]
    p2 = Tb2[:3,3]

    x3_i = Tb3[:3,0]
    y3_i = Tb3[:3,1]
    z3_i = Tb3[:3,2]
    p3 = Tb3[:3,3]

    pee = Tb4[:3,3]

    print(' MATRICE DI TRASFORMAZIONE Tb4  \n',Tb4)
    print('\npee = ',pee)

    #----------------------------------------------------
    # PLOT DEL MANIPOLATORE NELLA CONFIGURAZIONE INIZIALE
    #----------------------------------------------------
        
    fig = plt.figure(figsize=(14,8))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_title('Manipulator at start configuration', fontsize=16)

    # Disegno i link
    ax.plot3D([p0[0],p1[0]], [p0[1],p1[1]], [p0[2],p1[2]], lw=3, color='orange')
    ax.plot3D([p1[0],p2[0]], [p1[1],p2[1]], [p1[2],p2[2]], lw=3, color='orange')
    ax.plot3D([p2[0],p3[0]], [p2[1],p3[1]], [p2[2],p3[2]], lw=3, color='orange')
    ax.plot3D([p3[0],p3[0]], [p3[1],p3[1]], [p3[2],p3[2]+d4], lw=3, color='orange')
    ax.plot3D([p3[0],pee[0]], [p3[1],pee[1]], [p3[2]+d4,pee[2]], lw=3, color='orange')

    # Disegno i giunti e gli assi
    for p, x_i, y_i, z_i in zip([p0, p1, p2, p3], [x0_i, x1_i, x2_i, x3_i], [y0_i, y1_i, y2_i, y3_i], [z0_i, z1_i, z2_i, z3_i]):
        ax.quiver(p[0], p[1], p[2], x_i[0]/30, x_i[1]/30, x_i[2]/30, color='k', label='X-axis')
        ax.quiver(p[0], p[1], p[2], y_i[0]/30, y_i[1]/30, y_i[2]/30, color='g', label='Y-axis')
        ax.quiver(p[0], p[1], p[2], z_i[0]/30, z_i[1]/30, z_i[2]/30, color='r', label='Z-axis')
    
    ax.plot3D(p0[0], p0[1], p0[2], '.', ms=12, c='blue')
    ax.plot3D(p1[0], p1[1], p1[2], '.', ms=12, c='blue')
    ax.plot3D(p2[0], p2[1], p2[2], '.', ms=12, c='blue')
    ax.plot3D(p3[0], p3[1], p3[2]+d4, '.', ms=12, c='blue')

    # Disegno end-effector
    ax.plot3D(pee[0], pee[1], pee[2], 'o', ms=12, color='purple', label='End Effector')

    # Definizione degli elementi della legenda
    legend_elements = [
        Line2D([0], [0], color='orange', lw=2, label='Links'),
        Line2D([0], [0], marker = '.', ms=12, linestyle='None', color='blue', label='joints'),
        Line2D([0], [0], color='k', lw=2, label='X-axis'),
        Line2D([0], [0], color='g', lw=2, label='Y-axis'),
        Line2D([0], [0], color='r', lw=2, label='Z-axis'),
        Line2D([0], [0], marker = 'o', ms=12, linestyle='None', color='purple', label='end-effector')]

    ax.legend(handles=legend_elements, loc='best', fontsize=15, bbox_to_anchor=(1, 0.15, 0.45, 0.5))

    ax.set_xlim([-0.1, 0.2])
    ax.set_ylim([-0.1, 0.2])
    ax.set_zlim([-0.1, 0.1])

    ax.set_xticks(np.arange(-0.1,0.35,0.1))
    ax.set_yticks(np.arange(-0.1, 0.25, 0.1))
    ax.set_zticks(np.arange(-0.1,0.15,0.1))

    ax.set_xlabel('X [m]', fontsize=12, labelpad=10)
    ax.set_ylabel('Y [m]', fontsize=12, labelpad=10)
    ax.set_zlabel('Z [m]', fontsize=12, labelpad=10)

    ax.set_aspect('equal')
    ax.view_init(30, 110) 
    ax.invert_xaxis()  
    ax.invert_yaxis()
    plt.tight_layout()
    #plt.savefig('manipulator_start.jpg', dpi=300)
    plt.show()

    #-------------------------------------------------------
    # PIANIFICAZIONE DELLE TRAIETORIE NELLO SPAZIO OPERATIVO
    #-------------------------------------------------------

    # Scelgo punti per la pianificazione di traiettoria
    _, _, _, pA, *_ = dir_kin(q0)
    pB = np.array([0.1, 0.15, 0.13])
    pC = np.array([-0.2, 0.05, 0.1])
    print('\nVALORI PUNTI DELLA TRAIETTORIA \n')
    print('Punto A ha coordinate : ', pA)
    print('Punto B ha coordinate : ', pB)
    print('Punto C ha coordinate : ', pC)

    # Trovo limiti del mio workspace
    workspace_limits = calculate_workspace_limits(reachable_points)
    print("\nLIMITI DELLO SPAZIO DI LAVORO \n")
    print("X:", workspace_limits[0])
    print("Y:", workspace_limits[1])
    print("Z:", workspace_limits[2])

    # controllo se i punti appartengono al mio workspace
    if is_point_in_workspace(pA, workspace_limits) and is_point_in_workspace(pB, workspace_limits) and is_point_in_workspace(pC, workspace_limits) : 
        print('\nTutti i punti selezionati appartengono allo spazio di lavoro \n')
    else:
        print('\nAlmeno uno dei punti selezionati NON appartiene allo spazio di lavoro \n')

    print("VALORE DEI CENTRI DELLE DUE TRAIETTORIE \n")
    C1 = center(pA, pB, 0.1)
    C2 = center(pB, pC, 0.3)
    print('Punto C1 ha coordinate : ', C1)
    print('Punto C2 ha coordinate : ', C2)

    # Pianificazione delle traiettorie
    tA = 0
    tB = 10
    tC = 20
    path_1 = "short" 
    path_2 = "short"  
    t_values_1 = np.arange(tA, tB + 0.05, 0.05)
    t_values_2 = np.arange(tB, tC + 0.05, 0.05)

    # Preparo i dati per la visualizzazione
    trajectory_1 = np.zeros((len(t_values_1), 3))
    trajectory_2 = np.zeros((len(t_values_2), 3))
    speed_1 = np.zeros((len(t_values_1), 3))
    speed_2 = np.zeros((len(t_values_2), 3))

    for i, t in enumerate(t_values_1):
        pd, pdot = CircumferencePlanner(C1, pA, pB, tA, tB, t, path_1)
        trajectory_1[i, :] = pd
        speed_1[i, :] = pdot

    for i, t in enumerate(t_values_2):
        pd, pdot = CircumferencePlanner(C2, pB, pC, tB, tC, t, path_2)
        trajectory_2[i, :] = pd
        speed_2[i, :] = pdot

    # Concatenazione
    t_total = np.concatenate((t_values_1, t_values_2))
    trajectory_total = np.vstack((trajectory_1, trajectory_2))
    speed_total = np.vstack((speed_1, speed_2))

    #-------------------------------------------------------
    # PLOT DELLE TRAIETTORIE
    #-------------------------------------------------------

    fig = plt.figure(figsize=(14, 6)) 
    gs = gridspec.GridSpec(nrows=2, ncols=2, width_ratios=[1.2, 1], height_ratios=[1, 1])
    
    # Traiettoria
    ax0 = fig.add_subplot(gs[:, 0], projection='3d')
    ax0.plot(trajectory_total[:, 0], trajectory_total[:, 1], trajectory_total[:, 2], label="Trajectory")

    ax0.plot([pA[0]], [pA[1]], [pA[2]], marker='.', linestyle='None', color='r', markersize=14, label='pA')
    ax0.plot([pB[0]], [pB[1]], [pB[2]], marker='.', linestyle='None', color='g', markersize=14, label='pB')
    ax0.plot([pC[0]], [pC[1]], [pC[2]], marker='.', linestyle='None', color='b', markersize=14, label='pC')

    ax0.set_title("Desired trajectory 3D")
    ax0.set_xlabel('X [m]')
    ax0.set_ylabel('Y [m]')
    ax0.set_zlabel('Z [m]')
    ax0.view_init(elev=40, azim=50)
    ax0.legend()

    # Posizione
    ax1 = fig.add_subplot(gs[0, 1])
    ax1.plot(t_total, trajectory_total[:, 0], label="p_dx")
    ax1.plot(t_total, trajectory_total[:, 1], label="p_dy")
    ax1.plot(t_total, trajectory_total[:, 2], label="p_dz")
    ax1.set_ylabel("Position [m]")
    ax1.set_title("Desired position over time")
    ax1.legend(loc='best')

    # Velocità
    ax2 = fig.add_subplot(gs[1, 1])
    ax2.plot(t_total, speed_total[:, 0], label="v_dx")
    ax2.plot(t_total, speed_total[:, 1], label="v_dy")
    ax2.plot(t_total, speed_total[:, 2], label="v_dz")
    ax2.set_ylabel("Velocity [m/s]")
    ax2.set_title("Desired velocity over time")
    ax2.legend(loc='best')

    plt.tight_layout()
    #plt.savefig('desired_trajectory.jpg', dpi=300)
    plt.show()

    #-----------------------------------------------------------------------------
    # PLOT DELLE TRAIETTORIE INSIEME AL WORKSPACE PER UNA MIGLIORE VISUALIZZAZIONE
    #-----------------------------------------------------------------------------

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')

    # Plot workspace
    ax.scatter(reachable_points[:, 0], reachable_points[:, 1], reachable_points[:, 2],
            color='lightgray', s=1, label='Workspace')

    # Plot della traiettoria
    ax.plot(trajectory_total[:, 0], trajectory_total[:, 1], trajectory_total[:, 2],
            color='blue', linewidth=2, label='Planned trajectory')

    ax.scatter(*pA, color='red', s=50, label='Initial point (pA)')
    ax.scatter(*pB, color='green', s=50, label='Middle point (pB)')
    ax.scatter(*pC, color='black', s=50, label='Final point (pC)')

    ax.text(*pA, "pA", fontsize=10, color='red')
    ax.text(*pB, "pB", fontsize=10, color='green')
    ax.text(*pC, "pC", fontsize=10, color='black')

    ax.set_title("Trajectory within the workspace")
    ax.set_xlabel("X [m]")
    ax.set_ylabel("Y [m]")
    ax.set_zlabel("Z [m]")
    ax.view_init(elev=40, azim=40)
    ax.legend()

    plt.tight_layout()
    #plt.savefig('trajectory_with_workspace.jpg', dpi=300)
    plt.show()

    #-------------------------------------------------------
    # INVERSIONE CINEMATICA
    #-------------------------------------------------------

    q0 = np.array([0, 0, 0, 0], dtype = float)
    n_samples = 100

    # Definisco range dei giunti per calcolare minimo, massimo e valore centrale
    q1_range = np.linspace(0, 175*np.pi/180, n_samples) # da 0 a 175
    q2_range = np.linspace(-14*np.pi/180, 106*np.pi/180, n_samples) # da -14 a 106
    q3_range = np.linspace(-2*np.pi/3, 7*np.pi/10, n_samples) # da -120 a 126
    q4_range = np.linspace(0, 2*np.pi, n_samples) # da 0 a 360
    q_min = np.array([np.min(q1_range), np.min(q2_range), np.min(q3_range), np.min(q4_range)])
    q_max = np.array([np.max(q1_range), np.max(q2_range), np.max(q3_range), np.max(q4_range)])
    q_mean = (q_min + q_max) / 2

    # Parametri (k e ka sono la migliore coppia di guadagni, risultati osservati in un file jupyter a parte)
    k = 1              # Guadagno proporzionale per tracking
    ka = 100             # Guadagno per il termine di ottimizzazione ridondante
    methods = ['inverse', 'redundant']   # Metodi di inversione cinematica
    delta_t = 0.05     # Passo temporale
    t_f = 10           # Tempo finale per ogni arco 

    # Generazione dei vettori tempo
    times = np.arange(0, t_f + delta_t, delta_t)
    total_time = np.concatenate([times, times + t_f])

    # Dizionario per salvare i risultati
    results = {}

    # Ciclo sui metodi ('inverse' e 'redundant')
    for method in methods:
        
        current_q = q0.copy()      # variabili di giunto iniziali
        ee_trajectory = []         # Posizioni end-effector effettive
        desired_trajectory = []    # Posizioni end-effector desiderate
        tracking_error = []        # Errori di tracking (norma dell’errore)
        joint_trajectory = []      # Sequenza delle configurazioni articolari

        # Primo tratto: da pA a pB
        for t in times:
            # Genera posizione e velocità desiderata su circonferenza
            pd, pdot = CircumferencePlanner(C1, pA, pB, 0, t_f, t, path_1)

            # Calcola Qdot con il metodo scelto
            Qdot, _ = inv_kin(current_q, pd, pdot, k, method, ka, dw_dq_func, q_mean, q_max, q_min)

            # Aggiorna configurazione articolare
            current_q += Qdot * delta_t
            joint_trajectory.append(current_q.copy())

            # Cinematica diretta per ottenere p_ee e calcolare errore
            _, _, _, p_ee, *_ = dir_kin(current_q)
            error = np.linalg.norm(pd - p_ee)

            # Salva traiettorie e errore
            ee_trajectory.append(p_ee)
            desired_trajectory.append(pd)
            tracking_error.append(error)

        # Secondo tratto: da pB a pC
        for t in times:
            pd, pdot = CircumferencePlanner(C2, pB, pC, 0, t_f, t, path_2)
            Qdot, _ = inv_kin(current_q, pd, pdot, k, method, ka, dw_dq_func, q_mean, q_max, q_min)
            current_q += Qdot * delta_t
            joint_trajectory.append(current_q.copy())

            _, _, _, p_ee, *_ = dir_kin(current_q)
            error = np.linalg.norm(pd - p_ee)

            ee_trajectory.append(p_ee)
            desired_trajectory.append(pd)
            tracking_error.append(error)

        # Conversione in array NumPy
        ee_trajectory = np.array(ee_trajectory)
        desired_trajectory = np.array(desired_trajectory)
        tracking_error = np.array(tracking_error)
        joint_trajectory = np.array(joint_trajectory)

        # Calcolo velocità tramite derivata discreta
        ee_velocity = np.gradient(ee_trajectory, delta_t, axis=0)
        desired_velocity = np.gradient(desired_trajectory, delta_t, axis=0)

        # Salvataggio dei risultati per il metodo corrente
        results[method] = {
            'ee_trajectory': ee_trajectory,
            'desired_trajectory': desired_trajectory,
            'tracking_error': tracking_error,
            'ee_velocity': ee_velocity,
            'desired_velocity': desired_velocity,
            'joint_trajectory': joint_trajectory
        }

    # Print statistiche a seconda del metodo utilizzato
    print(f"\nANALISI DELL'ERRORE DI TRACKING ({method})\n")
    print(f"Errore minimo      : {np.min(tracking_error):.6f} m")
    print(f"errore massimo     : {np.max(tracking_error):.6f} m")
    print(f"errore medio       : {np.mean(tracking_error):.6f} m")

    diff = np.linalg.norm(results['inverse']['ee_trajectory'] - results['redundant']['ee_trajectory'], axis=1)

    print("\nDIFFERENZE TRA 'inverse' E 'redundant'\n")
    print("Differenza media   :", np.mean(diff))
    print("Differenza massima  :", np.max(diff))

    #-------------------------------------------------------
    # PLOT TRAIETTORIA, ERRORE DI TRACKING, POSIZIONE E VELOCITA'
    #-------------------------------------------------------

    # PLOT TRAIETTORIA 3D
    fig = plt.figure(figsize=(12, 6))
    ax = fig.add_subplot(121, projection='3d')

    # Plot traiettoria desiderata
    ax.plot(results['inverse']['desired_trajectory'][:, 0],
            results['inverse']['desired_trajectory'][:, 1],
            results['inverse']['desired_trajectory'][:, 2],
            'g--', label='Desired')

    # Plot traiettorie EE per ogni metodo
    for method in methods:
        ax.plot(results[method]['ee_trajectory'][:, 0],
                results[method]['ee_trajectory'][:, 1],
                results[method]['ee_trajectory'][:, 2],
                label=f'EE ({method})')

    ax.scatter(*pA, color='red', s=50, label='pA')
    ax.scatter(*pB, color='blue', s=50, label='pB')
    ax.scatter(*pC, color='black', s=50, label='pC')
    ax.set_title("EE trajecory vs desired")
    ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
    ax.legend(); ax.grid(True)
    
    # PLOT ERRORE
    ax2 = fig.add_subplot(122)
    for method in methods:
        ax2.plot(total_time, results[method]['tracking_error'], label=f'Error ({method})')
    ax2.set_title("Tracking error")
    ax2.set_xlabel("Time [s]")
    ax2.set_ylabel("Error [m]")
    ax2.legend(); ax2.grid(True)
    plt.tight_layout()
    #fig.savefig('ee_vs_error.png', dpi=300)
    plt.show()

    # PLOT POSIZIONE E VELOCITA'
    fig2, axs = plt.subplots(3, 2, figsize=(14, 8))
    labels = ['X', 'Y', 'Z']

    for i in range(3):
        for method in methods:
            axs[i, 0].plot(total_time, results[method]['desired_trajectory'][:, i], 'b--' if method == methods[0] else 'r:', label='Desired' if method == methods[0] else "")
            axs[i, 0].plot(total_time, results[method]['ee_trajectory'][:, i], label=f'EE ({method})')
            axs[i, 1].plot(total_time, results[method]['desired_velocity'][:, i], 'r--' if method == methods[0] else 'r:', label='Desired' if method == methods[0] else "")
            axs[i, 1].plot(total_time, results[method]['ee_velocity'][:, i], label=f'EE ({method})')

        axs[i, 0].set_ylabel(f'{labels[i]} [m]')
        axs[i, 0].grid(True)
        axs[i, 1].grid(True)
        if i == 0:
            axs[i, 0].set_title('Tracking position')
            axs[i, 1].set_title('Tracking velocity')
        if i == 2:
            axs[i, 0].set_xlabel('Time [s]')
            axs[i, 1].set_xlabel('Time [s]')

    axs[0, 0].legend()
    axs[0, 1].legend()
    plt.tight_layout()
    #fig2.savefig('position_velocity.png', dpi=300)
    plt.show()

    #----------------------------------------------------------------------------
    # VISUALIZZAZIONE ANIMATA DEL MANIPOLATORE CHE ESEGUE LA TRAIETTORIA COMPLETA
    #----------------------------------------------------------------------------

    # Parametri di animazione
    method_to_animate = 'redundant' 
    q_trajectory = results[method_to_animate]['joint_trajectory']
    ee_des = results[method_to_animate]['desired_trajectory']
    ee_real = results[method_to_animate]['ee_trajectory']

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_title(f"Robot animation - Method: {method_to_animate}")
    ax.set_xlim([-0.1, 0.3])
    ax.set_ylim([-0.1, 0.2])
    ax.set_zlim([-0.05, 0.2])
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.grid(True)

    # Traiettoria desiderata
    ax.plot(ee_des[:, 0], ee_des[:, 1], ee_des[:, 2], 'b--', label='Desired trajectory')

    # Linee dinamiche
    robot_line, = ax.plot([], [], [], 'ko-', label='Robot')
    ee_point, = ax.plot([], [], [], 'ro', markersize=5, label='End-Effector')
    trail, = ax.plot([], [], [], 'y-', linewidth=1, label='Trail EE')

    # Inizializzazione
    def init():
        robot_line.set_data([], [])
        robot_line.set_3d_properties([])
        ee_point.set_data([], [])
        ee_point.set_3d_properties([])
        trail.set_data([], [])
        trail.set_3d_properties([])
        return robot_line, ee_point, trail

    ee_trail = []

    # Funzione di aggiornamento frame
    def update(frame):
        q = q_trajectory[frame]
        
        # Ottieni posizione giunti dal tuo forward_kinematics
        _, _, _, p_ee, g1, g2, g3, _, corner_point = dir_kin(q)

        # Lista di punti giunto + base
        base = np.array([0, 0, 0])
        joints = np.array([base, g1, g2, corner_point, g3, p_ee])

        # Aggiorna struttura robotica
        robot_line.set_data(joints[:, 0], joints[:, 1])
        robot_line.set_3d_properties(joints[:, 2])

        # End-effector point
        ee_point.set_data([p_ee[0]], [p_ee[1]])
        ee_point.set_3d_properties([p_ee[2]])

        # Trail
        ee_trail.append(p_ee)
        trail_coords = np.array(ee_trail)
        trail.set_data(trail_coords[:, 0], trail_coords[:, 1])
        trail.set_3d_properties(trail_coords[:, 2])

        return robot_line, ee_point, trail

    # Avvio animazione
    ani = animation.FuncAnimation(
        fig, update, frames=len(q_trajectory),
        init_func=init, blit=False, interval=50
    )

    ax.legend()
    plt.tight_layout()
    #writer = PillowWriter(fps=20)
    #ani.save('robot_animation.gif', writer=writer)
    plt.show()

    #----------------------------------------------------------------------------
    # PLOT PER LA VISUALIZZAZIONE DELL'AZIONE DEL FUNZIONALE
    #----------------------------------------------------------------------------

    # PLOT VARIABILI DI GIUNTO IN GRADI CON LIMITI
    
    fig, axs = plt.subplots(2, 2, figsize=(14, 8), sharex=True)
    axs = axs.flatten()
    joint_labels = ['Joint 1', 'Joint 2', 'Joint 3', 'Joint 4']

    for i in range(4):
        for method in methods:
            joint_deg = np.rad2deg(results[method]['joint_trajectory'][:, i])
            axs[i].plot(total_time, joint_deg, label=f'{method}')
        axs[i].hlines(np.rad2deg(q_min[i]), total_time[0], total_time[-1], colors='gray', linestyles='dashed', label='q_min' if i == 0 else "")
        axs[i].hlines(np.rad2deg(q_max[i]), total_time[0], total_time[-1], colors='gray', linestyles='dotted', label='q_max' if i == 0 else "")
        axs[i].set_ylabel(f'{joint_labels[i]} [degrees]')
        axs[i].grid(True)
        axs[i].set_title(f'{joint_labels[i]}')

    axs[2].set_xlabel('Time [s]')
    axs[3].set_xlabel('Time [s]')
    axs[0].legend()
    fig.suptitle('Joint Variables in Degrees with Limits ', fontsize=16)
    plt.tight_layout()
    #fig.savefig('joint_variables_limits.png', dpi=300)
    plt.show()

    # Calcolo di w(q) per ogni metodo
    for method in methods:
        q_traj = results[method]['joint_trajectory']
        w_traj = []

        for q in q_traj:
            input_vals = np.concatenate([q, q_mean, q_max, q_min])
            dw_dq_val = dw_dq_func(*input_vals)
            w_q = np.linalg.norm(dw_dq_val)
            w_traj.append(w_q)

        w_traj = np.array(w_traj)
        results[method]['w_traj'] = w_traj

    # PLOT DI W(q) E DELLA SUA DERIVATA
    fig, axs = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    for method in methods:
        w = results[method]['w_traj']
        dw_dt = np.gradient(w, delta_t)
        
        axs[0].plot(total_time, w, label=f"w(q) – {method}")
        axs[1].plot(total_time, dw_dt, label=f"dw/dt – {method}")

    axs[0].set_title("Evolution of Functional w(q)")
    axs[0].set_ylabel("w(q)")
    axs[0].legend()
    axs[0].grid(True)

    axs[1].set_title("Time Derivative of w(q)")
    axs[1].set_ylabel("dw/dt")
    axs[1].set_xlabel("Time [s]")
    axs[1].axhline(0, color='black', linestyle='--')
    axs[1].legend()
    axs[1].grid(True)

    plt.tight_layout()
    #fig.savefig('functional_wq_evolution.png', dpi=300)
    plt.show()