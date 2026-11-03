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

        # np.angle jumps from -180 to +180 degrees; unwrap removes those jumps so the phase keeps falling
        # (without it an unstable amp with phase -235 deg would get PM = 180 + 125 = 305 deg)
        phase = np.degrees(np.unwrap(np.angle(vout)))
        # read the phase at the UGBW on a log-frequency axis, like the logarithmic AC sweep and find_ugbw
        phase_at_ugbw = np.interp(np.log10(ugbw), np.log10(freq), phase)
        return 180.0 + phase_at_ugbw

    def find_slew_rate(self, time, signal, threshold_low=0.1, threshold_high=0.9, time_unit='us'):
        """
        Slew rate: speed of the output between 10 % and 90 % of its swing, on the first rising and the
        first falling edge. Returns the slowest of the two (the spec must hold in both directions),
        in V/us (time_unit='us') or V/s ('s'). Both edges are kept in self.slew_rate_rise and
        self.slew_rate_fall. Never raises: too few samples, mismatched arrays or a flat output give 0.0.
        """
        time = np.asarray(time, dtype=float)
        signal = np.asarray(signal, dtype=float)
        self.slew_rate_rise, self.slew_rate_fall = 0.0, 0.0
        if time.size < 4 or time.shape != signal.shape:
            return 0.0
        v_low, v_high = np.min(signal), np.max(signal)
        if v_high <= v_low:
            return 0.0  # flat (railed) output: no edge
        v_10 = v_low + threshold_low * (v_high - v_low)
        v_90 = v_low + threshold_high * (v_high - v_low)

        t_rise_10 = self._first_crossing_time(time, signal, v_10, rising=True)
        t_rise_90 = self._first_crossing_time(time, signal, v_90, rising=True, after=t_rise_10)
        t_fall_90 = self._first_crossing_time(time, signal, v_90, rising=False)
        t_fall_10 = self._first_crossing_time(time, signal, v_10, rising=False, after=t_fall_90)

        # an edge that never gets from 10 % to 90 % (or back) has no slew rate: 0, a failing spec
        sr_rise, sr_fall = 0.0, 0.0
        if t_rise_10 is not None and t_rise_90 is not None and t_rise_90 > t_rise_10:
            sr_rise = (v_90 - v_10) / (t_rise_90 - t_rise_10)
        if t_fall_90 is not None and t_fall_10 is not None and t_fall_10 > t_fall_90:
            sr_fall = (v_90 - v_10) / (t_fall_10 - t_fall_90)

        to_time_unit = {'s': 1.0, 'us': 1e-6}[time_unit]  # V/s -> V/us
        self.slew_rate_rise = sr_rise * to_time_unit
        self.slew_rate_fall = sr_fall * to_time_unit
        return min(self.slew_rate_rise, self.slew_rate_fall)

    def _first_crossing_time(self, time, signal, level, rising, after=None):
        """
        First time (after `after`, if given) at which signal crosses `level` upwards (rising=True) or
        downwards (rising=False), linearly interpolated between the two samples. None if it never does.
        """
        for i in range(len(signal) - 1):
            if after is not None and time[i + 1] <= after:
                continue
            if rising and signal[i] < level <= signal[i + 1]:
                return np.interp(level, [signal[i], signal[i + 1]], [time[i], time[i + 1]])
            if not rising and signal[i] > level >= signal[i + 1]:
                return np.interp(level, [signal[i + 1], signal[i]], [time[i + 1], time[i]])
        return None

    def _get_best_crossing(cls, xvec, yvec, val):
        interp_fun = interp.InterpolatedUnivariateSpline(xvec, yvec)

        def fzero(x):
            return interp_fun(x) - val

        xstart, xstop = xvec[0], xvec[-1]
        try:
            return sciopt.brentq(fzero, xstart, xstop), True
        except ValueError:
            return xstop, False