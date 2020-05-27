import numpy as np
import copy
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QVariant, QThread
from scipy.optimize import least_squares, leastsq, minimize, differential_evolution
import plotly
import plotly.graph_objs as go
import random, os
from functools import partial
from scipy import special
import mpmath
mpmath.mp.dps = 16

np.random.seed(211)
random.seed(211)

def diffcylim(w, R_d, Cd):
    """ diffcylim R_d Cd """
    ret_sqrt = np.sqrt(R_d * np.multiply(1j*w, Cd))

    ret_mp = [R_d * mpmath.besseli(0, x) /  (x * mpmath.besseli(1, x)) for x in ret_sqrt]
    
    z_ret = np.array(ret_mp, dtype=np.complex128)
    return z_ret

def Barsoukov_Pham_Lee_1(parvals, f):
    """
    Barsoukov-Pham-Lee #1D
    Cathode: DX30 modified with corrected Cd, Ci
    Liquid electrolyte instead of R_ohm, use DX15
    """

    omegas = 2 * np.pi * np.array(f)
    
    #Cathode
    R_m = parvals['r_m']
    R_ct = parvals['r_ct']
    R_d = parvals['r_d']

    R_i = parvals["r_i"]
    C_dl = parvals["c_dl"]
    C_d = parvals["c_d"]

    C_i = parvals["c_i"]
    Q_W = parvals["q_w"]

    Cdl_C0 = C_dl
    Cdl_HNC = 1e-20
    Cdl_HNT = 1e-20
    Cdl_HNP = 1e-20
    Cdl_HNU = 1e-20

    Cd_C0 = C_d
    Cd_HNC = C_i
    Cd_HNT = R_i*C_i
    Cd_HNP = 1
    Cd_HNU = 1
    CPE_B_T = Q_W
    CPE_B_P = 0.5

    Cstar_d = Cd_C0 + Cd_HNC / ((1 + (1j * omegas * Cd_HNT) ** Cd_HNU) ** Cd_HNP)
    Cstar_dl = Cdl_C0 + Cdl_HNC / ((1 + (1j * omegas * Cdl_HNT) ** Cdl_HNU) ** Cdl_HNP)
    Cstar_B = CPE_B_T * ((1j * omegas) ** (CPE_B_P - 1))

    Zd_numerator = np.sqrt(R_d / (1j*np.multiply(omegas, Cstar_d)))
    Zd_denominator = np.tanh(np.sqrt(R_d*1j * np.multiply(omegas, Cstar_d)))

    Zd = np.divide(Zd_numerator, Zd_denominator)

    Zs = R_m
    Y_P = (1j * omegas * Cstar_dl) + 1.0 / (R_ct + Zd)
    Z_B = 1.0 / (1j * omegas * Cstar_B)

    Z_cathode = (1 + Z_B * np.sqrt(Y_P / Zs) * (1.0 / np.tanh(np.sqrt(Zs * Y_P)))) / (
            Z_B * Y_P / Zs + np.sqrt(Y_P / Zs) * (1.0 / np.tanh(np.sqrt(Zs * Y_P))))
            
            
    #Liquid electrolyte
    DX15_R1 = parvals['r_c_liq']
    DX15_C1 = 1e-20
    DX15_R2 = parvals['r_a_liq']

    DX15_C2 = 1e-20
    DX15_R3 = 1e20
    DX15_C3 = parvals['c_d_liq']
    DX15_RA = parvals['r_+||']
    DX15_CA = 1e-20
    DX15_RB = parvals['r_-||']
    DX15_CB = 1e-20

    DX15_Z1 = np.divide(DX15_R1, 1 + 1j*omegas*DX15_R1*DX15_C1)
    DX15_Z2 = np.divide(DX15_R2, 1 + 1j*omegas*DX15_R2*DX15_C2)
    DX15_Z3 = np.divide(DX15_R3, 1 + 1j*omegas*DX15_R3*DX15_C3)
    DX15_ZA = np.divide(DX15_RA, 1 + 1j*omegas*DX15_RA*DX15_CA)
    DX15_ZB = np.divide(DX15_RB, 1 + 1j*omegas*DX15_RB*DX15_CB)

    Z_DX15_p1 = np.divide(np.multiply(DX15_Z1, DX15_Z2), DX15_Z1 + DX15_Z2)
    Z_DX15_p2 = np.divide(2.0, DX15_Z1 + DX15_Z2)
    DX15_k = np.sqrt(np.divide(DX15_Z1 + DX15_Z2, DX15_Z3))
    Z_DX15_p3 = DX15_k*DX15_ZA*DX15_ZB*(DX15_Z1 + DX15_Z2) + ((DX15_Z2**2) *DX15_ZA + (DX15_Z1**2) * DX15_ZB)*np.tanh(DX15_k/2)
    Z_DX15_p4 = DX15_k*(DX15_ZA + DX15_ZB) + (DX15_Z1 + DX15_Z2)*np.tanh(DX15_k/2)
    
    Z_DX15 = Z_DX15_p1 + np.divide(Z_DX15_p2 * Z_DX15_p3, Z_DX15_p4)
    
    Z = Z_cathode + Z_DX15
    return Z
    
