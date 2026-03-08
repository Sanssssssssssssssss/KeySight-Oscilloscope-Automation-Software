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
import json
from pathlib import Path
from tkinter import filedialog, messagebox

from keysight_software.paths import project_path
from keysight_software.ui.theme import (
    COLORS,
    create_button,
    create_checkbutton,
    create_entry,
    create_label,
    style_toplevel,
)
from keysight_software.utils.waveform import get_measurement_names


DEFAULT_WAVEFORM_CONFIG = project_path("waveform_config.json")


class WaveformConfig:
    """
    GUI tool for configuring oscilloscope waveform capture settings.
    Allows users to select measurement parameters, channels, save options,
    and file storage directories, with the ability to save and load configurations.
    """

    def __init__(self, master):
        """Initializes the waveform configuration GUI and loads previous settings."""
        self.master = master
        style_toplevel(self.master, geometry="720x760")

        self.config = {
            "channels": [tk.IntVar() for _ in range(4)],  # Channel selection checkboxes
            "measurements": {  # Measurement selection checkboxes
                "Vpp": tk.IntVar(value=0),
                "Vmin": tk.IntVar(value=0),
                "Vmax": tk.IntVar(value=0),
                "Frequency": tk.IntVar(value=0),
                "Period": tk.IntVar(value=0),
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
        filepath = DEFAULT_WAVEFORM_CONFIG if directory == "." else Path(directory) / "waveform_config.json"
        with open(filepath, 'w', encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)

    def save_to_json2(self, directory):
        """Saves the current configuration settings as a JSON file and shows a success message."""
        self.save_to_json(directory)
        messagebox.showinfo("Save Successful", f"Configuration saved to {directory}/waveform_config.json")

    def create_ui(self):
        """Creates the graphical user interface with checkboxes, labels, and buttons."""
        self.master.configure(bg=COLORS["background"], padx=24, pady=24)
        create_label(self.master, "Select Channels", font=("SF Pro Display", 16, "bold")).grid(
            row=0, column=0, sticky='w', columnspan=4
        )
        for i in range(4):
            create_checkbutton(self.master, f"Channel {i + 1}", self.config["channels"][i]).grid(
                row=1, column=i, sticky='w', pady=(12, 0)
            )
            self.config["channels"][i].trace("w", lambda *args: self.save_to_json("."))

        create_label(self.master, "Select Measurements", font=("SF Pro Display", 16, "bold")).grid(
            row=2, column=0, sticky='w', columnspan=4, pady=(24, 0)
        )
        row_offset = 3
        measurement_names = get_measurement_names()
        self.config["measurements"] = {
            name: self.config["measurements"].get(name, tk.IntVar(value=0))
            for name in measurement_names
        }
        for j, (name, var) in enumerate(self.config["measurements"].items()):
            create_checkbutton(self.master, name, var).grid(row=row_offset + j // 4, column=j % 4, sticky='w', pady=(10, 0))
            var.trace("w", lambda *args: self.save_to_json("."))

        create_label(self.master, "Save Options", font=("SF Pro Display", 16, "bold")).grid(
            row=row_offset + (j // 4) + 1, column=0, sticky='w', columnspan=4, pady=(24, 0)
        )
        save_labels = ["Save Screenshot", "Save Waveform", "Save CSV", "Save Measurements"]
        for k, label in enumerate(save_labels):
            create_checkbutton(self.master, label, self.config["save_options"][k]).grid(
                row=row_offset + (j // 4) + 2, column=k % 4, sticky='w', pady=(10, 0)
            )
            self.config["save_options"][k].trace("w", lambda *args: self.save_to_json("."))

        row_for_directory = row_offset + (j // 4) + 3
        create_label(self.master, "Save Directory", muted=True).grid(row=row_for_directory, column=0, sticky='w', pady=(18, 0))
        self.save_dir_entry = create_entry(self.master, textvariable=self.config["save_directory"], width=30)
        self.save_dir_entry.grid(row=row_for_directory, column=1, sticky='w', padx=10, pady=5)
        create_button(self.master, "Browse", self.browse_directory, tone="secondary").grid(
            row=row_for_directory, column=2, sticky='w', padx=10, pady=5
        )

        create_label(self.master, "File Name", muted=True).grid(row=row_for_directory + 1, column=0, sticky='w', pady=(10, 0))
        self.file_name_entry = create_entry(self.master, textvariable=self.config["file_name"], width=30)
        self.file_name_entry.grid(row=row_for_directory + 1, column=1, sticky='w', padx=10, pady=5)

        # Bind directory and filename to auto-save
        self.config["save_directory"].trace("w", lambda *args: self.save_to_json("."))
        self.config["file_name"].trace("w", lambda *args: self.save_to_json("."))

        create_button(self.master, "Save Configuration", self.save_configuration, tone="primary").grid(
            row=row_for_directory + 2, column=0, pady=18
        )
        create_button(self.master, "Load Configuration", self.load_configuration, tone="secondary").grid(
            row=row_for_directory + 2, column=1, pady=18
        )

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
            with open(DEFAULT_WAVEFORM_CONFIG, "r", encoding="utf-8") as f:
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
            messagebox.showwarning("No Configuration Found", "No saved configuration found to load.")


if __name__ == "__main__":
    root = tk.Tk()
    app = WaveformConfig(root)
    root.mainloop()

