"""
===================================================
Created on: 21-7-2024
Author: Chang Xu
File: measure.py
Version: 1.7
Language: Python 3.12.3
Description:
This script provides measurement functionalities for
the Keysight oscilloscope automation system. It allows
users to execute various waveform measurements, send
commands, and retrieve real-time data from the oscilloscope.
===================================================
"""

import pyvisa
import time

class Measure:
    def __init__(self, scope):
        """Initialize the measurement class with an oscilloscope instance."""
        self.scope = scope

    def _setup_measurement(self, measurement_type, channel):
        """Set up the measurement type on a specific channel."""
        try:
            command = f":MEASure:{measurement_type} CHANnel{channel}"
            self.scope.write(command)
        except Exception as e:
            print(f"An error occurred while setting up {measurement_type} on channel {channel}: {e}")

    def measure(self, measurement_type, channel):
        """Execute a measurement and return the result."""
        # Set up the measurement type
        self._setup_measurement(measurement_type, channel)

        # Execute the measurement and retrieve the result
        command = f":MEASure:{measurement_type}? CHANnel{channel}"
        retries = 3  # Number of retries
        for i in range(retries):
            try:
                result = self.scope.query(command)
                return float(result)
            except pyvisa.errors.VisaIOError as e:
                if e.error_code == pyvisa.constants.VI_ERROR_TMO and i < retries - 1:
                    time.sleep(0.1)  # Wait 0.1s before retrying
                    continue
                else:
                    print(f"An error occurred while measuring {measurement_type} on channel {channel}: {e}")
                    return None
            except ValueError:
                print(f"Error converting measurement result to float: {result}")
                return None

    # Basic Measurements
    def measure_vpp(self, channel):
        """Measure peak-to-peak voltage."""
        return self.measure("VPP", channel)

    def measure_vmin(self, channel):
        """Measure minimum voltage."""
        return self.measure("VMIN", channel)

    def measure_vmax(self, channel):
        """Measure maximum voltage."""
        return self.measure("VMAX", channel)

    def measure_frequency(self, channel):
        """Measure signal frequency."""
        return self.measure("FREQuency", channel)

    def measure_period(self, channel):
        """Measure signal period."""
        return self.measure("PERiod", channel)

    def measure_pulse_width(self, channel):
        """Measure pulse width."""
        return self.measure("PWIDth", channel)

    def measure_duty_cycle(self, channel):
        """Measure duty cycle percentage."""
        return self.measure("DUTYcycle", channel)

    def measure_rms_voltage(self, channel):
        """Measure root mean square (RMS) voltage."""
        return self.measure("VRMS", channel)

    def measure_average_voltage(self, channel):
        """Measure average voltage."""
        return self.measure("VAVerage", channel)

    def measure_rise_time(self, channel):
        """Measure signal rise time."""
        return self.measure("RISetime", channel)

    def measure_fall_time(self, channel):
        """Measure signal fall time."""
        return self.measure("FALLtime", channel)

    def measure_n_edges(self, channel):
        """Measure the number of negative edges."""
        return self.measure("NEDGes", channel)

    def measure_p_edges(self, channel):
        """Measure the number of positive edges."""
        return self.measure("PEDGes", channel)

    # Advanced Measurements
    def measure_mean_voltage(self, channel):
        """Measure mean voltage."""
        return self.measure("MEAN", channel)

    def measure_std_deviation(self, channel):
        """Measure standard deviation of voltage."""
        return self.measure("SDEViation", channel)

    def measure_edge_count(self, channel):
        """Measure total edge count."""
        return self.measure("NEDGes", channel)

    def measure_pos_edge_count(self, channel):
        """Measure positive edge count."""
        return self.measure("PEDGes", channel)

    def measure_width_pos(self, channel):
        """Measure positive pulse width."""
        return self.measure("NWIDth", channel)

    def measure_width_neg(self, channel):
        """Measure negative pulse width."""
        return self.measure("NWIDth", channel)

    def measure_bit_rate(self, channel):
        """Measure bit rate of the signal."""
        return self.measure("BRATe", channel)

    def measure_bandwidth(self, channel):
        """Measure signal bandwidth."""
        return self.measure("BWIDth", channel)

    def measure_phase(self, channel, ref_channel):
        """Measure phase difference between the given channel and a reference channel."""
        command = f":MEASure:PHASe? CHANnel{channel},CHANnel{ref_channel}"
        return float(self.scope.query(command))

    def measure_amplitude(self, channel):
        """Measure signal amplitude."""
        return self.measure("VAMPlitude", channel)

    def measure_overshoot(self, channel):
        """Measure signal overshoot percentage."""
        return self.measure("OVERshoot", channel)

    def measure_preshoot(self, channel):
        """Measure signal preshoot percentage."""
        return self.measure("PREShoot", channel)

    def measure_n_pulses(self, channel):
        """Measure the number of negative pulses."""
        return self.measure("NPULses", channel)

    def measure_p_pulses(self, channel):
        """Measure the number of positive pulses."""
        return self.measure("PPULses", channel)

    def measure_xmin(self, channel):
        """Measure the minimum X-axis value."""
        return self.measure("XMIN", channel)

    def measure_xmax(self, channel):
        """Measure the maximum X-axis value."""
        return self.measure("XMAX", channel)

    def measure_vtop(self, channel):
        """Measure the top voltage level."""
        return self.measure("VTOP", channel)

    def measure_vbase(self, channel):
        """Measure the base voltage level."""
        return self.measure("VBASe", channel)

    def measure_vratio(self, channel):
        """Measure the voltage ratio."""
        return self.measure("VRATio", channel)