def Barsoukov_Pham_Lee_2(parvals, f):
    """ 
    Barsoukov-Pham-Lee #2D
    """
    #co factor 2trong Cd, 2 trong Ci
    omegas = 2 * np.pi * np.array(f)

    R_m = parvals['r_m']
    R_ct = parvals['r_ct']
    R_d = parvals['r_d']

    R_i = parvals["r_i"]
    C_dl = parvals["c_dl"]
    C_d = parvals["c_d"]

    C_i = parvals["c_i"]
    Q_W = parvals["q_w"]

    Cdl_C0 = C_dl
    Cdl_HNC = 1e-20
    Cdl_HNT = 1e-20
    Cdl_HNP = 1e-20
    Cdl_HNU = 1e-20

    Cd_C0 = C_d
    Cd_HNC = C_i
    Cd_HNT = R_i*C_i
    Cd_HNP = 1
    Cd_HNU = 1
    CPE_B_T = Q_W
    CPE_B_P = 0.5

    Cstar_d = Cd_C0 + (2*(Cd_HNC + Cd_C0)- Cd_C0)/ ((1 + (1j * omegas * Cd_HNT) ** Cd_HNU) ** Cd_HNP)
    Cstar_dl = Cdl_C0 + Cdl_HNC / ((1 + (1j * omegas * Cdl_HNT) ** Cdl_HNU) ** Cdl_HNP)
    Cstar_B = CPE_B_T * ((1j * omegas) ** (CPE_B_P - 1))

    Zd = diffcylim(omegas, R_d, Cstar_d)

    Zs = R_m
    Y_P = (1j * omegas * Cstar_dl) + 1.0 / (R_ct + Zd)
    Z_B = 1.0 / (1j * omegas * Cstar_B)

    Z_cathode = (1 + Z_B * np.sqrt(Y_P / Zs) * (1.0 / np.tanh(np.sqrt(Zs * Y_P)))) / (
            Z_B * Y_P / Zs + np.sqrt(Y_P / Zs) * (1.0 / np.tanh(np.sqrt(Zs * Y_P))))
            
    #Liquid electrolyte
    DX15_R1 = parvals['r_c_liq']
    DX15_C1 = 1e-20
    DX15_R2 = parvals['r_a_liq']

    DX15_C2 = 1e-20
    DX15_R3 = 1e20
    DX15_C3 = parvals['c_d_liq']
    DX15_RA = parvals['r_+||']
    DX15_CA = 1e-20
    DX15_RB = parvals['r_-||']
    DX15_CB = 1e-20

    DX15_Z1 = np.divide(DX15_R1, 1 + 1j*omegas*DX15_R1*DX15_C1)
    DX15_Z2 = np.divide(DX15_R2, 1 + 1j*omegas*DX15_R2*DX15_C2)
    DX15_Z3 = np.divide(DX15_R3, 1 + 1j*omegas*DX15_R3*DX15_C3)
    DX15_ZA = np.divide(DX15_RA, 1 + 1j*omegas*DX15_RA*DX15_CA)
    DX15_ZB = np.divide(DX15_RB, 1 + 1j*omegas*DX15_RB*DX15_CB)

    Z_DX15_p1 = np.divide(np.multiply(DX15_Z1, DX15_Z2), DX15_Z1 + DX15_Z2)
    Z_DX15_p2 = np.divide(2.0, DX15_Z1 + DX15_Z2)
    DX15_k = np.sqrt(np.divide(DX15_Z1 + DX15_Z2, DX15_Z3))
    Z_DX15_p3 = DX15_k*DX15_ZA*DX15_ZB*(DX15_Z1 + DX15_Z2) + ((DX15_Z2**2) *DX15_ZA + (DX15_Z1**2) * DX15_ZB)*np.tanh(DX15_k/2)
    Z_DX15_p4 = DX15_k*(DX15_ZA + DX15_ZB) + (DX15_Z1 + DX15_Z2)*np.tanh(DX15_k/2)
    
    Z_DX15 = Z_DX15_p1 + np.divide(Z_DX15_p2 * Z_DX15_p3, Z_DX15_p4)
    
    Z = Z_cathode + Z_DX15

    return Z

