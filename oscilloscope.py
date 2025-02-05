"""
===================================================
Created on: 24-7-2024
Author: Chang Xu
File: oscilloscope.py
Version: 2.4
Language: Python 3.12.3
Description:
This script defines an oscilloscope control interface
for interacting with a Keysight oscilloscope via VISA.
It includes functions for waveform capture, measurement,
marker placement, and configuration adjustments.
===================================================
"""

import pyvisa
import numpy as np
import matplotlib.pyplot as plt
import time
import io
from PIL import Image
from measure import Measure


class Oscilloscope:
    def __init__(self, visa_address, timeout=20000):
        """Initialize the oscilloscope connection."""
        self.rm = pyvisa.ResourceManager()
        self.visa_address = visa_address
        self.scope = self.rm.open_resource(self.visa_address)
        self.scope.timeout = timeout
        self.measure = Measure(self.scope)  # Initialize measurement class

        # Define colors for each channel
        self.channel_colors = ['yellow', 'green', 'blue', 'red']
        print(f"Initialized scope: {self.scope}")

    def write(self, command):
        """Send a command to the oscilloscope."""
        self.scope.write(command)

    def get_idn(self):
        """Retrieve oscilloscope identification information."""
        return self.scope.query("*IDN?")

    def get_segment_count(self):
        """Get the number of waveform segments."""
        return int(self.scope.query(":WAVeform:SEGMented:COUNt?"))

    def set_segment_index(self, index):
        """Set the active waveform segment index."""
        self.scope.write(f":ACQuire:SEGMented:INDex {index}")

    def get_time_tag(self):
        """Retrieve the timestamp of the current waveform segment."""
        return float(self.scope.query(":WAVeform:SEGMented:TTAG?"))

    def query(self, command):
        """Send a query command and return the response."""
        return self.scope.query(command)

    def perform_measurements(self, channel):
        """Execute peak-to-peak voltage and frequency measurements."""
        vpp = self.measure.measure("VPP", channel)
        freq = self.measure.measure("FREQ", channel)
        return vpp, freq

    def get_active_channels(self):
        """Retrieve a list of currently active channels."""
        active_channels = []
        for channel in range(1, 5):  # Assuming the oscilloscope has 4 channels
            if int(self.scope.query(f":CHANnel{channel}:DISPlay?")):
                active_channels.append(channel)
        return active_channels

    def activate_channel(self, channel):
        """Activate a specific channel."""
        self.scope.write(f":CHANnel{channel}:DISPlay ON")

    def capture_screenshot(self, filename="screenshot.png"):
        """Capture a screenshot of the oscilloscope display and save it as a PNG file."""
        # Send command to acquire screenshot data
        self.scope.write(":DISPlay:DATA? PNG, COLOR")

        # Read the first two bytes to verify the data header
        raw_header = self.scope.read_bytes(2)
        if raw_header[0:1] != b'#':
            raise ValueError("Invalid data header")

        # Extract the length field size
        length_digits = int(raw_header[1:2])

        # Read the actual length of the data
        raw_length = self.scope.read_bytes(length_digits)
        data_length = int(raw_length.decode())

        # Read the image data in chunks
        image_data = b""
        bytes_remaining = data_length
        while bytes_remaining > 0:
            chunk_size = min(1024, bytes_remaining)  # Read 1KB per iteration
            chunk = self.scope.read_bytes(chunk_size)
            image_data += chunk
            bytes_remaining -= len(chunk)

        # Save the image file
        with open(filename, 'wb') as f:
            f.write(image_data)
        print(f"Screenshot saved as {filename}")

        # Display the image
        img = Image.open(io.BytesIO(image_data))
        img.show()

    def capture_waveform(self, channel=1):
        """Capture waveform data from the specified channel."""
        self.scope.write(f":WAV:SOUR CHAN{channel}")
        self.scope.write(":WAV:FORM ASCII")

        # Retrieve time axis information
        preamble = self.scope.query(":WAVeform:PREamble?").split(',')
        x_increment = float(preamble[4])  # Time interval
        x_origin = float(preamble[5])  # Start time
        x_reference = float(preamble[6])  # Time reference point

        # Get waveform data
        data = self.scope.query(":WAV:DATA?")

        # Process data, skipping the header
        waveform_data = np.array([float(val) for val in data.split(',') if val.strip() and not val.startswith("#")])

        # Generate time axis
        time_values = np.arange(0, len(waveform_data)) * x_increment + x_origin

        return time_values, waveform_data

    def capture_all_waveforms(self):
        """Capture waveforms from all active channels."""
        active_channels = []
        waveforms = {}

        # Assuming up to 4 channels
        for channel in range(1, 5):
            display_state = self.scope.query(f":CHANnel{channel}:DISPlay?")
            if int(display_state) == 1:  # If the channel is active
                active_channels.append(channel)
                time_values, waveform_data = self.capture_waveform(channel)
                waveforms[channel] = (time_values, waveform_data)

        return active_channels, waveforms

    def plot_waveform(self, time_values, waveform_data, channel, ax, canvas):
        """Plot a single waveform."""
        ax.clear()
        ax.plot(time_values, waveform_data, label=f"Channel {channel}", color='b')
        ax.set_title("Captured Waveform")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Amplitude (V)")
        ax.grid(True)
        ax.legend(loc="best")

        canvas.draw()

    def plot_all_waveforms(self, waveforms, ax, canvas):
        """Plot waveforms from all active channels."""
        ax.clear()

        # Plot each waveform
        for channel, (time_values, waveform_data) in waveforms.items():
            ax.plot(time_values, waveform_data, label=f"Channel {channel}", color=self.channel_colors[channel - 1])

        ax.set_title("Captured Waveforms")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Amplitude (V)")
        ax.grid(True)
        ax.legend(loc="best")

        canvas.draw()

    def set_timebase_scale(self, scale):
        """Set the timebase scale (seconds per division)."""
        try:
            self.scope.write(f":TIMebase:SCALe {scale}")
        except Exception as e:
            print(f"Failed to set timebase scale: {e}")

    def set_timebase_position(self, position):
        """Set the horizontal position of the timebase."""
        try:
            self.scope.write(f":TIMebase:POSition {position}")
        except Exception as e:
            print(f"Failed to set timebase position: {e}")

    def set_channel_scale(self, channel, scale):
        """Set the vertical scale of a specific channel."""
        try:
            self.scope.write(f":CHANnel{channel}:SCALe {scale}")
        except Exception as e:
            print(f"Failed to set channel {channel} scale: {e}")

    def set_channel_position(self, channel, position):
        """Set the vertical position of a specific channel."""
        try:
            self.scope.write(f":CHANnel{channel}:POSition {position}")
        except Exception as e:
            print(f"Failed to set channel {channel} position: {e}")

    def add_marker_x1(self, position):
        """Add a marker at position X1."""
        try:
            self.scope.write(f":MARKer:X1Position {position}")
        except Exception as e:
            print(f"Failed to add X1 marker: {e}")

    def add_marker_x2(self, position):
        """Add a marker at position X2."""
        try:
            self.scope.write(f":MARKer:X2Position {position}")
        except Exception as e:
            print(f"Failed to add X2 marker: {e}")

    def add_marker_y1(self, position):
        """Add a marker at position Y1."""
        try:
            self.scope.write(f":MARKer:Y1Position {position}")
        except Exception as e:
            print(f"Failed to add Y1 marker: {e}")

    def add_marker_y2(self, position):
        """Add a marker at position Y2."""
        try:
            self.scope.write(f":MARKer:Y2Position {position}")
        except Exception as e:
            print(f"Failed to add Y2 marker: {e}")

    def close(self):
        """Close the oscilloscope connection."""
        self.scope.close()
