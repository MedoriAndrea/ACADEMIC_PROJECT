#!/usr/bin/env python3
import numpy as np
import time
from ev3dev2.motor import LargeMotor, OUTPUT_A, OUTPUT_B, SpeedPercent
from ev3dev2.motor import MediumMotor, OUTPUT_C, OUTPUT_D, SpeedPercent

# Parametri di DH
a= np.array([0.065, 0.065, 0.0, 0.03])
q0=np.array([0.0, 0.0, 0.0, 0.0]) 
d=np.array([0.0, 0.0, -0.03, 0.105])
alpha=np.array([-np.pi/2, np.pi/2, -np.pi/2, 0.0]) 

# Definizione delle funzioni da usare

# Funzione numerica del gradiente fine-corsa
def dw_dq(q, q_mean, q_max, q_min):
    q1, q2, q3, q4       = q
    qm1, qm2, qm3, qm4   = q_mean
    QM1, QM2, QM3, QM4   = q_max
    q_m1, q_m2, q_m3, q_m4 = q_min
    return np.array([
        -(((q1 - qm1)/(QM1 - q_m1))) / 4.0,
        -(((q2 - qm2)/(QM2 - q_m2))) / 4.0,
        -(((q3 - qm3)/(QM3 - q_m3))) / 4.0,
        -(((q4 - qm4)/(QM4 - q_m4))) / 4.0,
    ])


# Matrice di trasformazione omogenea 
def DH(d, a, alpha, theta):
    T = np.array([
        [np.cos(theta), -np.sin(theta)*np.cos(alpha), np.sin(theta)*np.sin(alpha), a*np.cos(theta)],
        [np.sin(theta), np.cos(theta)*np.cos(alpha), -np.cos(theta)*np.sin(alpha), a*np.sin(theta)],
        [0.0,           np.sin(alpha),               np.cos(alpha),               d],
        [0.0,           0.0,                         0.0,                         1.0]
    ])
    return T

Tb0 = DH(0, 0, np.pi/2, 0)

# Calcolo dello Jacobiano
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

# Algoritmi di inversione cinematica
def inv_kin(q, xd, xdot, k, method, ka, dw_dq_func, q_mean, q_max, q_min, max_iter=100, tolerance=1e-6):

    J = Jacobian(q)

    T01 = DH(d[0], a[0], alpha[0], q[0])
    T12 = DH(d[1], a[1], alpha[1], q[1])
    T23 = DH(d[2], a[2], alpha[2], q[2])
    T34 = DH(d[3], a[3], alpha[3], q[3])

    Tb1 = np.matmul(Tb0, T01)
    Tb2 = np.matmul(Tb1, T12)
    Tb3 = np.matmul(Tb2, T23)
    Tb4 = np.matmul(Tb3, T34)

    p_ee = Tb4[:3, 3]
    e = xd - p_ee
    err = np.linalg.norm(e)
    K = k * np.eye(3)
    correction = xdot + np.matmul(K, e)

    Qdot = np.zeros_like(q)

    if method == 'inverse':
        Qdot = np.matmul(np.linalg.pinv(J), correction)

    elif method == 'transpose':
        Qdot = np.matmul(J.T, correction)

    elif method == 'redundant':
        P = np.eye(4) - np.matmul(np.linalg.pinv(J), J)
        dw_dq_val = dw_dq_func(*np.concatenate([q, q_mean, q_max, q_min]))
        Qdot = (np.matmul(np.linalg.pinv(J), correction) + ka * np.matmul(P, dw_dq_val))

    return Qdot, err

# FUNZIONE PER PIANIFICRE UN ARCO DI CIRCONFERENZA NELLO SPAZIO OPERATIVO
def CircumferencePlanner(C, pi, pf, t0, tf, t, path):        
    rho = np.linalg.norm(pi - C)
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
        s = coeff[0]*t**3 + coeff[1]*t**2 + coeff[2]*t + coeff[3]
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