def Barsoukov_Pham_Lee_3(parvals, f):
    """ 
    Barsoukov-Pham-Lee #3D
    """
    #co factor 3 trong Cd, 3 trong Ci
    omegas = 2 * np.pi * np.array(f)

    R_m = parvals['r_m']
    R_ct = parvals['r_ct']
    R_d = parvals['r_d']

    R_i = parvals["r_i"]
    C_dl = parvals["c_dl"]
    C_d = parvals["c_d"]

    C_i = parvals["c_i"]
    Q_W = parvals["q_w"]

    Cdl_C0 = C_dl
    Cdl_HNC = 1e-20
    Cdl_HNT = 1e-20
    Cdl_HNP = 1e-20
    Cdl_HNU = 1e-20

    Cd_C0 = C_d
    Cd_HNC = C_i
    Cd_HNT = R_i*C_i
    Cd_HNP = 1
    Cd_HNU = 1
    CPE_B_T = Q_W
    CPE_B_P = 0.5

    Cstar_d = Cd_C0 + (3*(Cd_HNC + Cd_C0)- Cd_C0) / ((1 + (1j * omegas * Cd_HNT) ** Cd_HNU) ** Cd_HNP)
    Cstar_dl = Cdl_C0 + Cdl_HNC / ((1 + (1j * omegas * Cdl_HNT) ** Cdl_HNU) ** Cdl_HNP)
    Cstar_B = CPE_B_T * ((1j * omegas) ** (CPE_B_P - 1))

    tanh_sqrt = np.sqrt(R_d * (1j * omegas * Cstar_d))
    tanh_values = (1+0j)*np.ones(tanh_sqrt.shape, dtype=np.complex64)
    tanh_values[np.real(tanh_sqrt) < 100] = np.tanh(tanh_sqrt[np.real(tanh_sqrt) < 100])

    Zd = tanh_values / (
           np.sqrt(1j * omegas * Cstar_d / R_d) - (1 / R_d) * tanh_values)

    Zs = R_m
    Y_P = (1j * omegas * Cstar_dl) + 1.0 / (R_ct + Zd)
    Z_B = 1.0 / (1j * omegas * Cstar_B)

    Z_cathode = (1 + Z_B * np.sqrt(Y_P / Zs) * (1.0 / np.tanh(np.sqrt(Zs * Y_P)))) / (
            Z_B * Y_P / Zs + np.sqrt(Y_P / Zs) * (1.0 / np.tanh(np.sqrt(Zs * Y_P))))

    #Liquid electrolyte
    DX15_R1 = parvals['r_c_liq']
    DX15_C1 = 1e-20
    DX15_R2 = parvals['r_a_liq']

    DX15_C2 = 1e-20
    DX15_R3 = 1e20
    DX15_C3 = parvals['c_d_liq']
    DX15_RA = parvals['r_+||']
    DX15_CA = 1e-20
    DX15_RB = parvals['r_-||']
    DX15_CB = 1e-20

    DX15_Z1 = np.divide(DX15_R1, 1 + 1j*omegas*DX15_R1*DX15_C1)
    DX15_Z2 = np.divide(DX15_R2, 1 + 1j*omegas*DX15_R2*DX15_C2)
    DX15_Z3 = np.divide(DX15_R3, 1 + 1j*omegas*DX15_R3*DX15_C3)
    DX15_ZA = np.divide(DX15_RA, 1 + 1j*omegas*DX15_RA*DX15_CA)
    DX15_ZB = np.divide(DX15_RB, 1 + 1j*omegas*DX15_RB*DX15_CB)

    Z_DX15_p1 = np.divide(np.multiply(DX15_Z1, DX15_Z2), DX15_Z1 + DX15_Z2)
    Z_DX15_p2 = np.divide(2.0, DX15_Z1 + DX15_Z2)
    DX15_k = np.sqrt(np.divide(DX15_Z1 + DX15_Z2, DX15_Z3))
    Z_DX15_p3 = DX15_k*DX15_ZA*DX15_ZB*(DX15_Z1 + DX15_Z2) + ((DX15_Z2**2) *DX15_ZA + (DX15_Z1**2) * DX15_ZB)*np.tanh(DX15_k/2)
    Z_DX15_p4 = DX15_k*(DX15_ZA + DX15_ZB) + (DX15_Z1 + DX15_Z2)*np.tanh(DX15_k/2)
    
    Z_DX15 = Z_DX15_p1 + np.divide(Z_DX15_p2 * Z_DX15_p3, Z_DX15_p4)
    
    Z = Z_cathode + Z_DX15
    return Z
   