# # Test script for validating measurements
# def main():
#     rm = pyvisa.ResourceManager()
#     oscilloscope = rm.open_resource("USB0::0x0957::0x1780::MY55310270::0::INSTR")
#     measure = Measure(oscilloscope)
#
#     test_channel = 3
#     ref_channel = 2  # Reference channel for dual-channel measurements
#
#     measurement_tests = [
#         ("Vpp", measure.measure_vpp),
#         ("Vmin", measure.measure_vmin),
#         ("Vmax", measure.measure_vmax),
#         ("Frequency", measure.measure_frequency),
#         ("Period", measure.measure_period),
#         ("Pulse Width", measure.measure_pulse_width),
#         ("Duty Cycle", measure.measure_duty_cycle),
#         ("RMS Voltage", measure.measure_rms_voltage),
#         ("Average Voltage", measure.measure_average_voltage),
#         ("Rise Time", measure.measure_rise_time),
#         ("Fall Time", measure.measure_fall_time),
#         ("Amplitude", measure.measure_amplitude),
#         ("Overshoot", measure.measure_overshoot),
#         ("Preshoot", measure.measure_preshoot),
#         ("Negative Edges", measure.measure_n_edges),
#         ("Positive Edges", measure.measure_p_edges),
#         ("Negative Pulses", measure.measure_n_pulses),
#         ("Positive Pulses", measure.measure_p_pulses),
#         ("XMin", measure.measure_xmin),
#         ("XMax", measure.measure_xmax),
#         ("VTop", measure.measure_vtop),
#         ("VBase", measure.measure_vbase),
#         ("VRatio", measure.measure_vratio),
#         ("Standard Deviation", measure.measure_std_deviation),
#         ("Bit Rate", measure.measure_bit_rate),
#         ("Bandwidth", measure.measure_bandwidth),
#         ("Phase", lambda ch: measure.measure_phase(ch, ref_channel)),
#     ]
#
#     for name, func in measurement_tests:
#         try:
#             result = func(test_channel)
#             if result is not None:
#                 print(f"{name} for Channel {test_channel}: {result}")
#             else:
#                 print(f"{name} for Channel {test_channel} returned no result.")
#         except Exception as e:
#             print(f"Error testing {name}: {e}")
#
#
# if __name__ == "__main__":
#     main()
