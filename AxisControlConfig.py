"""
===================================================
Created on: 21-7-2024
Author: Chang Xu
File: AxisControlConfig.py
Version: 1.2
Language: Python 3.12.3
Description:
This script defines a GUI-based configuration panel
for axis control settings in a Keysight oscilloscope
automation system. It allows users to set and save
timebase, channel, and marker parameters.
===================================================
"""

import tkinter as tk
from tkinter import messagebox
import json


class AxisControlConfig:
    def __init__(self, master, config_file='axis_config.json'):
        self.master = master
        self.config_file = config_file

        # Initialize configuration
        self.config = {
            "timebase": {"scale": 1.0, "position": 0.0},
            "channels": {f"channel_{i}": {"scale": 1.0, "position": 0.0} for i in range(1, 5)},
            "markers": [{"x": 0.0, "y": 0.0}, {"x": 0.0, "y": 0.0}]
        }

        # Create UI elements
        self.create_ui()

    def create_ui(self):
        tk.Label(self.master, text="Timebase Settings:").grid(row=0, column=0, columnspan=2, pady=10)

        tk.Label(self.master, text="Scale (s/div):").grid(row=1, column=0, sticky='w')
        self.timebase_scale = tk.DoubleVar(value=self.config["timebase"]["scale"])
        tk.Entry(self.master, textvariable=self.timebase_scale).grid(row=1, column=1, padx=10, pady=5)

        tk.Label(self.master, text="Position (s):").grid(row=2, column=0, sticky='w')
        self.timebase_position = tk.DoubleVar(value=self.config["timebase"]["position"])
        tk.Entry(self.master, textvariable=self.timebase_position).grid(row=2, column=1, padx=10, pady=5)

        # Channel settings
        for i in range(1, 5):
            tk.Label(self.master, text=f"Channel {i} Settings:").grid(row=3 + (i - 1) * 3, column=0, columnspan=2,
                                                                      pady=10)

            tk.Label(self.master, text="Scale (V/div):").grid(row=4 + (i - 1) * 3, column=0, sticky='w')
            scale_var = tk.DoubleVar(value=self.config["channels"][f"channel_{i}"]["scale"])
            tk.Entry(self.master, textvariable=scale_var).grid(row=4 + (i - 1) * 3, column=1, padx=10, pady=5)
            setattr(self, f"channel_{i}_scale", scale_var)

            tk.Label(self.master, text="Position (V):").grid(row=5 + (i - 1) * 3, column=0, sticky='w')
            position_var = tk.DoubleVar(value=self.config["channels"][f"channel_{i}"]["position"])
            tk.Entry(self.master, textvariable=position_var).grid(row=5 + (i - 1) * 3, column=1, padx=10, pady=5)
            setattr(self, f"channel_{i}_position", position_var)

        # Marker settings
        tk.Label(self.master, text="Markers:").grid(row=15, column=0, columnspan=2, pady=10)
        for i in range(2):
            tk.Label(self.master, text=f"X Marker {i + 1} Position (s):").grid(row=16 + i * 2, column=0, sticky='w')
            x_marker_var = tk.DoubleVar(value=self.config["markers"][i]["x"])
            tk.Entry(self.master, textvariable=x_marker_var).grid(row=16 + i * 2, column=1, padx=10, pady=5)
            setattr(self, f"x_marker_{i + 1}", x_marker_var)

            tk.Label(self.master, text=f"Y Marker {i + 1} Position (V):").grid(row=17 + i * 2, column=0, sticky='w')
            y_marker_var = tk.DoubleVar(value=self.config["markers"][i]["y"])
            tk.Entry(self.master, textvariable=y_marker_var).grid(row=17 + i * 2, column=1, padx=10, pady=5)
            setattr(self, f"y_marker_{i + 1}", y_marker_var)

        # Save and load buttons
        tk.Button(self.master, text="Save Configuration", command=self.save_configuration).grid(row=21, column=0,
                                                                                                pady=10)
        tk.Button(self.master, text="Load Configuration", command=self.load_configuration).grid(row=21, column=1,
                                                                                                pady=10)

    def save_if_valid(self):
        """Save all variables"""
        try:
            self.save_to_json(".")
        except tk.TclError as e:
            print(f"Error: {e}")
            pass

    def save_to_json(self, directory):
        """Save the current configuration as a JSON file"""
        self.config["timebase"]["scale"] = self.timebase_scale.get()
        self.config["timebase"]["position"] = self.timebase_position.get()

        for i in range(1, 5):
            self.config["channels"][f"channel_{i}"]["scale"] = getattr(self, f"channel_{i}_scale").get()
            self.config["channels"][f"channel_{i}"]["position"] = getattr(self, f"channel_{i}_position").get()

        for i in range(2):
            self.config["markers"][i]["x"] = getattr(self, f"x_marker_{i + 1}").get()
            self.config["markers"][i]["y"] = getattr(self, f"y_marker_{i + 1}").get()

        filepath = f"{directory}/axis_config.json"
        with open(filepath, 'w') as f:
            json.dump(self.config, f, indent=4)

        messagebox.showinfo("Saved Successfully", f"The current configuration has already been saved to {filepath}")

    def save_configuration(self):
        """Save the current configuration to the default file axis_config.json"""
        self.save_to_json(".")

    def load_configuration(self):
        """Load configuration"""
        try:
            with open(self.config_file, 'r') as f:
                loaded_config = json.load(f)
                self.config.update(loaded_config)

            self.timebase_scale.set(self.config["timebase"]["scale"])
            self.timebase_position.set(self.config["timebase"]["position"])

            for i in range(1, 5):
                getattr(self, f"channel_{i}_scale").set(self.config["channels"][f"channel_{i}"]["scale"])
                getattr(self, f"channel_{i}_position").set(self.config["channels"][f"channel_{i}"]["position"])

            for i in range(2):
                getattr(self, f"x_marker_{i + 1}").set(self.config["markers"][i]["x"])
                getattr(self, f"y_marker_{i + 1}").set(self.config["markers"][i]["y"])

            # messagebox.showinfo("Configuration Loaded", "Axis configuration loaded successfully!")
        except FileNotFoundError:
            messagebox.showwarning("Load Error", "No saved configuration found.")
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load configuration: {e}")