def Barsoukov_Pham_Lee(parvals, f, T=None, Voltage=None, c_case=5):

    if c_case == 5:
        fit_zrzi = Barsoukov_Pham_Lee_1(parvals, f)
    elif c_case == 6:
        fit_zrzi = Barsoukov_Pham_Lee_2(parvals, f)
    elif c_case == 7:
        fit_zrzi = Barsoukov_Pham_Lee_3(parvals, f)
    else:
        print('Undefined')

    L_str = 1e-20
    R_str = 1e-20
    Z_L = 1j * 2 * np.pi * f * L_str

    fit_zrzi = 1 / ((1 / Z_L) + (1 / R_str)) + fit_zrzi

    return fit_zrzi

def Barsoukov_Pham_Lee_1D_Full_cell(parvals, f, T=None, Voltage=None):
    
    #Stray effect: Simple LR in parallel
    L_str = parvals['l_str']
    R_str = parvals['r_str']
    Z_LR_str = 1.0/ ((1.0/(1j * 2 * np.pi * f * L_str)) + 1.0/R_str)
    
    omegas = 2*np.pi*f
    #Cathode: DX30 with corrected Cd* equation, Cdl is ideal C while Ci is CHN
    R_m = parvals['r_m']
    R_ct = parvals['r_ct']
    R_d = parvals['r_d']
    R_i = parvals["r_i"]
    
    C0_dl = parvals["c_dl"]
    CHN_dl = 1e-20
    THN_dl = 1e-20
    P_dl = 1.0
    U_dl = 1.0
    
    C_d = parvals["c_d"]
    C_i = parvals["c_i"]
    
    ###Tau_i is tau_HN_max, tau_i = Ri * Ci   
    P_i = 1 
    U_i = 1 
    
    Cd_HNT = (R_i * C_i) / (np.power(np.sin((np.pi*U_i*P_i)/(2*(P_i+1))) / np.sin((np.pi*U_i) / (2*(P_i+1))), 1/U_i))
        
    CPE_B_P = 0.5
    Q_w = parvals["q_w"]
    CPE_B_T = Q_w
    
    Cstar_d = C_d + (1*(C_i + C_d)- C_d) / ((1 + (1j * omegas * Cd_HNT) ** U_i) ** P_i)
    Cstar_dl = C0_dl + CHN_dl / ((1 + (1j * omegas * THN_dl) ** U_dl) ** P_dl)
    Cstar_B = CPE_B_T * ((1j * omegas) ** (CPE_B_P - 1))

    Zd_numerator = np.sqrt(R_d / (1j*np.multiply(omegas, Cstar_d)))
    Zd_denominator = np.tanh(np.sqrt(R_d*1j * np.multiply(omegas, Cstar_d)))

    Zd = np.divide(Zd_numerator, Zd_denominator)

    Zs = R_m
    Y_P = (1j * omegas * Cstar_dl) + 1.0 / (R_ct + Zd)
    Z_B = 1.0 / (1j * omegas * Cstar_B)

    Z_cathode = (1 + Z_B * np.sqrt(Y_P / Zs) * (1.0 / np.tanh(np.sqrt(Zs * Y_P)))) / (
            Z_B * Y_P / Zs + np.sqrt(Y_P / Zs) * (1.0 / np.tanh(np.sqrt(Zs * Y_P))))
    
    
    #Separator with liquid electrolyte: DX15 with 2 rails, ideal C
    DX15_R1 = parvals['r_c_liq']
    DX15_C1 = 1e-20
    DX15_R2 = parvals['r_a_liq']

    DX15_C2 = 1e-20
    DX15_R3 = 1e20
    DX15_C3 = parvals['c_d_liq']
    DX15_RA = parvals['r_+||']   # R_+||
    DX15_CA = 1e-20
    DX15_RB = parvals['r_-||']    # R_-||
    DX15_CB = 1e-20

    DX15_Z1 = np.divide(DX15_R1, 1 + 1j*omegas*DX15_R1*DX15_C1)
    DX15_Z2 = np.divide(DX15_R2, 1 + 1j*omegas*DX15_R2*DX15_C2)
    DX15_Z3 = np.divide(DX15_R3, 1 + 1j*omegas*DX15_R3*DX15_C3)
    DX15_ZA = np.divide(DX15_RA, 1 + 1j*omegas*DX15_RA*DX15_CA)
    DX15_ZB = np.divide(DX15_RB, 1 + 1j*omegas*DX15_RB*DX15_CB)

    Z_DX15_p1 = np.divide(np.multiply(DX15_Z1, DX15_Z2), DX15_Z1 + DX15_Z2)
    Z_DX15_p2 = np.divide(2.0, DX15_Z1 + DX15_Z2)
    DX15_k = np.sqrt(np.divide(DX15_Z1 + DX15_Z2, DX15_Z3))
    Z_DX15_p3 = DX15_k*DX15_ZA*DX15_ZB*(DX15_Z1 + DX15_Z2) + ((DX15_Z2**2) *DX15_ZA + (DX15_Z1**2) * DX15_ZB)*np.tanh(DX15_k/2)
    Z_DX15_p4 = DX15_k*(DX15_ZA + DX15_ZB) + (DX15_Z1 + DX15_Z2)*np.tanh(DX15_k/2)
    
    Z_DX15 = Z_DX15_p1 + np.divide(Z_DX15_p2 * Z_DX15_p3, Z_DX15_p4)
    
    
    #Anode: Simple RC in parallel
    R_ct_Li = parvals['r_ct_li']
    C_dl_Li = parvals['c_dl_li']
    Z_dl_Li = 1.0/((1.0/R_ct_Li)+ (1j * 2 * np.pi * f * C_dl_Li))
    
    #Total impedance    
    Z_ret = Z_LR_str + Z_cathode + Z_DX15 + Z_dl_Li
    
    return Z_ret

