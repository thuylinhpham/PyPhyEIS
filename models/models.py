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

def DX30_change_Cstar_d(parvals, f):
    """ define DX30 Generalized Battery model ....
    Change cstar_d
    """
    omegas = 2 * np.pi * np.array(f)

    Rm = parvals['rm']
    Rct = parvals['rct']
    Rd = parvals['rd']

    Cdl_C0 = parvals['cdl_c0']
    Cdl_HNC = parvals['cdl_hnc']
    Cdl_HNT = parvals['cdl_hnt']
    Cdl_HNP = parvals['cdl_hnp']
    Cdl_HNU = parvals['cdl_hnu']

    Cd_C0 = parvals['cd_c0']
    Cd_Cs = parvals['cd_cs']
    DE6_d_R = parvals['de6_d_r']
    DE6_d_T = parvals['de6_d_t']
    DE6_d_P = parvals['de6_d_p']
    DE6_d_U = parvals['de6_d_u']

    CPE_B_T = parvals['cpe_b_t']
    CPE_B_P = parvals['cpe_b_p']

    # Change cstar_d in here
    Zstar_d = np.divide(1.0, 1j * omegas * Cd_C0 + np.divide(1.0, np.divide(DE6_d_R, np.power(1 + np.power(1j * omegas * DE6_d_T, DE6_d_U), DE6_d_P)) + np.divide(1.0, 1j*omegas*Cd_Cs)))
    Cstar_d = np.divide(1.0, np.multiply(1j * omegas, Zstar_d))

    Cstar_dl = Cdl_C0 + Cdl_HNC / ((1 + (1j * omegas * Cdl_HNT) ** Cdl_HNU) ** Cdl_HNP)
    Cstar_B = CPE_B_T * ((1j * omegas) ** (CPE_B_P - 1))

    tanh_sqrt = np.sqrt(3 * Rd * (1j * omegas * Cstar_d))
    tanh_values = (1+0j)*np.ones(tanh_sqrt.shape, dtype=np.complex64)
    tanh_values[np.real(tanh_sqrt) < 100] = np.tanh(tanh_sqrt[np.real(tanh_sqrt) < 100])

    #Zd = np.tanh(np.sqrt(3 * Rd * (1j * omegas * Cstar_d))) / (
    #        np.sqrt(3 * 1j * omegas * Cstar_d / Rd) - (1 / Rd) * np.tanh(np.sqrt(3 * Rd * 1j * omegas * Cstar_d)))
    Zd = tanh_values / (
           np.sqrt(3 * 1j * omegas * Cstar_d / Rd) - (1 / Rd) * tanh_values)

    Zs = Rm
    Y_P = (1j * omegas * Cstar_dl) + 1.0 / (Rct + Zd)
    Z_B = 1.0 / (1j * omegas * Cstar_B)

    Z = (1 + Z_B * np.sqrt(Y_P / Zs) * (1.0 / np.tanh(np.sqrt(Zs * Y_P)))) / (
            Z_B * Y_P / Zs + np.sqrt(Y_P / Zs) * (1.0 / np.tanh(np.sqrt(Zs * Y_P))))

    return Z
    
def LR_DX30(parvals, f, T=None, Voltage=None, c_case=1):

    fit_zrzi = DX30_change_Cstar_d(parvals, f)

    # Add L1, DE1, R1
    L = parvals['l']
    R = parvals['r']
    R_OHM = parvals['r_ohm']
    Z_L = 1j * 2 * np.pi * f * L
    # End of L1, DE1, R1

    fit_zrzi = 1 / ((1 / Z_L) + (1 / R)) + R_OHM + fit_zrzi

    return fit_zrzi


def Phy_EIS(parvals, f, T=None, Voltage=None, c_case=3):
    """
    Full cell dx22 dx30
    c_case = 3 => DX30_change_Cstar_d
    """
    DX22_T2 = parvals['dx22_t2']
    DX22_P2 = parvals['dx22_p2']
    DX22_R2 = parvals['dx22_r2']
    
    DX22_T3 = parvals['dx22_t3']
    DX22_P3 = parvals['dx22_p3']
    DX22_R3 = parvals['dx22_r3']
    
    DX22_R1 = parvals['dx22_r1']
    
    iomega = 1j * 2* np.pi * f
    ZB_DX22 = np.divide(1.0, 1.0 / DX22_R2 + DX22_T2 * np.power(iomega, DX22_P2))
    ZP_DX22 = np.divide(1.0, 1.0 / DX22_R3 + DX22_T3 * np.power(iomega, DX22_P3))
    YP_DX22 = np.divide(1.0, ZP_DX22)
    Zs_DX22 = DX22_R1
    
    in_sqrt_div = np.sqrt(np.divide(YP_DX22, Zs_DX22))
    in_sqrt_mul = np.sqrt(np.multiply(Zs_DX22, YP_DX22))
    
    numerator = 1 + np.multiply(np.multiply(ZB_DX22, in_sqrt_div), 1.0 / np.tanh(in_sqrt_mul))
    denominator = np.multiply(ZB_DX22, np.divide(YP_DX22, Zs_DX22)) + np.multiply(in_sqrt_div, 1.0 / np.tanh(in_sqrt_mul))
    Z_DX22 = np.divide(numerator, denominator)
    
    Z_LR_DX30 = LR_DX30(parvals, f, c_case=c_case)
    
    Z_ret = Z_LR_DX30 + Z_DX22
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
    