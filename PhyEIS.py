from PyQt5.QtWidgets import QApplication
from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QVariant, QThread
from PyQt5.QtGui import QIcon
from models import models
import pandas as pd
import numpy as np
import copy
import os, random
from scipy.optimize import least_squares, leastsq, minimize, differential_evolution
import plotly
import plotly.graph_objs as go
from functools import partial

np.random.seed(211)
random.seed(211)

class RunFitting(QThread):
    def __init__(self, isFit, guess, ls_params, dr_method=False, fixed_params=None, minimize_method='L-BFGS-B',
                 md_type=1, name_dict=None, niters=1e+6):
        """

        :param isFit:
        :param guess: list of values will be fit (free parameters)
        :param ls_params: dictionary, dict of parameters (fixed, free)
        :param dr_method: use dr method or not
        """
        QThread.__init__(self)
        self.params_dict, self.recv_method, self.zp_data, self.fp_data, self.z_data, self.f_data, self.recv_wgt_index, self.calc_func, self.tp_data, self.t_data, self.volp_data, self.vol_data = ls_params
        self.result = None
        self.zf = None
        self.isFit = isFit
        self.fitReport = None
        self.Dr = dr_method
        self.epsilon = np.finfo('float64').eps
        if self.Dr:
            self.init_val = np.ones(len(guess))
            self.guess = guess
        else:
            self.init_val = guess
            self.guess = None
        self.p_cov = None
        self.perror = None
        self.perror_percent = None
        self.params_ret = None
        self.nfev = None
        self.mesg = None
        self.minimize_method = minimize_method
        self.guess_names = fixed_params
        self.chisqr = -1
        self.reduced_chisqr = -1
        self.success = False
        self.model_type = md_type
        self.name_dict = name_dict
        self.niters = int(niters)
        self.nfev = -1

    def fit_leastsq(self):
        """
        Leastsq fitting
        :return:
        """
        pv, cv, infodict, mesg, ier = leastsq(models.cost_vector, self.init_val,
                                              args=(self.zp_data, self.fp_data, self.recv_wgt_index, self.calc_func,
                                                    self.tp_data, self.volp_data, self.guess, self.guess_names,
                                                    self.params_dict),
                                              maxfev=self.niters,
                                              ftol=self.epsilon, gtol=self.epsilon, xtol=self.epsilon, full_output=True)

        self.params_ret = pv
        self.nfev = infodict['nfev']
        self.mesg = mesg
        if cv is not None:
            self.p_cov = cv * models.cost_scalar(self.params_ret, self.zp_data, self.fp_data,
                                                 self.recv_wgt_index, self.calc_func, self.tp_data,
                                                 self.volp_data, self.guess, self.guess_names,
                                                 self.params_dict) / (self.zp_data.size - self.init_val.size)
        self.p_cov = cv

        if ier in [1, 2, 3, 4]:
            self.success = True
        else:
            self.success = False

    def fit_leastsquares(self):
        """
        Leastsquares
        :return:
        """
        r_lsq = least_squares(models.cost_vector, self.init_val,
                              args=(self.zp_data, self.fp_data, self.recv_wgt_index, self.calc_func, self.tp_data,
                                    self.volp_data, self.guess, self.guess_names, self.params_dict),
                              max_nfev=self.niters,
                              ftol=self.epsilon, gtol=self.epsilon, xtol=self.epsilon, verbose=1)

        print("The number of function calls: ", r_lsq.nfev)
        self.mesg = r_lsq.message
        self.success = r_lsq.success
        self.nfev = r_lsq.nfev
        self.params_ret = r_lsq.x
        _, s, vh = np.linalg.svd(r_lsq.jac, full_matrices=False)
        threshold = self.epsilon * np.max(r_lsq.jac.shape) * s[0]
        s = s[s > threshold]
        vh = vh[:s.size]
        p_cov = np.dot(vh.T / s ** 2, vh)
        self.p_cov = p_cov * models.cost_scalar(self.params_ret, self.zp_data, self.fp_data,
                                                self.recv_wgt_index, self.calc_func, self.tp_data,
                                                self.volp_data, self.guess, self.guess_names,
                                                self.params_dict) / (self.zp_data.size - self.init_val.size)

    def fit_minimize(self):
        """
        Minimize
        :return:
        """
        r_bfgs = minimize(models.cost_scalar, self.init_val,
                          args=(self.zp_data, self.fp_data, self.recv_wgt_index, self.calc_func, self.tp_data,
                                self.volp_data, self.guess, self.guess_names, self.params_dict),
                          method=self.minimize_method, tol=self.epsilon,
                          options={'maxcor': 100, 'maxfun': self.niters, 'maxiter': self.niters, 'ftol': self.epsilon,
                                   'gtol': self.epsilon})

        self.params_ret = r_bfgs.x
        hess_inv = r_bfgs.hess_inv.todense()
        self.p_cov = 2.0 * hess_inv * models.cost_scalar(self.params_ret, self.zp_data, self.fp_data,
                                                         self.recv_wgt_index, self.calc_func, self.tp_data,
                                                         self.volp_data, self.guess, self.guess_names,
                                                         self.params_dict) / (self.zp_data.size - self.init_val.size)
        self.success = r_bfgs.success
        self.nfev = r_bfgs.nfev
        self.mesg = r_bfgs.message

    def fit_diev(self):
        """
        Differential evolution fitting
        :return:
        """
        if self.Dr:
            bnds = tuple((0.1, 10.0) for i in range(self.init_val.size))
        else:
            bnds = tuple((0.1, 10.0) for i in range(self.init_val.size))

        r_diev = differential_evolution(models.cost_scalar, bnds, args=(
            self.zp_data, self.fp_data, self.recv_wgt_index, self.calc_func, self.tp_data, self.volp_data, self.guess,
            self.guess_names, self.params_dict), maxiter=self.niters, tol=0.0001)

        self.params_ret = r_diev.x
        self.nfev = r_diev.nfev
        self.mesg = r_diev.message
        self.success = r_diev.success

    def run(self):
        """
        Running
        :return:
        """
        print("Running")
        epsilon = np.finfo('float64').eps
        resd = -1e20
        if self.isFit == 1:
            if self.recv_method == 'leastsq':
                self.fit_leastsq()

            elif self.recv_method == 'least_squares':
                self.fit_leastsquares()

            elif self.recv_method == 'minimize':
                self.fit_minimize()

            elif self.recv_method == 'differential_evolution':
                self.fit_diev()

            if self.p_cov is not None:
                self.perror = np.sqrt(np.diag(self.p_cov))
                self.perror_percent = 100 * self.perror / self.params_ret
            else:
                self.perror = ['N/A'] * len(self.guess)
                self.perror_percent = ['N/A'] * len(self.guess)

            if self.Dr:
                self.params_ret = np.multiply(self.params_ret, self.guess)
                if self.p_cov is not None:
                    self.perror = np.multiply(self.perror, self.guess)

            for idx, gs_name in enumerate(self.guess_names):
                self.params_dict[gs_name] = self.params_ret[idx]

            resd = np.sum(
                np.abs(self.calc_func(self.params_dict, self.fp_data, self.t_data, self.vol_data) - self.zp_data))
            self.zf = self.calc_func(self.params_dict, self.f_data, self.t_data, self.vol_data)
            self.zf[np.isinf(self.zf)] = 0
            print("CHECKED: ", np.count_nonzero(self.params_ret <= 0))

            self.chisqr = models.cost_scalar(self.params_ret, self.zp_data, self.fp_data,
                                             self.recv_wgt_index, self.calc_func, self.tp_data,
                                             self.volp_data, self.guess, self.guess_names,
                                             self.params_dict)
            self.reduced_chisqr = self.chisqr / (self.zp_data.size - self.init_val.size)

        elif self.isFit == 2:
            print("Simulation")
            self.zf = self.calc_func(self.params_dict, self.f_data, T=self.t_data, Voltage=self.vol_data)
            self.plot_data()

        self.result = {'param_ret': self.params_dict, 'perror': self.perror, 'perror_percent': self.perror_percent,
                       'chisqr': self.chisqr, 'red_chisqr': self.reduced_chisqr, 'success': self.success,
                       'message': self.mesg,
                       'residual': resd, 'nfev': self.nfev}
        self.plot_data()

        self.finished.emit()

    def plot_data(self):
        """
        Plot data
        :return:
        """
        html_graphs = open("impedance_plot.html", "w")
        html_graphs.write("<html><head></head><body>" + "\n")

        if self.model_type == 1:
            fitColor = '#008000'
            rawColor = '#FF0000'
            markerColor = '#0000FF'
            iFit = go.Scatter(x=np.real(self.zf), y=np.imag(self.zf), mode='lines', name='Fit',
                              line=dict(color=fitColor))
            iRaw = go.Scatter(x=np.real(self.z_data), y=np.imag(self.z_data), mode='lines+markers', name='Raw',
                              line=dict(color=rawColor), marker=dict(color=markerColor, size=5))

            iAdmitFit, iCapacFit, iCapacFit_abs, iAdmitRaw, iCapacRaw, iCapacRaw_abs = self.calc_admittance_capacitance()

            graph_names = ["Impedance", "Capacitance", "Admittance", "Linear Capacitance"]#, "Log abs Capacitance"]
            graph_data = [[iFit, iRaw], [iCapacFit, iCapacRaw], [iAdmitFit, iAdmitRaw], [iCapacFit, iCapacRaw], [iCapacFit_abs, iCapacRaw_abs]]
            yaxis_names = ['Z"', "E'", "Y'", "E'", "abs(E')"]
            xaxis_names = ["Z'", "Frequency (Hz)", "Frequency (Hz)", "Frequency (Hz)", "Frequency (Hz)"]
            for idx in range(len(graph_names)):
                cur_data = graph_data[idx]
                if idx == 0:
                    cur_layout = go.Layout(title=graph_names[idx],
                                           yaxis=dict(autorange='reversed', title=yaxis_names[idx], showline=True),
                                           xaxis=dict(title=xaxis_names[idx], showline=True))
                elif idx == 3:
                    cur_layout = go.Layout(title=graph_names[idx],
                                           yaxis=dict(title=yaxis_names[idx], type='linear', showline=True),
                                           xaxis=dict(title=xaxis_names[idx], type='log', showline=True))
                elif idx == 4:
                    cur_layout = go.Layout(title=graph_names[idx],
                                           yaxis=dict(title=yaxis_names[idx], type='log', showline=True),
                                           xaxis=dict(title=xaxis_names[idx], type='log', showline=True))
                else:
                    cur_layout = go.Layout(title=graph_names[idx],
                                           yaxis=dict(title=yaxis_names[idx], type='log', showline=True),
                                           xaxis=dict(title=xaxis_names[idx], type='log', showline=True))

                fig = go.Figure(data=cur_data, layout=cur_layout)
                plotly.offline.plot(fig, filename='Chart_' + graph_names[idx] + '.html', auto_open=False,
                                    include_mathjax='cdn',
                                    config={'scrollZoom': True, 'editable': False, 'edits': {'legendPosition': True},
                                            'showLink': False})
                html_graphs.write("  <object data=\"" + 'Chart_' + graph_names[
                    idx] + '.html' + "\" width=\"500\" height=\"500\" ></object>" + "\n")

        elif self.model_type == 2:
            # Impedance
            iFit = []
            iRaw = []
            fit_admit = []
            fit_capac = []
            fit_fim = []

            raw_admit = []
            raw_capac = []
            raw_fim = []

            keys = [int(x[:-4]) for x in self.name_dict.keys()]
            keys.sort()

            keys = ['{}.dat'.format(x) for x in keys]
            for key in keys:
                value = self.name_dict[key]
                cur_idx = self.t_data == value
                cur_f = self.f_data[cur_idx]
                cur_zf = self.zf[cur_idx]
                cur_zraw = self.z_data[cur_idx]

                cur_fit = go.Scatter(x=np.real(cur_zf), y=np.imag(cur_zf), mode='lines', name=key)
                cur_fit_admit = go.Scatter(x=cur_f, y=self.get_admittance(cur_zf), mode='lines+markers', name=key)
                cur_fit_capac = go.Scatter(x=cur_f, y=self.get_capacitance(cur_f, cur_zf), mode='lines+markers',
                                           name=key)

                cur_raw = go.Scatter(x=np.real(cur_zraw), y=np.imag(cur_zraw), mode='lines+markers', name=key)
                cur_raw_admit = go.Scatter(x=cur_f, y=self.get_admittance(cur_zraw), mode='lines+markers', name=key)
                cur_raw_capac = go.Scatter(x=cur_f, y=self.get_capacitance(cur_f, cur_zraw), mode='lines+markers',
                                           name=key)

                iFit.append(cur_fit)
                fit_fim.append(go.Scatter(x=cur_f, y=-np.imag(cur_zf), mode='lines+markers', name=key))
                fit_admit.append(cur_fit_admit)
                fit_capac.append(cur_fit_capac)

                iRaw.append(cur_raw)
                raw_fim.append(go.Scatter(x=cur_f, y=-np.imag(cur_zraw), mode='lines+markers', name=key))
                raw_admit.append(cur_raw_admit)
                raw_capac.append(cur_raw_capac)

            graph_names = ['Capacitance', 'Admittance', '', 'Impedance']
            yaxis_names = ["E'", "Y'", 'Z"', 'Z"']
            xaxis_names = ["Frequency", "Frequency", "Frequency", "Z'"]
            graph_data = [(fit_capac, raw_capac), (fit_admit, raw_admit), (fit_fim, raw_fim), (iFit, iRaw)]
            for idx in range(len(graph_names)):
                cur_fit, cur_raw = graph_data[idx]
                if idx == len(graph_names) - 1:
                    cur_layout = go.Layout(title=graph_names[idx],
                                           yaxis=dict(autorange='reversed', title=yaxis_names[idx], showline=True),
                                           xaxis=dict(title=xaxis_names[idx], showline=True))
                elif idx == len(graph_names) - 2:
                    cur_layout = go.Layout(title=graph_names[idx],
                                           yaxis=dict(autorange='reversed', type='log', title=yaxis_names[idx],
                                                      showline=True),
                                           xaxis=dict(title=xaxis_names[idx], type='log', showline=True))
                else:
                    cur_layout = go.Layout(title=graph_names[idx],
                                           yaxis=dict(title=yaxis_names[idx], type='log', showline=True),
                                           xaxis=dict(title=xaxis_names[idx], type='log', showline=True))

                fig1 = go.Figure(data=cur_fit, layout=cur_layout.update(title="Fit " + graph_names[idx]))
                plotly.offline.plot(fig1, filename='Chart_' + graph_names[idx] + '_Fit.html', auto_open=False,
                                    include_mathjax='cdn',
                                    config={'scrollZoom': True, 'editable': False, 'edits': {'legendPosition': True},
                                            'showLink': False})
                html_graphs.write("  <object data=\"" + 'Chart_' + graph_names[
                    idx] + '_Fit.html' + "\" width=\"500\" height=\"500\" ></object>" + "\n")

                fig2 = go.Figure(data=cur_raw, layout=cur_layout.update(title="Raw " + graph_names[idx]))
                plotly.offline.plot(fig2, filename='Chart_' + graph_names[idx] + '_Raw.html', auto_open=False,
                                    include_mathjax='cdn',
                                    config={'scrollZoom': True, 'editable': False, 'edits': {'legendPosition': True},
                                            'showLink': False})
                html_graphs.write("  <object data=\"" + 'Chart_' + graph_names[
                    idx] + '_Raw.html' + "\" width=\"500\" height=\"500\" ></object>" + "\n")

            freqs = np.unique(self.fp_data)
            for fq in freqs:
                fq_index = np.abs(self.f_data - fq) < 1e-10

            # print(freqs)

        html_graphs.write("</body></html>")
        self.plotStrings = "impedance_plot.html"

    @staticmethod
    def get_admittance(zdata):
        """
        Calc admittance
        :param zdata:
        :return:
        """
        cur_real = np.real(zdata)
        cur_im = np.imag(zdata)
        cur_admit = np.divide(cur_real, np.power(cur_real, 2.0) + np.power(cur_im, 2.0))
        return cur_admit

    @staticmethod
    def get_capacitance(freq, zdata):
        """
        Calc capacitance
        :param zdata:
        :return:
        """
        cur_real = np.real(zdata)
        cur_im = np.imag(zdata)
        cur_capacitance = -1 * np.divide(np.divide(cur_im, np.power(cur_im, 2.0) + np.power(cur_real, 2.0)) / 2 / np.pi,
                                         freq)
        return cur_capacitance

    def calc_admittance_capacitance(self):
        """
        Emit Admittance
        """
        fitColor = '#008000'
        rawColor = '#FF0000'
        markerColor = '#0000FF'

        cur_real = np.real(self.zp_data)
        cur_im = np.imag(self.zp_data)
        root_data = self.fp_data

        raw_Capa = -1 * np.divide(np.divide(cur_im, np.power(cur_im, 2.0) + np.power(cur_real, 2.0)) / 2 / np.pi,
                                  root_data)
        
        raw_Admit = np.divide(cur_real, np.power(cur_real, 2.0) + np.power(cur_im, 2.0))

 
        
        iAdmitRaw = go.Scatter(x=root_data, y=raw_Admit, mode='lines+markers', name='Raw', line=dict(color=rawColor),
                               marker=dict(color=markerColor, size=5))
        iCapacRaw = go.Scatter(x=root_data, y=raw_Capa, mode='lines+markers', name='Raw', line=dict(color=rawColor),
                               marker=dict(color=markerColor, size=5))
        iCapacRaw_abs = go.Scatter(x=root_data, y=np.abs(raw_Capa), mode='lines+markers', name='Raw', line=dict(color=rawColor),
                               marker=dict(color=markerColor, size=5))
                               
        cur_real = np.real(self.zf)
        cur_im = np.imag(self.zf)

        ret_Capa = -1 * np.divide(np.divide(cur_im, np.power(cur_im, 2.0) + np.power(cur_real, 2.0)) / 2 / np.pi,
                                  root_data)
        ret_Admit = np.divide(cur_real, np.power(cur_real, 2.0) + np.power(cur_im, 2.0))

        
        
        
        
        iAdmitFit = go.Scatter(x=root_data, y=ret_Admit, mode='lines', name='Fit', line=dict(color=fitColor))
        iCapacFit = go.Scatter(x=root_data, y=ret_Capa, mode='lines', name='Fit', line=dict(color=fitColor))
        iCapacFit_abs = go.Scatter(x=root_data, y=np.abs(ret_Capa), mode='lines', name='Fit', line=dict(color=fitColor))

        return iAdmitFit, iCapacFit, iCapacFit_abs, iAdmitRaw, iCapacRaw, iCapacRaw_abs