def Barsoukov_Pham_Lee_2D_Full_cell(parvals, f, T=None, Voltage=None):
    
    #Stray effect: Simple LR in parallel
    L_str = parvals['l_str']
    R_str = parvals['r_str']
    Z_LR_str = 1.0/ ((1.0/(1j * 2 * np.pi * f * L_str)) + 1.0/R_str)
    
    omegas = 2*np.pi*f
    #Cathode: DX30 with corrected Cd* equation, Cdl is ideal C while Ci is CHN
    R_m = parvals['r_m']
    R_ct = parvals['r_ct']
    R_d = parvals['r_d']
    R_i = parvals["r_i"]
    
    C0_dl = parvals["c_dl"]
    CHN_dl = 1e-20
    THN_dl = 1e-20
    P_dl = 1.0
    U_dl = 1.0
    
    C_d = parvals["c_d"]
    C_i = parvals["c_i"]
    
    ###Tau_i is tau_HN_max, tau_i = Ri * Ci   
    P_i = 1 
    U_i = 1 
    
    Cd_HNT = (R_i * C_i) / (np.power(np.sin((np.pi*U_i*P_i)/(2*(P_i+1))) / np.sin((np.pi*U_i) / (2*(P_i+1))), 1/U_i))
        
    CPE_B_P = 0.5
    Q_w = parvals["q_w"]
    CPE_B_T = Q_w
    
    Cstar_d = C_d + (2*(C_i + C_d)- C_d) / ((1 + (1j * omegas * Cd_HNT) ** U_i) ** P_i)
    Cstar_dl = C0_dl + CHN_dl / ((1 + (1j * omegas * THN_dl) ** U_dl) ** P_dl)
    Cstar_B = CPE_B_T * ((1j * omegas) ** (CPE_B_P - 1))

    Zd = diffcylim(omegas, R_d, Cstar_d)

    Zs = R_m
    Y_P = (1j * omegas * Cstar_dl) + 1.0 / (R_ct + Zd)
    Z_B = 1.0 / (1j * omegas * Cstar_B)

    Z_cathode = (1 + Z_B * np.sqrt(Y_P / Zs) * (1.0 / np.tanh(np.sqrt(Zs * Y_P)))) / (
            Z_B * Y_P / Zs + np.sqrt(Y_P / Zs) * (1.0 / np.tanh(np.sqrt(Zs * Y_P))))
    
    
    #Separator with liquid electrolyte: DX15 with 2 rails, ideal C
    DX15_R1 = parvals['r_c_liq']
    DX15_C1 = 1e-20
    DX15_R2 = parvals['r_a_liq']

    DX15_C2 = 1e-20
    DX15_R3 = 1e20
    DX15_C3 = parvals['c_d_liq']
    DX15_RA = parvals['r_+||']
    DX15_CA = 1e-20
    DX15_RB = parvals['r_-||']
    DX15_CB = 1e-20

    DX15_Z1 = np.divide(DX15_R1, 1 + 1j*omegas*DX15_R1*DX15_C1)
    DX15_Z2 = np.divide(DX15_R2, 1 + 1j*omegas*DX15_R2*DX15_C2)
    DX15_Z3 = np.divide(DX15_R3, 1 + 1j*omegas*DX15_R3*DX15_C3)
    DX15_ZA = np.divide(DX15_RA, 1 + 1j*omegas*DX15_RA*DX15_CA)
    DX15_ZB = np.divide(DX15_RB, 1 + 1j*omegas*DX15_RB*DX15_CB)

    Z_DX15_p1 = np.divide(np.multiply(DX15_Z1, DX15_Z2), DX15_Z1 + DX15_Z2)
    Z_DX15_p2 = np.divide(2.0, DX15_Z1 + DX15_Z2)
    DX15_k = np.sqrt(np.divide(DX15_Z1 + DX15_Z2, DX15_Z3))
    Z_DX15_p3 = DX15_k*DX15_ZA*DX15_ZB*(DX15_Z1 + DX15_Z2) + ((DX15_Z2**2) *DX15_ZA + (DX15_Z1**2) * DX15_ZB)*np.tanh(DX15_k/2)
    Z_DX15_p4 = DX15_k*(DX15_ZA + DX15_ZB) + (DX15_Z1 + DX15_Z2)*np.tanh(DX15_k/2)
    
    Z_DX15 = Z_DX15_p1 + np.divide(Z_DX15_p2 * Z_DX15_p3, Z_DX15_p4)
    
    
    #Anode: Simple RC in parallel
    R_ct_Li = parvals['r_ct_li']
    C_dl_Li = parvals['c_dl_li']
    Z_dl_Li = 1.0/((1.0/R_ct_Li)+ (1j * 2 * np.pi * f * C_dl_Li))
    
    #Total impedance    
    Z_ret = Z_LR_str + Z_cathode + Z_DX15 + Z_dl_Li
    
    return Z_ret

