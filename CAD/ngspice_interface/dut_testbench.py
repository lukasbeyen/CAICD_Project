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
        spec_dict['slewRate'] = self.find_slew_rate(self.time, self.vout_tran, threshold_low=0.1, threshold_high=0.9, time_unit='us')
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

    def find_slew_rate(self, time, signal, threshold_low=0.1, threshold_high=0.9, time_unit='us'):
        """
        Slew rate: speed of the output between 10 % and 90 % of its swing, evaluated on EVERY rising and
        EVERY falling edge of the transient. Per direction the fastest edge is kept, then the slowest of
        the two directions is returned (the spec must hold in both directions), in V/us (time_unit='us')
        or V/s ('s'). Both per-direction values are kept in self.slew_rate_rise and self.slew_rate_fall,
        and every individual edge rate (in the requested unit) in self.slew_rate_rise_edges / _fall_edges.
        Crossing times are located with the spline root finder _get_best_crossing on a local window of
        samples, so a coarse time grid does not turn the chord between two samples into a too-small
        slew rate. Never raises: too few samples, mismatched arrays or a flat output give 0.0.
        """
        time = np.asarray(time, dtype=float)
        signal = np.asarray(signal, dtype=float)
        self.slew_rate_rise, self.slew_rate_fall = 0.0, 0.0
        self.slew_rate_rise_edges, self.slew_rate_fall_edges = [], []
        if time.size < 4 or time.shape != signal.shape:
            return 0.0
        v_low, v_high = np.min(signal), np.max(signal)
        if v_high <= v_low:
            return 0.0  # flat (railed) output: no edge
        v_10 = v_low + threshold_low * (v_high - v_low)
        v_90 = v_low + threshold_high * (v_high - v_low)
        dv = v_90 - v_10

        # rising edges: 10 % -> 90 %. Falling edges: mirror the signal, so a falling 90 % -> 10 % edge
        # becomes a rising edge between -v_90 and -v_10 and the same routine can be reused.
        rise_durations = self._edge_durations(time, signal, v_10, v_90)
        fall_durations = self._edge_durations(time, -signal, -v_90, -v_10)

        to_time_unit = {'s': 1.0, 'us': 1e-6}[time_unit]  # V/s -> V/us
        self.slew_rate_rise_edges = [dv / d * to_time_unit for d in rise_durations]
        self.slew_rate_fall_edges = [dv / d * to_time_unit for d in fall_durations]

        # fastest edge per direction (0.0 if the direction has no complete edge: a failing spec)
        self.slew_rate_rise = max(self.slew_rate_rise_edges) if self.slew_rate_rise_edges else 0.0
        self.slew_rate_fall = max(self.slew_rate_fall_edges) if self.slew_rate_fall_edges else 0.0
        # slowest of the two directions
        return min(self.slew_rate_rise, self.slew_rate_fall)

    def _edge_durations(self, time, signal, lo, hi):
        """
        Durations of all complete rising edges lo -> hi in the signal. An edge starts at the last upward
        crossing of `lo` before the signal reaches `hi`; if the signal drops back below `lo` before
        reaching `hi`, the attempt is discarded (no complete edge).
        """
        durations = []
        t_start = None
        for i in range(len(signal) - 1):
            s0, s1 = signal[i], signal[i + 1]
            if s0 < lo <= s1:                                  # upward crossing of lo: (re)start the edge
                t_start = self._crossing_time(time, signal, i, lo)
            elif s0 >= lo > s1:                                # fell back below lo: aborted edge
                t_start = None
            if t_start is not None and s0 < hi <= s1:          # upward crossing of hi: edge complete
                t_end = self._crossing_time(time, signal, i, hi)
                if t_end > t_start:
                    durations.append(t_end - t_start)
                t_start = None
        return durations

    def _crossing_time(self, time, signal, i, level):
        """
        Time at which `signal` reaches `level` inside the sample interval i -> i+1 (known to bracket it
        upwards). Uses _get_best_crossing on the 4 samples around the interval, with the time axis
        normalised to u = (t - t_i) / (t_i+1 - t_i) so brentq's absolute xtol does not depend on the
        time scale. Falls back to linear interpolation if the window is unusable (time not strictly
        increasing, window end points do not bracket the level, root outside the interval).
        """
        t0, t1 = time[i], time[i + 1]
        linear = np.interp(level, [signal[i], signal[i + 1]], [t0, t1])
        if signal.size < 4 or not t1 > t0:
            return linear
        a = min(max(i - 1, 0), signal.size - 4)    # window a..a+3 always contains i and i+1
        t_win = time[a:a + 4]
        if not np.all(np.diff(t_win) > 0):
            return linear
        u_win = (t_win - t0) / (t1 - t0)
        try:
            u, ok = self._get_best_crossing(u_win, signal[a:a + 4], level)
        except ValueError:
            return linear
        if not ok or not 0.0 <= u <= 1.0:
            return linear
        return t0 + u * (t1 - t0)

    def _get_best_crossing(cls, xvec, yvec, val):
        interp_fun = interp.InterpolatedUnivariateSpline(xvec, yvec)

        def fzero(x):
            return interp_fun(x) - val

        xstart, xstop = xvec[0], xvec[-1]
        try:
            return sciopt.brentq(fzero, xstart, xstop), True
        except ValueError:
            return xstop, False