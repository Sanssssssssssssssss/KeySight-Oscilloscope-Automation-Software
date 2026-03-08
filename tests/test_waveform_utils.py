import csv
import os
import tempfile
import unittest

from waveform_utils import (
    build_measurement_row,
    collect_channel_measurements,
    get_selected_measurement_headers,
    write_waveforms_to_csv,
)


class FakeMeasure:
    def __init__(self):
        self.calls = []

    def measure_vpp(self, channel):
        self.calls.append(("measure_vpp", channel))
        return channel * 10

    def measure_period(self, channel):
        self.calls.append(("measure_period", channel))
        return channel * 0.5

    def measure_phase(self, channel_1, channel_2):
        self.calls.append(("measure_phase", channel_1, channel_2))
        return 90.0


class WaveformUtilsTests(unittest.TestCase):
    def test_selected_headers_preserve_supported_order(self):
        selected_measurements = {
            "Phase": 1,
            "Period": 1,
            "Vpp": 1,
        }

        headers = get_selected_measurement_headers(selected_measurements)

        self.assertEqual(headers, ["Vpp", "Period", "Phase"])

    def test_collect_channel_measurements_only_invokes_selected_methods(self):
        measure = FakeMeasure()
        selected_measurements = {
            "Vpp": 1,
            "Period": 1,
            "Phase": 1,
        }

        result = collect_channel_measurements(measure, selected_measurements, 3)

        self.assertEqual(result, {"Vpp": 30, "Period": 1.5})
        self.assertEqual(
            measure.calls,
            [("measure_vpp", 3), ("measure_period", 3)],
        )

    def test_build_measurement_row_merges_channel_and_shared_values(self):
        selected_measurements = {
            "Vpp": 1,
            "Phase": 1,
        }

        row = build_measurement_row(
            2,
            selected_measurements,
            {"Vpp": 12.3},
            {"Phase": 45.0},
        )

        self.assertEqual(row, ["Channel 2", 12.3, 45.0])

    def test_write_waveforms_to_csv_exports_multiple_channels(self):
        waveforms = {
            1: ([0.0, 0.1], [1.0, 1.1]),
            3: ([0.0, 0.1], [3.0, 3.1]),
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = os.path.join(temp_dir, "waveform.csv")
            write_waveforms_to_csv(csv_path, waveforms)
            with open(csv_path, newline="", encoding="utf-8") as csv_file:
                rows = list(csv.reader(csv_file))

        self.assertEqual(
            rows,
            [
                ["Time (s)", "Channel 1 Amplitude (V)", "Channel 3 Amplitude (V)"],
                ["0.0", "1.0", "3.0"],
                ["0.1", "1.1", "3.1"],
            ],
        )


if __name__ == "__main__":
    unittest.main()