def Barsoukov_Pham_Lee_3D_Full_cell(parvals, f, T=None, Voltage=None):
    
    #Stray effect: Simple LR in parallel
    L_str = parvals['l_str']
    R_str = parvals['r_str']
    Z_LR_str = 1.0/ ((1.0/(1j * 2 * np.pi * f * L_str)) + 1.0/R_str)
    
    omegas = 2*np.pi*f
    #Cathode: DX30 with corrected Cd* equation, Cdl is ideal C while Ci is CHN
    R_m = parvals['r_m']
    R_ct = parvals['r_ct']
    R_d = parvals['r_d']
    R_i = parvals["r_i"]
    
    C0_dl = parvals["c_dl"]
    CHN_dl = 1e-20
    THN_dl = 1e-20
    P_dl = 1.0
    U_dl = 1.0
    
    C_d = parvals["c_d"]
    C_i = parvals["c_i"]
    
    ###Tau_i is tau_HN_max, tau_i = Ri * Ci   
    P_i = 1 
    U_i = 1 
    
    Cd_HNT = (R_i * C_i) / (np.power(np.sin((np.pi*U_i*P_i)/(2*(P_i+1))) / np.sin((np.pi*U_i) / (2*(P_i+1))), 1/U_i))
        
    CPE_B_P = 0.5
    Q_w = parvals["q_w"]
    CPE_B_T = Q_w
    
    Cstar_d = C_d + (3*(C_i + C_d)- C_d) / ((1 + (1j * omegas * Cd_HNT) ** U_i) ** P_i)
    
    Cstar_dl = C0_dl + CHN_dl / ((1 + (1j * omegas * THN_dl) ** U_dl) ** P_dl)
    Cstar_B = CPE_B_T * ((1j * omegas) ** (CPE_B_P - 1))

    tanh_sqrt = np.sqrt(R_d * (1j * omegas * Cstar_d))
    tanh_values = (1+0j)*np.ones(tanh_sqrt.shape, dtype=np.complex64)
    tanh_values[np.real(tanh_sqrt) < 100] = np.tanh(tanh_sqrt[np.real(tanh_sqrt) < 100])

    Zd = tanh_values / (
           np.sqrt(1j * omegas * Cstar_d / R_d) - (1 / R_d) * tanh_values)

    Zs = R_m
    Y_P = (1j * omegas * Cstar_dl) + 1.0 / (R_ct + Zd)
    Z_B = 1.0 / (1j * omegas * Cstar_B)

    Z_cathode = (1 + Z_B * np.sqrt(Y_P / Zs) * (1.0 / np.tanh(np.sqrt(Zs * Y_P)))) / (
            Z_B * Y_P / Zs + np.sqrt(Y_P / Zs) * (1.0 / np.tanh(np.sqrt(Zs * Y_P))))
    
    
    #Separator with liquid electrolyte: DX15 with 2 rails, ideal C
    DX15_R1 = parvals['r_c_liq']
    DX15_C1 = 1e-20
    DX15_R2 = parvals['r_a_liq']

    DX15_C2 = 1e-20
    DX15_R3 = 1e20
    DX15_C3 = parvals['c_d_liq']
    DX15_RA = parvals['r_+||']
    DX15_CA = 1e-20
    DX15_RB = parvals['r_-||']
    DX15_CB = 1e-20

    DX15_Z1 = np.divide(DX15_R1, 1 + 1j*omegas*DX15_R1*DX15_C1)
    DX15_Z2 = np.divide(DX15_R2, 1 + 1j*omegas*DX15_R2*DX15_C2)
    DX15_Z3 = np.divide(DX15_R3, 1 + 1j*omegas*DX15_R3*DX15_C3)
    DX15_ZA = np.divide(DX15_RA, 1 + 1j*omegas*DX15_RA*DX15_CA)
    DX15_ZB = np.divide(DX15_RB, 1 + 1j*omegas*DX15_RB*DX15_CB)

    Z_DX15_p1 = np.divide(np.multiply(DX15_Z1, DX15_Z2), DX15_Z1 + DX15_Z2)
    Z_DX15_p2 = np.divide(2.0, DX15_Z1 + DX15_Z2)
    DX15_k = np.sqrt(np.divide(DX15_Z1 + DX15_Z2, DX15_Z3))
    Z_DX15_p3 = DX15_k*DX15_ZA*DX15_ZB*(DX15_Z1 + DX15_Z2) + ((DX15_Z2**2) *DX15_ZA + (DX15_Z1**2) * DX15_ZB)*np.tanh(DX15_k/2)
    Z_DX15_p4 = DX15_k*(DX15_ZA + DX15_ZB) + (DX15_Z1 + DX15_Z2)*np.tanh(DX15_k/2)
    
    Z_DX15 = Z_DX15_p1 + np.divide(Z_DX15_p2 * Z_DX15_p3, Z_DX15_p4)
    
    
    #Anode: Simple RC in parallel
    R_ct_Li = parvals['r_ct_li']
    C_dl_Li = parvals['c_dl_li']
    Z_dl_Li = 1.0/((1.0/R_ct_Li)+ (1j * 2 * np.pi * f * C_dl_Li))
    
    #Total impedance    
    Z_ret = Z_LR_str + Z_cathode + Z_DX15 + Z_dl_Li
    
    return Z_ret

