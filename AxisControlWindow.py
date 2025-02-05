"""
===================================================
Created on: 22-7-2024
Author: Chang Xu
File: AxisControlWindow.py
Version: 1.1
Language: Python 3.12.3
Description:
This script defines a GUI-based control interface
for configuring axis settings on a Keysight oscilloscope.
It allows users to adjust timebase, channel parameters,
and markers interactively.
===================================================
"""


import tkinter as tk
from tkinter import messagebox, scrolledtext
import json


class AxisControlPage(tk.Frame):
    def __init__(self, master, oscilloscope, config_file='axis_config.json'):
        super().__init__(master)
        self.oscilloscope = oscilloscope
        self.config_file = config_file
        self.pack(fill=tk.BOTH, expand=True)

        # Create a console output box
        self.console_output = scrolledtext.ScrolledText(self, width=50, height=10, wrap=tk.WORD, bg="black", fg="white")
        self.console_output.grid(row=0, column=0, columnspan=5, padx=10, pady=10)

        # Retrieve active channels
        # Check oscilloscope connection status
        try:
            self.active_channels = self.oscilloscope.get_active_channels()
            if not self.active_channels:
                raise ValueError("No active channels detected.")  # Raise an exception if no valid channels are detected
        except Exception as e:
            # Handle cases where the oscilloscope is not connected or has no active channels
            self.console_output.insert(tk.END,
                                       f"Warning: Oscilloscope not connected or no active channels. Default settings will be used.\n")
            self.active_channels = [3]  # Retrieve default channels list

        # Create the timebase control module
        self.create_timebase_controls()

        # Create control modules for each channel
        self.create_channel_controls()

        # Create marker control modules
        self.create_marker_controls()

        # Apply button
        tk.Button(self, text="Apply Settings", command=self.apply_settings).grid(row=14, column=0, columnspan=5, pady=20)

        # Try to load previously saved settings
        self.load_settings()

    def create_timebase_controls(self):
        tk.Label(self, text="Timebase (X Axis)").grid(row=1, column=0, padx=10, pady=5, columnspan=5)

        self.x_scale_var = tk.DoubleVar(value=1.0)
        tk.Label(self, text="Scale (s/div)").grid(row=2, column=0, padx=20)
        tk.Entry(self, textvariable=self.x_scale_var).grid(row=3, column=0, padx=20)

        self.x_pos_var = tk.DoubleVar(value=0.0)
        tk.Label(self, text="Position (s)").grid(row=2, column=1, padx=20)
        tk.Entry(self, textvariable=self.x_pos_var).grid(row=3, column=1, padx=20)

    def create_channel_controls(self):
        for channel in range(1, 5):  # Assume the oscilloscope has 4 channels
            col = channel - 1        # Place each channel in a separate column
            tk.Label(self, text=f"Channel {channel}").grid(row=4, column=col, padx=10, pady=5)

            # Y-axis control
            y_scale_var = tk.DoubleVar(value=1.0)
            tk.Label(self, text="Scale (V/div)").grid(row=5, column=col, padx=20)
            tk.Entry(self, textvariable=y_scale_var).grid(row=6, column=col, padx=20)

            y_pos_var = tk.DoubleVar(value=0.0)
            tk.Label(self, text="Position (V)").grid(row=7, column=col, padx=20)
            tk.Entry(self, textvariable=y_pos_var).grid(row=8, column=col, padx=20)

            # Store variables in the instance for later use
            setattr(self, f'y_scale_var_{channel}', y_scale_var)
            setattr(self, f'y_pos_var_{channel}', y_pos_var)

            # Disable input fields if the channel is not active
            if channel not in self.active_channels:
                getattr(self, f'y_scale_var_{channel}').set(0.0)
                getattr(self, f'y_pos_var_{channel}').set(0.0)

    def create_marker_controls(self):
        tk.Label(self, text="Markers").grid(row=9, column=0, padx=10, pady=5, columnspan=5)

        # Input the number of markers to be added
        self.marker_count_var = tk.IntVar(value=2)  # Default to 2 markers
        tk.Label(self, text="Number of Markers (1 or 2)").grid(row=10, column=0, padx=20, columnspan=5)
        tk.Entry(self, textvariable=self.marker_count_var).grid(row=11, column=0, padx=20, columnspan=5)

        # Add input fields for markers
        self.marker_entries = []

        # Create input fields for two markers
        for i in range(1, 3):
            x_marker_var = tk.DoubleVar(value=0.0)
            tk.Label(self, text=f"X Marker {i} Position (s)").grid(row=12, column=(i - 1) * 2, padx=20)
            tk.Entry(self, textvariable=x_marker_var).grid(row=13, column=(i - 1) * 2, padx=20)
            self.marker_entries.append(x_marker_var)

            y_marker_var = tk.DoubleVar(value=0.0)
            tk.Label(self, text=f"Y Marker {i} Position (V)").grid(row=12, column=(i - 1) * 2 + 1, padx=20)
            tk.Entry(self, textvariable=y_marker_var).grid(row=13, column=(i - 1) * 2 + 1, padx=20)
            self.marker_entries.append(y_marker_var)

    def apply_settings(self):
        try:
            if self.oscilloscope:
                # Set Y-axis (voltage scale)
                for channel in range(1, 5):
                    y_scale_var = getattr(self, f'y_scale_var_{channel}')
                    y_pos_var = getattr(self, f'y_pos_var_{channel}')
                    if channel in self.active_channels:
                        self.oscilloscope.set_channel_scale(channel, y_scale_var.get())
                        self.oscilloscope.set_channel_position(channel, y_pos_var.get())
                        self.console_output.insert(tk.END, f"Channel {channel} settings applied.\n")
                    else:
                        self.console_output.insert(tk.END, f"Channel {channel} is not active.\n")

                # Configure markers
                marker_count = self.marker_count_var.get()
                if marker_count >= 1:
                    x1_marker_var = self.marker_entries[0]
                    y1_marker_var = self.marker_entries[1]
                    self.oscilloscope.add_marker_x1(x1_marker_var.get())
                    self.oscilloscope.add_marker_y1(y1_marker_var.get())
                    self.console_output.insert(tk.END, f"Marker 1 settings applied.\n")
                if marker_count == 2:
                    x2_marker_var = self.marker_entries[2]
                    y2_marker_var = self.marker_entries[3]
                    self.oscilloscope.add_marker_x2(x2_marker_var.get())
                    self.oscilloscope.add_marker_y2(y2_marker_var.get())
                    self.console_output.insert(tk.END, f"Marker 2 settings applied.\n")

                # Save settings after successful application
                self.save_settings()
                self.console_output.insert(tk.END, "Settings saved successfully.\n")

                messagebox.showinfo("Success", "Axis settings and markers have been applied successfully.")
            else:
                messagebox.showerror("Error", "Oscilloscope is not connected.")
        except Exception as e:
            self.console_output.insert(tk.END, f"Error: {e}\n")
            messagebox.showerror("Error", f"Failed to apply settings: {e}")

    def save_settings(self):
        settings = {
            "timebase": {
                "scale": self.x_scale_var.get(),
                "position": self.x_pos_var.get()
            },
            "channel_settings": {},
            "marker_positions": []
        }

        for channel in range(1, 5):
            y_scale_var = getattr(self, f'y_scale_var_{channel}').get()
            y_pos_var = getattr(self, f'y_pos_var_{channel}').get()
            settings["channel_settings"][f'channel_{channel}'] = {
                "scale": y_scale_var,
                "position": y_pos_var
            }

        # Save marker positions
        marker_count = self.marker_count_var.get()
        for i in range(marker_count):
            x_marker_var = self.marker_entries[i * 2].get()
            y_marker_var = self.marker_entries[i * 2 + 1].get()
            settings["marker_positions"].append({"x": x_marker_var, "y": y_marker_var})

        with open(self.config_file, 'w') as f:
            json.dump(settings, f, indent=4)
    def load_settings(self):
        try:
            with open(self.config_file, 'r') as f:
                settings = json.load(f)

            # Load timebase settings
            self.x_scale_var.set(settings["timebase"]["scale"])
            self.x_pos_var.set(settings["timebase"]["position"])

            for channel in range(1, 5):
                if f'channel_{channel}' in settings["channel_settings"]:
                    y_scale_var = settings["channel_settings"][f'channel_{channel}']["scale"]
                    y_pos_var = settings["channel_settings"][f'channel_{channel}']["position"]
                    getattr(self, f'y_scale_var_{channel}').set(y_scale_var)
                    getattr(self, f'y_pos_var_{channel}').set(y_pos_var)

            # Load marker positions
            marker_count = len(settings["marker_positions"])
            self.marker_count_var.set(marker_count)
            for i in range(marker_count):
                x_marker_var = settings["marker_positions"][i]["x"]
                y_marker_var = settings["marker_positions"][i]["y"]
                self.marker_entries[i * 2].set(x_marker_var)
                self.marker_entries[i * 2 + 1].set(y_marker_var)
            self.console_output.insert(tk.END, "Settings loaded successfully.\n")
        except FileNotFoundError:
            self.console_output.insert(tk.END, "No saved settings found.\n")
        except Exception as e:
            self.console_output.insert(tk.END, f"Failed to load settings: {e}\n")
