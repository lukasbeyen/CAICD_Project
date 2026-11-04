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
        # returns None for a failed simulation (output files missing, empty, too short or NaN), like NgspiceWrapper does
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
        # VDD of this simulation: the netlist's .param VDD, or the vdd passed to create_new_netlist (env's pvt_corner)
        spec_dict['slewRate'] = self.find_slew_rate(self.time, self.vout_tran, threshold_low=0.1, threshold_high=0.9,
                                                    time_unit='us', vdd=float(self.VDD))
        spec_dict['ugbw'] = self.find_ugbw(self.freq, self.vout_complex)

        # a NaN or inf metric means the simulation data was broken: failed simulation
        for value in spec_dict.values():
            if not np.isfinite(value):
                return None
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
        try:
            tran_raw_outputs = np.genfromtxt(tran_fname, skip_header=1)
            ac_raw_outputs = np.genfromtxt(ac_fname, skip_header=1)
            dc_raw_outputs = np.genfromtxt(dc_fname, skip_header=1)
            noise_raw_outputs = np.genfromtxt(noise_fname, skip_header=1)
        except ValueError:
            print("output files could not be read")
            return False
        # expected layout (see the wrdata lines in TwoStage.cir): tran = rows of (time, vout),
        # ac = rows of (freq, real, imag), dc = one row (v(net4), i(vdd)), noise = one row (onoise_total twice)
        if (tran_raw_outputs.ndim != 2 or tran_raw_outputs.shape[0] < 2
                or ac_raw_outputs.ndim != 2 or ac_raw_outputs.shape[0] < 2 or ac_raw_outputs.shape[1] < 3
                or dc_raw_outputs.size < 2 or noise_raw_outputs.size < 1):
            print("output files are too short")
            return False

        self.time = tran_raw_outputs[:, 0]
        self.vout_tran = tran_raw_outputs[:, 1]
        
        self.freq = ac_raw_outputs[:, 0]
        vout_real = ac_raw_outputs[:, 1]
        vout_imag = ac_raw_outputs[:, 2]
        self.vout_complex = vout_real + 1j*vout_imag
        
        self.current = - dc_raw_outputs[1]

        self.noise = noise_raw_outputs[0]

        for data in [self.time, self.vout_tran, self.freq, self.vout_complex, self.current, self.noise]:
            if not np.all(np.isfinite(data)):
                print("output files contain NaN or inf")
                return False
        return True
    
    def find_dc_gain(self, vout):
        """
        DC gain in V/V (the unit of the spec in TwoStage.yaml): |vout| at the first AC point (1 Hz).
        The differential AC input is 1 V, so vout is the gain itself.
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
        if np.count_nonzero(mask) < 4:
            return 0.0  # the cubic spline in _get_best_crossing needs at least 4 points

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

    def find_slew_rate(self, time, signal, threshold_low=0.1, threshold_high=0.9, time_unit='us', vdd=None):
        """
        Slew rate of the RISING edge, as in the TAs' reference designs: speed of the output between 10 % and 90 %
        of its swing on the first rising edge, with the crossing times linearly interpolated between the two
        samples around them (the same as ngspice's meas). In V/us (time_unit='us') or V/s ('s'), also kept in
        self.slew_rate_rise. Never raises: too few samples, mismatched arrays or a flat output give 0.0.
        The 90 % level is capped at threshold_high * vdd (vdd = supply voltage in V, required): a glitch or
        overshoot above the real swing would otherwise push the 90 % level up. The levels used are kept in
        self.slew_rate_v10 and self.slew_rate_v90.
        """
        if vdd is None:
            raise ValueError('find_slew_rate needs vdd (the supply voltage of the simulation) to cap the 90 % level')
        time = np.asarray(time, dtype=float)
        signal = np.asarray(signal, dtype=float)
        self.slew_rate_rise = 0.0
        self.slew_rate_v10, self.slew_rate_v90 = None, None
        if time.size < 4 or time.shape != signal.shape:
            return 0.0
        v_low, v_high = np.min(signal), np.max(signal)
        if v_high <= v_low:
            return 0.0  # flat (railed) output: no edge
        v_10 = v_low + threshold_low * (v_high - v_low)
        v_90 = v_low + threshold_high * (v_high - v_low)
        # hard limit: a glitch above the real swing must not move the 90 % level above threshold_high * VDD
        v_90 = min(v_90, threshold_high * vdd)
        self.slew_rate_v10, self.slew_rate_v90 = v_10, v_90
        if v_90 <= v_10:
            return 0.0  # degenerate swing (e.g. the whole output sits above the cap): no edge

        t_10 = self._first_rising_crossing(time, signal, v_10)
        t_90 = self._first_rising_crossing(time, signal, v_90, after=t_10)
        if t_10 is None or t_90 is None or t_90 <= t_10:
            return 0.0  # the output never gets from 10 % to 90 %: no slew rate, a failing spec

        to_time_unit = {'s': 1.0, 'us': 1e-6}[time_unit]  # V/s -> V/us
        self.slew_rate_rise = (v_90 - v_10) / (t_90 - t_10) * to_time_unit
        return self.slew_rate_rise

    def _first_rising_crossing(self, time, signal, level, after=None):
        """
        First time (after `after`, if given) at which signal crosses `level` upwards, linearly interpolated
        between the two samples around the crossing. None if it never does.
        """
        for i in range(len(signal) - 1):
            if after is not None and time[i + 1] <= after:
                continue
            if signal[i] < level <= signal[i + 1]:
                return np.interp(level, [signal[i], signal[i + 1]], [time[i], time[i + 1]])
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