def get_cost_vector(zcalc, zdata, weighting):
    """
    Get cost vector
    :param y_pred:
    :param ydata:
    :param weighting:
        2: data-proportional
        3: calc-proportional
        4: data-modulus
        5: calc-modulus
        otherwise: unit weighting
    :return:
    """

    # if np.count_nonzero(np.logical_or(np.isinf(zcalc), np.isnan(zcalc))):
    #     return 1e16 * np.ones(len(zcalc) * 2)

    error = zdata - zcalc
    if weighting == 2:
        # data-proportional
        error.real = np.real(error) / np.real(zdata)
        error.imag = np.imag(error) / np.imag(zdata)
    elif weighting == 3:
        # calc-proportional
        error.real = np.real(error) / np.real(zcalc)
        error.imag = np.imag(error) / np.imag(zcalc)
    elif weighting == 4:
        # data-modulus
        error = error / np.abs(zdata)
    elif weighting == 5:
        # calc-modulus
        error = error / np.abs(zcalc)

    # e1d = error.view(np.float64)
    e1d = np.zeros(zdata.size * 2, dtype=np.float64)
    e1d[0:e1d.size:2] = error.real
    e1d[1:e1d.size:2] = error.imag
    if np.count_nonzero(np.logical_or(np.isinf(e1d), np.isnan(e1d))):
        print("Residual NaN, INF")
    return e1d


