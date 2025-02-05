"""
===================================================
Created on: 22-07-2024
Author: Chang Xu
File: waveform_config.py
Version: 1.3
Language: Python 3.12.3
Description:
This script defines the WaveformConfig class, which
provides a GUI interface for configuring oscilloscope
waveform capture settings. Users can select channels,
measurements, save options, and directories for storing
captured data. The configuration can be saved and
loaded as a JSON file.
===================================================
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import json


class WaveformConfig:
    """
    GUI tool for configuring oscilloscope waveform capture settings.
    Allows users to select measurement parameters, channels, save options,
    and file storage directories, with the ability to save and load configurations.
    """

    def __init__(self, master):
        """Initializes the waveform configuration GUI and loads previous settings."""
        self.master = master

        # Configuration dictionary to store user selections
        self.config = {
            "channels": [tk.IntVar() for _ in range(4)],  # Channel selection checkboxes
            "measurements": {  # Measurement selection checkboxes
                "Vpp": tk.IntVar(value=0),
                "Vmin": tk.IntVar(value=0),
                "Vmax": tk.IntVar(value=0),
                "Frequency": tk.IntVar(value=0),
                "Pulse Width": tk.IntVar(value=0),
                "Fall Time": tk.IntVar(value=0),
                "Rise Time": tk.IntVar(value=0),
                "Duty Cycle": tk.IntVar(value=0),
                "RMS Voltage": tk.IntVar(value=0),
                "Average Voltage": tk.IntVar(value=0),
                "Amplitude": tk.IntVar(value=0),
                "Overshoot": tk.IntVar(value=0),
                "Preshoot": tk.IntVar(value=0),
                "Phase": tk.IntVar(value=0),
                "Edge Count": tk.IntVar(value=0),
                "Positive Edges": tk.IntVar(value=0),
                "Negative Pulses": tk.IntVar(value=0),
                "Positive Pulses": tk.IntVar(value=0),
                "XMin": tk.IntVar(value=0),
                "XMax": tk.IntVar(value=0),
                "VTop": tk.IntVar(value=0),
                "VBase": tk.IntVar(value=0),
                "VRatio": tk.IntVar(value=0),
            },
            "save_options": [tk.IntVar(value=0) for _ in range(4)],  # Save options checkboxes
            "save_directory": tk.StringVar(value=""),  # Directory to save files
            "file_name": tk.StringVar(value="waveform_data")  # Default filename
        }

        # Create UI components
        self.create_ui()

    def save_to_json(self, directory):
        """Saves the current configuration settings as a JSON file in the specified directory."""
        config_data = {
            "channels": [var.get() for var in self.config["channels"]],
            "measurements": {name: var.get() for name, var in self.config["measurements"].items()},
            "save_options": [var.get() for var in self.config["save_options"]],
            "save_directory": self.config["save_directory"].get(),
            "file_name": self.config["file_name"].get(),
        }
        filepath = f"{directory}/waveform_config.json"
        with open(filepath, 'w') as f:
            json.dump(config_data, f, indent=4)

    def save_to_json2(self, directory):
        """Saves the current configuration settings as a JSON file and shows a success message."""
        self.save_to_json(directory)
        tk.messagebox.showinfo("Save Successful", f"Configuration saved to {directory}/waveform_config.json")

    def create_ui(self):
        """Creates the graphical user interface with checkboxes, labels, and buttons."""
        # Channel selection
        tk.Label(self.master, text="Select Channels:").grid(row=0, column=0, sticky='w', columnspan=4)
        for i in range(4):
            tk.Checkbutton(self.master, text=f"Channel {i + 1}", variable=self.config["channels"][i]).grid(
                row=1, column=i, sticky='w')
            self.config["channels"][i].trace("w", lambda *args: self.save_to_json("."))

        # Measurement selection
        tk.Label(self.master, text="Select Measurements:").grid(row=2, column=0, sticky='w', columnspan=4)
        row_offset = 3
        for j, (name, var) in enumerate(self.config["measurements"].items()):
            tk.Checkbutton(self.master, text=name, variable=var).grid(row=row_offset + j // 4, column=j % 4, sticky='w')
            var.trace("w", lambda *args: self.save_to_json("."))

        # Save options
        tk.Label(self.master, text="Save Options:").grid(row=row_offset + (j // 4) + 1, column=0, sticky='w',
                                                         columnspan=4)
        save_labels = ["Save Screenshot", "Save Waveform", "Save CSV", "Save Measurements"]
        for k, label in enumerate(save_labels):
            tk.Checkbutton(self.master, text=label, variable=self.config["save_options"][k]).grid(
                row=row_offset + (j // 4) + 2, column=k % 4, sticky='w')
            self.config["save_options"][k].trace("w", lambda *args: self.save_to_json("."))

        # Save directory and file name
        row_for_directory = row_offset + (j // 4) + 3
        tk.Label(self.master, text="Save Directory:").grid(row=row_for_directory, column=0, sticky='w')
        self.save_dir_entry = tk.Entry(self.master, textvariable=self.config["save_directory"], width=30)
        self.save_dir_entry.grid(row=row_for_directory, column=1, sticky='w', padx=10, pady=5)
        tk.Button(self.master, text="Browse", command=self.browse_directory).grid(row=row_for_directory, column=2,
                                                                                  sticky='w', padx=10, pady=5)

        tk.Label(self.master, text="File Name:").grid(row=row_for_directory + 1, column=0, sticky='w')
        self.file_name_entry = tk.Entry(self.master, textvariable=self.config["file_name"], width=30)
        self.file_name_entry.grid(row=row_for_directory + 1, column=1, sticky='w', padx=10, pady=5)

        # Bind directory and filename to auto-save
        self.config["save_directory"].trace("w", lambda *args: self.save_to_json("."))
        self.config["file_name"].trace("w", lambda *args: self.save_to_json("."))

        # Buttons for saving and loading configurations
        tk.Button(self.master, text="Save Configuration", command=self.save_configuration).grid(
            row=row_for_directory + 2, column=0, pady=10)
        tk.Button(self.master, text="Load Configuration", command=self.load_configuration).grid(
            row=row_for_directory + 2, column=1, pady=10)

    def browse_directory(self):
        """Opens a directory selection dialog and updates the save directory path."""
        directory = filedialog.askdirectory()
        if directory:
            self.config["save_directory"].set(directory)

    def save_configuration(self):
        """Saves the current configuration to the default JSON file."""
        self.save_to_json2(".")

    def load_configuration(self):
        """Loads the configuration settings from the default JSON file."""
        try:
            with open("waveform_config.json", "r") as f:
                config_data = json.load(f)
            for i, val in enumerate(config_data["channels"]):
                self.config["channels"][i].set(val)
            for name, val in config_data["measurements"].items():
                self.config["measurements"][name].set(val)
            for i, val in enumerate(config_data["save_options"]):
                self.config["save_options"][i].set(val)
            self.config["save_directory"].set(config_data["save_directory"])
            self.config["file_name"].set(config_data["file_name"])
        except FileNotFoundError:
            tk.messagebox.showwarning("No Configuration Found", "No saved configuration found to load.")


if __name__ == "__main__":
    root = tk.Tk()
    app = WaveformConfig(root)
    root.mainloop()

