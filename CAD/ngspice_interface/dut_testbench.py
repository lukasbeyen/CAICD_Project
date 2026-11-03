import time
import numpy as np
import os
import scipy.interpolate as interp
import scipy.optimize as sciopt
from scipy.optimize import differential_evolution
from .area_estimation import BPTM45nmAreaEstimator
from .ngspice_wrapper import NgspiceWrapper


class DUT(NgspiceWrapper):
    def measure_metrics(self):
        # returns None for a failed simulation (output files missing or empty), like NgspiceWrapper does
        if not self.parse_outputs():
            return None
        spec_dict = {}
        # post process raw data
        area_estimator = BPTM45nmAreaEstimator(self.circuit_params, self.circuit_multipliers)
        spec_dict['area'] = area_estimator.find_area()
        spec_dict['current'] = self.current
        spec_dict['gain'] = self.find_dc_gain(self.vout_complex)
        spec_dict['noise'] = self.noise
        spec_dict['phm'] = self.find_phm(self.freq, self.vout_complex)
        spec_dict['slewRate'] = self.find_slew_rate(self.time, self.vout_tran, threshold_low=0.1, threshold_high=0.9, time_unit='us')
        spec_dict['ugbw'] = self.find_ugbw(self.freq, self.vout_complex)

        return spec_dict
    
    def parse_outputs(self):
        tran_fname = os.path.join(self.output_files_folder, 'tran_'+self.random_name+'.csv')
        ac_fname = os.path.join(self.output_files_folder, 'ac_'+self.random_name+'.csv')
        dc_fname = os.path.join(self.output_files_folder, 'dc_'+self.random_name+'.csv')
        noise_fname = os.path.join(self.output_files_folder, 'noise_'+self.random_name+'.csv')
        # add these file names in a list
        self.output_files = [tran_fname, ac_fname, dc_fname, noise_fname]
        for file in self.output_files:
            if not os.path.isfile(file) or os.path.getsize(file) == 0:
                print(f"{file} doesn't exist or is empty")
                return False
        tran_raw_outputs = np.genfromtxt(tran_fname, skip_header=1)
        ac_raw_outputs = np.genfromtxt(ac_fname, skip_header=1)
        dc_raw_outputs = np.genfromtxt(dc_fname, skip_header=1)
        noise_raw_outputs = np.genfromtxt(noise_fname, skip_header=1)

        self.time = tran_raw_outputs[:, 0]
        self.vout_tran = tran_raw_outputs[:, 1]
        
        self.freq = ac_raw_outputs[:, 0]
        vout_real = ac_raw_outputs[:, 1]
        vout_imag = ac_raw_outputs[:, 2]
        self.vout_complex = vout_real + 1j*vout_imag
        
        self.current = - dc_raw_outputs[1]

        self.noise = noise_raw_outputs[0]
        return True
    
    def find_dc_gain(self, vout):
        """
        TODO: Implement the DC gain calculation
        
        Hint:
        Use numpy's abs() function to calculate the magnitude of the complex number at each point.
        """
        return np.abs(vout[0])
        
        
    def find_ugbw(self, freq, vout):
        """
        Unity gain bandwidth: the frequency where the gain magnitude |vout| drops through 1 (0 dB).
        Use the spline-based root finder on the log-log representation to interpolate the exact crossing.
        """
        freq = np.asarray(freq, dtype=float)
        gain = np.abs(vout)
        mask = np.isfinite(freq) & np.isfinite(gain) & (freq > 0) & (gain > 0)
        if np.count_nonzero(mask) < 2:
            return 0.0

        xvec = np.log10(freq[mask])
        yvec = np.log10(gain[mask])
        root, ok = self._get_best_crossing(xvec, yvec, 0.0)
        if not ok:
            return 0.0
        return 10 ** root
    
    def find_phm(self, freq, vout):
        """
        Phase margin at the unity-gain frequency.
        """
        ugbw = self.find_ugbw(freq, vout)
        if ugbw == 0.0:
            return 0.0  # no unity-gain crossing: no phase margin

        freq = np.asarray(freq, dtype=float)
        vout = np.asarray(vout)

        real_at_ugbw = np.interp(ugbw, freq, vout.real)
        imag_at_ugbw = np.interp(ugbw, freq, vout.imag)
        vout_at_ugbw = real_at_ugbw + 1j * imag_at_ugbw
        phase_at_ugbw = np.angle(vout_at_ugbw, deg=True)
        return 180 + phase_at_ugbw
    
    def find_slew_rate(self, time, signal, threshold_low=0.1, threshold_high=0.9, time_unit='us'):
        """Max slew rate (V per time_unit) over all rising and falling edges. `time` is in seconds."""
        t = np.asarray(time, dtype=float)
        v = np.asarray(signal, dtype=float)
        if t.size < 4 or t.shape != v.shape:
            return 0.0

        vmin, vmax = v.min(), v.max()
        if vmax <= vmin:
            return 0.0
        v10 = vmin + threshold_low * (vmax - vmin)
        v90 = vmin + threshold_high * (vmax - vmin)

        # work in time_unit so brentq's absolute tolerance isn't too coarse
        factor = {'s': 1, 'ms': 1e-3, 'us': 1e-6, 'ns': 1e-9, 'ps': 1e-12}[time_unit.lower()]
        t = t / factor

        # every crossing of the 10% / 90% levels as (time, level_name, rising)
        events = []
        for i in range(len(v) - 1):
            for name, level in (('low', v10), ('high', v90)):
                a, b = v[i], v[i + 1]
                if (a < level <= b) or (a > level >= b):
                    lo = min(max(i - 1, 0), len(t) - 4)
                    tc, ok = self._get_best_crossing(t[lo:lo + 4], v[lo:lo + 4], level)
                    if ok and t[i] <= tc <= t[i + 1]:
                        events.append((tc, name, b > a))
        events.sort()

        rates = []
        for (t1, n1, up1), (t2, n2, up2) in zip(events, events[1:]):
            rising_edge = up1 and up2 and n1 == 'low' and n2 == 'high'
            falling_edge = (not up1) and (not up2) and n1 == 'high' and n2 == 'low'
            if (rising_edge or falling_edge) and t2 > t1:
                rates.append((v90 - v10) / (t2 - t1))

        return max(rates) if rates else 0.0

    def _get_best_crossing(cls, xvec, yvec, val):
        interp_fun = interp.InterpolatedUnivariateSpline(xvec, yvec)

        def fzero(x):
            return interp_fun(x) - val

        xstart, xstop = xvec[0], xvec[-1]
        try:
            return sciopt.brentq(fzero, xstart, xstop), True
        except ValueError:
            return xstop, False