def cost_vector(guess, Z, F, weighting, calc_func=None, T=None, Voltage=None, pars=None, guess_names=None,
                params_dict=None):
    """
    Type of weighting
    2: data-proportional
    3: calc-proportional
    4: data-modulus
    5: calc-modulus
    otherwise: unit weighting
    """
    for i in range(len(guess)):
        # print(guess_names[i])
        if guess[i] <= 0 and guess_names[i] != 'r_str':
            # print("WARNING ", i, guess[i].value)
            return 1.0e16 * np.ones(len(Z) * 2)

    params_dict_local = copy.deepcopy(params_dict)

    for idx, gs_name in enumerate(guess_names):
        if pars is None:
            params_dict_local[gs_name] = guess[idx]
        else:
            params_dict_local[gs_name] = guess[idx] * pars[idx]

    # calc = Linh_func_OLO(par * guess, F)
    calc = calc_func(params_dict_local, F, T, Voltage)

    if np.count_nonzero(np.logical_or(np.isinf(calc), np.isnan(calc))):
        return 1e16 * np.ones(len(Z) * 2)

    e1d = get_cost_vector(calc, Z, weighting)

    return e1d


def cost_scalar(guess, Z, F, weighting, calc_func=None, T=None, Voltage=None, pars=None, guess_names=None,
                params_dict=None):
    """
    """
    e1d = cost_vector(guess, Z, F, weighting, calc_func, T, Voltage, pars, guess_names, params_dict)
    return np.sum(np.array(e1d) ** 2)
    