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

def diffcylim(w, Rd, Cd):
    """ diffcylim Rd Cd """
    ret_sqrt = np.sqrt(Rd * np.multiply(1j*w, Cd))

    ret_mp = [Rd * mpmath.besseli(0, x) /  (x * mpmath.besseli(1, x)) for x in ret_sqrt]
    
    z_ret = np.array(ret_mp, dtype=np.complex128)
    return z_ret

def Barsoukov_Pham_Lee_1(parvals, f):
    """ Barsoukov-Pham-Lee #1D """

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
    Cd_HNC = parvals['cd_hnc']
    Cd_HNT = parvals['cd_hnt']
    Cd_HNP = parvals['cd_hnp']
    Cd_HNU = parvals['cd_hnu']
    CPE_B_T = parvals['cpe_b_t']
    CPE_B_P = parvals['cpe_b_p']

    Cstar_d = Cd_C0 + Cd_HNC / ((1 + (1j * omegas * Cd_HNT) ** Cd_HNU) ** Cd_HNP)
    Cstar_dl = Cdl_C0 + Cdl_HNC / ((1 + (1j * omegas * Cdl_HNT) ** Cdl_HNU) ** Cdl_HNP)
    Cstar_B = CPE_B_T * ((1j * omegas) ** (CPE_B_P - 1))

    Zd_numerator = np.sqrt(Rd / (1j*np.multiply(omegas, Cstar_d)))
    Zd_denominator = np.tanh(np.sqrt(Rd*1j * np.multiply(omegas, Cstar_d)))

    Zd = np.divide(Zd_numerator, Zd_denominator)

    Zs = Rm
    Y_P = (1j * omegas * Cstar_dl) + 1.0 / (Rct + Zd)
    Z_B = 1.0 / (1j * omegas * Cstar_B)

    Z = (1 + Z_B * np.sqrt(Y_P / Zs) * (1.0 / np.tanh(np.sqrt(Zs * Y_P)))) / (
            Z_B * Y_P / Zs + np.sqrt(Y_P / Zs) * (1.0 / np.tanh(np.sqrt(Zs * Y_P))))

    return Z
    
def Barsoukov_Pham_Lee_2(parvals, f):
    """ 
    Barsoukov-Pham-Lee #2D
    """
    #co factor 2trong Cd, 2 trong Ci
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
    Cd_HNC = parvals['cd_hnc']
    Cd_HNT = parvals['cd_hnt']
    Cd_HNP = parvals['cd_hnp']
    Cd_HNU = parvals['cd_hnu']
    CPE_B_T = parvals['cpe_b_t']
    CPE_B_P = parvals['cpe_b_p']

    Cstar_d = Cd_C0 + (2*(Cd_HNC + Cd_C0)- Cd_C0)/ ((1 + (1j * omegas * Cd_HNT) ** Cd_HNU) ** Cd_HNP)
    Cstar_dl = Cdl_C0 + Cdl_HNC / ((1 + (1j * omegas * Cdl_HNT) ** Cdl_HNU) ** Cdl_HNP)
    Cstar_B = CPE_B_T * ((1j * omegas) ** (CPE_B_P - 1))

    Zd = diffcylim(omegas, Rd, Cstar_d)

    Zs = Rm
    Y_P = (1j * omegas * Cstar_dl) + 1.0 / (Rct + Zd)
    Z_B = 1.0 / (1j * omegas * Cstar_B)

    Z = (1 + Z_B * np.sqrt(Y_P / Zs) * (1.0 / np.tanh(np.sqrt(Zs * Y_P)))) / (
            Z_B * Y_P / Zs + np.sqrt(Y_P / Zs) * (1.0 / np.tanh(np.sqrt(Zs * Y_P))))

    return Z

def Barsoukov_Pham_Lee_3(parvals, f):
    """ 
    Barsoukov-Pham-Lee #3D
    """
    #co factor 3 trong Cd, 3 trong Ci
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
    Cd_HNC = parvals['cd_hnc']
    Cd_HNT = parvals['cd_hnt']
    Cd_HNP = parvals['cd_hnp']
    Cd_HNU = parvals['cd_hnu']
    CPE_B_T = parvals['cpe_b_t']
    CPE_B_P = parvals['cpe_b_p']

    Cstar_d = Cd_C0 + (3*(Cd_HNC + Cd_C0)- Cd_C0) / ((1 + (1j * omegas * Cd_HNT) ** Cd_HNU) ** Cd_HNP)
    Cstar_dl = Cdl_C0 + Cdl_HNC / ((1 + (1j * omegas * Cdl_HNT) ** Cdl_HNU) ** Cdl_HNP)
    Cstar_B = CPE_B_T * ((1j * omegas) ** (CPE_B_P - 1))

    tanh_sqrt = np.sqrt(Rd * (1j * omegas * Cstar_d))
    tanh_values = (1+0j)*np.ones(tanh_sqrt.shape, dtype=np.complex64)
    tanh_values[np.real(tanh_sqrt) < 100] = np.tanh(tanh_sqrt[np.real(tanh_sqrt) < 100])

    Zd = tanh_values / (
           np.sqrt(1j * omegas * Cstar_d / Rd) - (1 / Rd) * tanh_values)

    Zs = Rm
    Y_P = (1j * omegas * Cstar_dl) + 1.0 / (Rct + Zd)
    Z_B = 1.0 / (1j * omegas * Cstar_B)

    Z = (1 + Z_B * np.sqrt(Y_P / Zs) * (1.0 / np.tanh(np.sqrt(Zs * Y_P)))) / (
            Z_B * Y_P / Zs + np.sqrt(Y_P / Zs) * (1.0 / np.tanh(np.sqrt(Zs * Y_P))))

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

    L = parvals['l']
    R = parvals['r']
    R_OHM = parvals['r_ohm']
    Z_L = 1j * 2 * np.pi * f * L

    fit_zrzi = 1 / ((1 / Z_L) + (1 / R)) + R_OHM + fit_zrzi

    return fit_zrzi


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
    