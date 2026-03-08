"""
Utilities for waveform measurements and export helpers.
"""

import csv
from collections import OrderedDict


CHANNEL_MEASUREMENTS = [
    {"name": "Vpp", "method": "measure_vpp", "unit": "V"},
    {"name": "Vmin", "method": "measure_vmin", "unit": "V"},
    {"name": "Vmax", "method": "measure_vmax", "unit": "V"},
    {"name": "Frequency", "method": "measure_frequency", "unit": "Hz"},
    {"name": "Period", "method": "measure_period", "unit": "s"},
    {"name": "Pulse Width", "method": "measure_pulse_width", "unit": "s"},
    {"name": "Fall Time", "method": "measure_fall_time", "unit": "s"},
    {"name": "Rise Time", "method": "measure_rise_time", "unit": "s"},
    {"name": "Duty Cycle", "method": "measure_duty_cycle", "unit": "%"},
    {"name": "RMS Voltage", "method": "measure_rms_voltage", "unit": "V"},
    {"name": "Average Voltage", "method": "measure_average_voltage", "unit": "V"},
    {"name": "Amplitude", "method": "measure_amplitude", "unit": "V"},
    {"name": "Overshoot", "method": "measure_overshoot", "unit": "%"},
    {"name": "Preshoot", "method": "measure_preshoot", "unit": "%"},
    {"name": "Edge Count", "method": "measure_edge_count", "unit": ""},
    {"name": "Positive Edges", "method": "measure_pos_edge_count", "unit": ""},
    {"name": "Negative Pulses", "method": "measure_n_pulses", "unit": ""},
    {"name": "Positive Pulses", "method": "measure_p_pulses", "unit": ""},
    {"name": "XMin", "method": "measure_xmin", "unit": ""},
    {"name": "XMax", "method": "measure_xmax", "unit": ""},
    {"name": "VTop", "method": "measure_vtop", "unit": "V"},
    {"name": "VBase", "method": "measure_vbase", "unit": "V"},
    {"name": "VRatio", "method": "measure_vratio", "unit": "dB"},
]

SHARED_MEASUREMENTS = [
    {"name": "Phase", "method": "measure_phase", "unit": "degrees"},
]

ALL_MEASUREMENTS = CHANNEL_MEASUREMENTS + SHARED_MEASUREMENTS

MEASUREMENT_UNITS = {
    spec["name"]: spec["unit"]
    for spec in ALL_MEASUREMENTS
}


def get_measurement_names():
    return [spec["name"] for spec in ALL_MEASUREMENTS]


def get_selected_measurement_headers(selected_measurements):
    return [
        spec["name"]
        for spec in ALL_MEASUREMENTS
        if selected_measurements.get(spec["name"])
    ]


def collect_channel_measurements(measure, selected_measurements, channel):
    results = OrderedDict()
    for spec in CHANNEL_MEASUREMENTS:
        if selected_measurements.get(spec["name"]):
            method = getattr(measure, spec["method"])
            results[spec["name"]] = method(channel)
    return results


def collect_shared_measurements(measure, selected_measurements, channel_1, channel_2):
    results = OrderedDict()
    for spec in SHARED_MEASUREMENTS:
        if selected_measurements.get(spec["name"]):
            method = getattr(measure, spec["method"])
            results[spec["name"]] = method(channel_1, channel_2)
    return results


def format_channel_measurement_lines(channel, measurements):
    lines = []
    for name, value in measurements.items():
        unit = MEASUREMENT_UNITS.get(name, "")
        suffix = f" {unit}" if unit else ""
        lines.append(f"Channel {channel} - {name}: {value}{suffix}")
    return lines


def format_shared_measurement_lines(shared_measurements, channel_1, channel_2):
    lines = []
    for name, value in shared_measurements.items():
        unit = MEASUREMENT_UNITS.get(name, "")
        suffix = f" {unit}" if unit else ""
        lines.append(
            f"{name} between Channel {channel_1} and {channel_2}: {value}{suffix}"
        )
    return lines


def build_measurement_row(channel, selected_measurements, channel_measurements, shared_measurements):
    row = [f"Channel {channel}"]
    for name in get_selected_measurement_headers(selected_measurements):
        if name in channel_measurements:
            row.append(channel_measurements[name])
        else:
            row.append(shared_measurements.get(name))
    return row


def write_waveforms_to_csv(csv_path, waveforms):
    if not waveforms:
        raise ValueError("No waveform data available for export.")

    ordered_channels = sorted(waveforms)
    time_axis = waveforms[ordered_channels[0]][0]
    max_samples = max(len(waveform_data) for _, waveform_data in waveforms.values())

    with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        header = ["Time (s)"] + [
            f"Channel {channel} Amplitude (V)"
            for channel in ordered_channels
        ]
        writer.writerow(header)

        for index in range(max_samples):
            row = [time_axis[index] if index < len(time_axis) else ""]
            for channel in ordered_channels:
                _, waveform_data = waveforms[channel]
                row.append(waveform_data[index] if index < len(waveform_data) else "")
            writer.writerow(row)