if __name__ == '__main__':
    m1 = LargeMotor(OUTPUT_A)
    m2 = LargeMotor(OUTPUT_B)
    m3 = MediumMotor(OUTPUT_C) 
    m4 = MediumMotor(OUTPUT_D)
    m1.polarity = 'inversed'
    m4.polarity = 'inversed'

    m1.reset()
    m2.reset()
    m3.reset()
    m4.reset()

    t0 = 0
    tA = 100
    tf = 200

    # PUNTI
    pA = np.array([0.16, 0.03, 0.105])
    pB = np.array([0.1, 0.15, 0.13])
    pC = np.array([-0.2, 0.05, 0.1 ]) 
    C1 =  np.array([0.19538348, 0.12269174, 0.1175]) 
    C2 =  np.array([-0.13048292, 0.34144875, 0.115])

    Qrobot = np.zeros((1000,4))
    Qrobot[0,:] = np.array([0.0, 0.0, 0.0, 0.0])

    # Inizializzazione SO
    T01 = DH(d[0], a[0], alpha[0], q0[0])
    T12 = DH(d[1], a[1], alpha[1], q0[1])
    T23 = DH(d[2], a[2], alpha[2], q0[2])
    T34 = DH(d[3], a[3], alpha[3], q0[3])
    TB1 = np.matmul(Tb0, T01)
    TB2 = np.matmul(TB1, T12)
    TB3 = np.matmul(TB2, T23)
    TB4 = np.matmul(TB3, T34)

    # Inizializzazione SG
    Qd = np.zeros((1000,4))
    Qdot = np.zeros((1000,4))
    Qd[0,:] = q0
    pee = TB4[:3,3]

    # Inizializzazione SO
    Pd = np.zeros((1000,3))
    Pddot = np.zeros((1000,3))
    Pd[0,:] = pee

    errore = np.zeros((1000, 3))
    errore[0] = np.array([0,0,0])
    norma_errore = np.zeros((1000, 1))
    norma_errore[0] = 0

    n_samples = 100
    q1_range = np.linspace(0, 175*np.pi/180, n_samples) # da 0 a 175
    q2_range = np.linspace(-14*np.pi/180, 106*np.pi/180, n_samples) # da -14 a 106
    q3_range = np.linspace(-2*np.pi/3, 7*np.pi/10, n_samples) # da -120 a 126
    q4_range = np.linspace(0, 2*np.pi, n_samples) # da 0 a 360
    q_min = np.array([np.min(q1_range), np.min(q2_range), np.min(q3_range), np.min(q4_range)])
    q_max = np.array([np.max(q1_range), np.max(q2_range), np.max(q3_range), np.max(q4_range)])
    q_mean = (q_min + q_max) / 2

    kgain = 1 # guadagno che esce da ottimizzazione
    ka = 100

    tempo_corrente= 0
    t_iniziale = time.time() 
    tempo_prec = time.time()
    counter = 1 # inizializzo il timer

    while(tempo_corrente<tf):
        istante = time.time()
        tempo_corrente = istante - t_iniziale
        dt = tempo_corrente - tempo_prec 
        tempo_prec = istante

        if tempo_corrente<=tA: 
            Pd[counter, :], Pddot[counter,:] = CircumferencePlanner(C1, pA, pB, t0, tA, tempo_corrente, 'short')
        
        else:
            Pd[counter,:], Pddot[counter,:]= CircumferencePlanner(C2, pB, pC, tA, tf, tempo_corrente, 'short') 

        # Leggo le Q reali a cui è arrivato il robot e le uso nell'inversione cinematica
        Qr1 = (np.pi/180)*m1.position
        Qr2 = (np.pi/180)*m2.position
        Qr3 = (np.pi/180)*m3.position
        Qr4 = (np.pi/180)*m4.position

        Qrobot[counter,:] = np.array([Qr1, Qr2, Qr3, Qr4])

        Qdot[counter, :], _ = inv_kin(Qrobot[counter,:],  Pd[counter,:], Pddot[counter,:], kgain, "redundant", ka, dw_dq, q_mean, q_max, q_min)
       
        Qd[counter+1,:] = Qd[counter,:] + dt*Qdot[counter, :]

        q1 = Qd[counter, 0]
        q2 = Qd[counter, 1]
        q3 = Qd[counter, 2]
        q4 = Qd[counter, 3]

        m1.on_to_position(SpeedPercent(10), np.round(Qd[counter, 0]*(180/np.pi)), brake=True, block=True) # trasformo in gradi  
        m2.on_to_position(SpeedPercent(10), np.round(Qd[counter, 1]*(180/np.pi)), brake=True, block=True) # break si ferma quando arrivato
        m3.on_to_position(SpeedPercent(10), np.round(Qd[counter, 2]*(180/np.pi)), brake=True, block=True) # block aspetta per eseguire la riga successiva
        m4.on_to_position(SpeedPercent(10), np.round(Qd[counter, 3]*(180/np.pi)), brake=True, block=True)

        # Salvataggio in file di testo
        with open("file_dati.txt", 'a') as file:
            file.write(str(istante) + ";" + str(q1) + ";" + str((m1.position)* (np.pi/180)) +";" +  str(q2) + ";" + str((m2.position)* (np.pi/180)) + ";" +  str(q3) + ";" + str((m3.position)* (np.pi/180)) +  ";" + str(q4) + ";" + str((m4.position)* (np.pi/180)) + '\n')

        counter = counter + 1