class FittingImpedance(QObject):
    def __init__(self, rootObj=None):
        QObject.__init__(self)
        self.rootObj = rootObj
        self.f_data, self.z_data, self.fp_data, self.zp_data = (None, None, None, None)
        self.result = None
        self.recv_wgt = ""
        self.recv_method = ""
        self.recv_mdl = ""
        self.recv_data = ""
        self.recv_names = ""
        self.wgt_method = ['unit', 'dataProportional', 'calcProportional', 'dataModulus', 'calcModulus']
        self.method_dict = ['leastsq', 'least_squares', 'minimize', 'differential_evolution']
        self.calc_func = None
        self.params = None
        self.recv_wgt_index = None
        self.runFittingSimulation = 0
        self.runObject = None
        self.parsed_params, self.fit_errors, self.fit_errors_percent = None, None, None
        self.fitreport = None
        self.md_type = 1
        self.name_dict = None

        self.tp_data, self.t_data, self.volp_data, self.vol_data = [None, None, None, None]
        self.zf = None
        self.dr_method = False
        self.terminated = False
        self.niters = 1000000
        self.rm_positive = False

    def reset_properties(self):
        """
        Reset all values
        :return:
        """
        self.f_data, self.z_data, self.fp_data, self.zp_data = (None, None, None, None)
        self.result = None
        self.recv_wgt = ""
        self.recv_method = ""
        self.recv_mdl = ""
        self.recv_data = ""
        self.recv_names = ""
        self.calc_func = None
        self.params = None
        self.recv_wgt_index = None
        self.runFittingSimulation = 0
        self.runObject = None
        self.parsed_params, self.fit_errors, self.fit_errors_percent = None, None, None
        self.fitreport = None
        self.md_type = 1
        self.name_dict = None
        self.terminated = False

        self.tp_data, self.t_data, self.volp_data, self.vol_data = [None, None, None, None]
        self.zf = None
        self.niters = 1000000
        self.rm_positive = False

    def setRootObj(self, rootObj):
        self.rootObj = rootObj
        # for child in self.rootObj.findChildren(QGridLayout):
        #     print(type(child))
        # print(self.rootObj.findChildren(QObject))

    fitCompleted = pyqtSignal(list, list, arguments=['new_params', "fit_ret"])
    fitCompleted2 = pyqtSignal()
    paramsZfitEmit = pyqtSignal(list, list, list, list, list, list, list, list,
                                arguments=['z_real', 'z_imag', 'param_names', 'best_params', "error_fit",
                                           "error_fit_percent", "zf_real", "zf_imag"])
    simulationEmit = pyqtSignal(list, list, list, list,
                                arguments=['z_real', 'z_imag', "zf_real", "zf_imag"])

    fitStatus = pyqtSignal(int, arguments=['fit_status'])
    chiSquare = pyqtSignal(QVariant, QVariant, QVariant,
                           arguments=['chiSquare_Val', 'redChiSquare_Val', 'residual_Val'])
    capacitanceEmit = pyqtSignal(list, list, list, arguments=['freqs', 'rvalue', 'rdvalue'])
    admittanceEmit = pyqtSignal(list, list, list, arguments=['freqs', 'rvalue', 'rdvalue'])
    fitReport = pyqtSignal(QVariant, arguments=['fitReportStr'])

    plotStringSignal = pyqtSignal(QVariant, arguments=['plotHtmlString'])
    fitLog = pyqtSignal(QVariant, arguments=['fit_log'])

    loadParamsEmit = pyqtSignal(list, list, list, list, list, arguments=['param_names', 'best_params', 'error_fit', 'error_fit_percent', 'par_frees'])
    # Slot for fitting
    @pyqtSlot(list, list, list, QVariant, int, QVariant, QVariant, int, int)
    def fitting(self, recv_names, recv_vals, recv_fixed, recv_mdl, recv_wgt, recv_method, recv_data, isFit, rm_positive):
        """

        :param recv_names:  Parameter names
        :param recv_vals:   Parameter values
        :param recv_fixed:  Parameter fixed or free
        :param recv_mdl:    Model type: DX30, DX29, .....
        :param recv_wgt:    Weighting method: 1,2,3,4,5,6
        :param recv_method: Fitting method: leastsq, least_squares, ....
        :param recv_data:   path to data file
        :return:
        """
        self.reset_properties()
        
        self.recv_wgt = self.wgt_method[recv_wgt]
        self.recv_wgt_index = recv_wgt + 1
        self.recv_method = recv_method
        self.recv_mdl = recv_mdl
        self.recv_data = recv_data
        self.recv_names = recv_names
        self.dr_method = False
        self.rm_positive = True if rm_positive == 1 else False


        self.niters = 100000
        self.dr_method = False

        # Initialize values
        self.params = {}
        self.guess_names = []
        self.guess_values = []
        for idx in range(len(recv_names)):
            self.params[recv_names[idx]] = float(recv_vals[idx])
            if 1 - recv_fixed[idx]:
                self.guess_names.append(recv_names[idx])
                self.guess_values.append(float(recv_vals[idx]))

        self.guess_values = np.array(self.guess_values)

        # Read data
        print('Recved MDL: ', recv_mdl)
            
        if recv_mdl == "Phy-EIS":
            self.f_data, self.z_data, self.fp_data, self.zp_data = self.dx30_read_data(recv_data)
            self.calc_func = partial(models.Phy_EIS, c_case=3)

        # Run fitting/simulation
        self.runFittingSimulation = isFit

        self.runObject = RunFitting(self.runFittingSimulation, self.guess_values,
                                    [self.params, self.recv_method, self.zp_data, self.fp_data, self.z_data,
                                     self.f_data,
                                     self.recv_wgt_index, self.calc_func, self.tp_data, self.t_data, self.volp_data,
                                     self.vol_data], dr_method=self.dr_method, fixed_params=self.guess_names,
                                    md_type=self.md_type, name_dict=self.name_dict, niters=self.niters)

        self.runObject.finished.connect(self.done)
        self.runObject.start()

        print("Emited signal")

    @pyqtSlot()
    def stop_fitting(self):
        """
        Stop fitting
        :return:
        """
        self.terminated = True
        self.runObject.terminate()

    def done(self):
        """
        Done
        :return:
        """
        if self.terminated:
            self.fitStatus.emit(-1)
            return
        if self.runFittingSimulation == 2:
            self.zf = copy.deepcopy(self.runObject.zf)
            self.fitStatus.emit(1)

            self.result = copy.deepcopy(self.runObject.result)
            self.parsed_params, self.fit_errors, self.fit_errors_percent = self.parse_params_ret()

            self.simulationEmit.emit(np.real(self.z_data).tolist(), np.imag(self.z_data).tolist(),
                                     np.real(self.zf).tolist(), np.imag(self.zf).tolist())

            self.chiSquare.emit('0', '0', '0')
            tmp = self.runObject.plotStrings

            tmp = tmp.replace("file://", "file:///")
            tmp = tmp.replace("\\", "/")
            self.plotStringSignal.emit(tmp)

            self.fitLog.emit("Simulation completed")
            
        else:
            self.result = copy.deepcopy(self.runObject.result)

            n_fev = self.runObject.result['nfev']
            mesg = self.runObject.result['message']
            
            success_str = "Success" if self.runObject.result['success'] else "Failed"

            wgt_str = self.recv_wgt
            fit_met = self.recv_method
            str_log = "Method: {0}.\nWeighting: {1}.\nNumber of iteration: {2}\n{3}: {4}".format(fit_met, wgt_str, n_fev, success_str, mesg)
            self.fitLog.emit(str_log)

            if self.result['success']:
                self.zf = copy.deepcopy(self.runObject.zf)

                tmp = self.runObject.plotStrings

                print(self.result['message'])

                self.fitStatus.emit(1)

                self.parsed_params, self.fit_errors, self.fit_errors_percent = self.parse_params_ret()

                self.paramsZfitEmit.emit(np.real(self.z_data).tolist(), np.imag(self.z_data).tolist(), self.recv_names,
                                         self.parsed_params, self.fit_errors, self.fit_errors_percent,
                                         np.real(self.zf).tolist(),
                                         np.imag(self.zf).tolist())
                self.chiSquare.emit('{:10.5e}'.format(self.result['chisqr']),
                                    '{:10.5e}'.format(self.result['red_chisqr']),
                                    '{:10.5e}'.format(self.result['residual']))

                tmp = tmp.replace("file://", "file:///")
                tmp = tmp.replace("\\", "/")
                self.plotStringSignal.emit(tmp)
                print(os.getcwd(), tmp)
            else:
                self.fitStatus.emit(0)

    @pyqtSlot(QVariant)
    def loadParameters(self, load_path):
        """
        Load parameters from file
        """
        df_pars = pd.read_csv(load_path, header=None, sep=',').values
        df_names = df_pars[0, :]
        df_values = df_pars[1, :]

        par_values = []
        par_names = []
        par_frees = [1] * (len(df_names) // 3) 
        for idx in range(len(df_names) // 3):
            par_names.append(df_names[3*idx])
            par_values.append(df_values[3*idx])
            if np.isnan(float(df_values[3*idx + 1])):
                par_frees[idx] = 0

        error_fit = ['']*len(par_values)
        error_fit_percent = ['']*len(par_values)
        self.loadParamsEmit.emit(par_names, par_values, error_fit, error_fit_percent, par_frees)
        self.fitLog.emit("Load parameters completed")


    @pyqtSlot(QVariant)
    def saveParameters(self, saved_path):
        """
        Save parameter to file
        :return:
        """
        data_name = self.recv_data.split("/")[-1][:-4]
        # write_name = './results/' + '_'.join((data_name, self.recv_mdl, self.recv_method, self.recv_wgt))
        write_name = saved_path + '.csv'

        cols = [""] * (3 * len(self.recv_names))
        cols_values = [-1] * (3 * len(self.recv_names))

        for idx in range(len(self.recv_names)):
            cols[3 * idx] = self.recv_names[idx].upper()
            cols[3 * idx + 1] = self.recv_names[idx].upper() + '_error'
            cols[3 * idx + 2] = self.recv_names[idx].upper() + '_error %'

            cols_values[3 * idx] = self.parsed_params[idx]
            cols_values[3 * idx + 1] = self.fit_errors[idx]
            cols_values[3 * idx + 2] = self.fit_errors_percent[idx]

        cols_values = np.array(cols_values).reshape(1, -1)
        pd.DataFrame(cols_values, columns=cols).to_csv(write_name, index=None, sep=',')

    @pyqtSlot(QVariant)
    def saveFitResults(self, saved_path):
        """
        Save fit results to file
        :return:
        """
        if self.md_type == 1:
            data_name = self.recv_data.split("/")[-1][:-4]
            write_name = saved_path + ".txt"
            write_data = np.vstack((self.f_data, np.real(self.zf), np.imag(self.zf))).T
            pd.DataFrame(write_data).to_csv(write_name, header=False, index=None, sep='\t')
        else:
            for key, value in self.name_dict.items():
                cur_idx = self.t_data == value
                cur_f = self.f_data[cur_idx]
                cur_zf = self.zf[cur_idx]

                txt_name = saved_path + '/' + key
                write_data = np.vstack((cur_f, np.real(cur_zf), np.imag(cur_zf))).T
                pd.DataFrame(write_data, columns=['Frequency', 'Real Impedance', 'Imaginary Impedance']).to_csv(
                    txt_name, encoding='ascii', sep='\t', header=True, index=False)
                with open(txt_name, 'r+') as fd:
                    contents = fd.read()
                    fd.seek(0, 0)
                    fd.write('\n{}\n\n\n\n'.format(value) + contents)

            print(saved_path)

    # Slot for simulation
    @pyqtSlot()
    def simulation(self):
        print("Simulation")

    def parse_params_ret(self):
        """

        :param param_names: Parameter names
        :return: arr of parameter values corresponding to parameter names
        """
        ret = []
        ret_error = [''] * len(self.recv_names)
        ret_error_percent = [''] * len(self.recv_names)
        
        parvals = self.result['param_ret']
        if self.result['perror'] is None:
            print('None')
            perror = [''] * len(self.recv_names)
        else:
            perror = self.result['perror']

        if self.result['perror_percent'] is None:
            print('None')
            perror_percent =  [''] * len(self.recv_names)
        else:
            perror_percent = self.result['perror_percent']

        for idx in range(len(self.recv_names)):
            name = self.recv_names[idx]
            ret.append('{:12.6e}'.format(float(parvals[name])))
            if name in self.guess_names:
                cur_idx = self.guess_names.index(name)
                if perror[cur_idx] != '':
                    ret_error[idx] = '{:12.6e}'.format(perror[cur_idx])
                    ret_error_percent[idx] = '{:12.6e}'.format(perror_percent[cur_idx])

        return ret, ret_error, ret_error_percent

    def dx30_read_data(self, dataPath):
        """
        Load dx30 data from dataPath
        :param dataPath:
        :return:
        """
        df = pd.read_csv(dataPath, sep="\t", header=None).values
        f_data = df[:, 0]
        z_data = df[:, 1] + 1j * df[:, 2]

        # Keep data with imag < 0
        if self.rm_positive:
            kp_data = (df[:, 2] < 0)
            fp_data = f_data[kp_data]
            zp_data = z_data[kp_data]
        else:
            fp_data = f_data.copy()
            zp_data = z_data.copy()

        return f_data, z_data, fp_data, zp_data

    def llz_read_data(self, ls_data_path):
        """
    
        :param raw_data_path: path to LLZ raw data
        :return:
        """
        list_raw = sorted(ls_data_path.split(";"))

        list_raw_data = [x.replace("//", "/") for x in list_raw if x.endswith(".dat")]

        list_name_data = np.array([x.split('/')[-1] for x in list_raw_data])
        list_raw_data = [x for x in list_raw_data]

        F_read = []
        Z = []
        ls_00 = []
        ls_temperature = []
        n_cnt = 0
        name_dict = {}

        # Check if a temperature appear multiple time
        ck_temps = []
        is_append = True
        for fd in list_raw_data:
            with open(fd) as fo:
                fo = open(fd)
                lines = fo.readlines()
                cur_F = []
                cur_Z = []
                cur_temp = -1
                for ix in range(len(lines)):

                    line = lines[ix]

                    if ix == 0:
                        ls_00.append(float(line))

                    elif ix == 1:
                        cur_temp = float(line)
                        if cur_temp in ck_temps:
                            is_append = False
                            break
                        else:
                            is_append = True
                            ck_temps.append(cur_temp)

                    elif ix > 6 and line != '':
                        line = line.replace('\\n', '')
                        xs = [float(vl) for vl in line.split('\t')]

                        cur_F.append(xs[0])
                        cur_Z.append(xs[1] + 1j * xs[2])

                        n_cnt += 1
                if is_append:
                    F_read = F_read + [cur_F]
                    Z = Z + [cur_Z]
                    ls_temperature = ls_temperature + [cur_temp] * len(cur_F)

                    name_dict[fd.split('/')[-1]] = cur_temp

        F_read = np.array(F_read, dtype=np.float64).reshape(1, -1).flatten()
        Z = np.array(Z).reshape(1, -1).flatten()
        ls_temperature = np.array(ls_temperature, dtype=np.float64).flatten()

        if self.rm_positive:
            kpZ = np.imag(Z) < 0
            F_fit = F_read[kpZ].flatten()
            Z_fit = Z[kpZ].flatten()
            T_fit = ls_temperature[kpZ.flatten()]
        else:
            F_fit = F_read.copy().flatten()
            Z_fit = Z.copy().flatten()
            T_fit = ls_temperature.copy().flatten()

        print(name_dict)
        return F_read.flatten(), Z, ls_temperature.flatten(), F_fit, Z_fit, T_fit, name_dict

    def otmlsm10_read_data(self, ls_data_path):
        """

        :param ls_data_path:
        :return:
        """
        list_raw = sorted(ls_data_path.split(";"))

        list_raw_data = [x.replace("//", "/") for x in list_raw if x.endswith(".dat")]

        list_name_data = np.array([x.split('/')[-1] for x in list_raw_data])
        list_raw_data = [x for x in list_raw_data]

        F_read = []
        Z = []
        ls_00 = []
        ls_temperature = []
        n_cnt = 0
        name_dict = {}

        # Check if a temperature appear multiple time
        ck_temps = []
        is_append = True
        for fd in list_raw_data:
            with open(fd) as fo:
                fo = open(fd)
                lines = fo.readlines()
                cur_F = []
                cur_Z = []
                cur_temp = -1
                for ix in range(len(lines)):

                    line = lines[ix]

                    if ix == 1:
                        cur_temp = float(line)
                        if cur_temp in ck_temps:
                            is_append = False
                            break
                        else:
                            is_append = True
                            ck_temps.append(cur_temp)

                    elif ix > 6 and line != '':
                        line = line.replace('\\n', '')
                        xs = [float(vl) for vl in line.split('\\t')]

                        cur_F.append(xs[0])
                        cur_Z.append(xs[1] + 1j * xs[2])

                        n_cnt += 1

                if is_append:
                    F_read = F_read + [cur_F]
                    Z = Z + [cur_Z]
                    ls_temperature = ls_temperature + [cur_temp] * len(cur_F)

                    name_dict[fd.split('/')[-1]] = cur_temp

        F_read = np.array(F_read, dtype=np.float64).reshape(1, -1)
        Z = np.array(Z).reshape(1, -1)
        ls_temperature = np.array(ls_temperature, dtype=np.float64)

        if self.rm_positive:
            kpZ = np.imag(Z) < 0
            F_fit = F_read[kpZ].flatten()
            Z_fit = Z[kpZ].flatten()
            T_fit = ls_temperature[kpZ.flatten()]
        else:
            F_fit = F_read.copy().flatten()
            Z_fit = Z.copy().flatten()
            T_fit = ls_temperature.copy().flatten()

        print(name_dict)
        return F_read.flatten(), Z, ls_temperature.flatten(), F_fit, Z_fit, T_fit, name_dict
        pass


if __name__ == "__main__":
    import sys

    # os.makedirs('./results', exist_ok=True)

    # Create an instance of the application
    app = QApplication(sys.argv)
    app.setOrganizationName("ECL")
    app.setApplicationName("Phy-EIS")
    app.setApplicationVersion('1.0')
    app.setWindowIcon(QIcon("icon.ico"))

    # Create QML engine
    engine = QQmlApplicationEngine()

    # Create a fitting impedance object
    impedance = FittingImpedance()
    # And register it in the context of QML
    engine.rootContext().setContextProperty("impedance", impedance)

    # Load the qml file into the engine
    engine.load("impedanceUI_v2.qml")

    rootObj = engine.rootObjects()[0]
    impedance.setRootObj(rootObj)

    engine.quit.connect(app.quit)
    sys.exit(app.exec_())
