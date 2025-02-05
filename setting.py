"""
===================================================
Created on: 22-07-2024
Author: Chang Xu
File: setting.py
Version: 1.4
Language: Python 3.12.3
Description:
This script defines the Settings interface for managing
the oscilloscope data save directory. Users can browse,
select, and save their preferred directory for storing
measurement data. The configuration is saved in a file
and reloaded upon startup.
===================================================
"""


import os
import tkinter as tk
from tkinter import filedialog, messagebox


class Setting:
    """
    A class to manage settings for saving oscilloscope data, allowing users to
    specify and save a directory for storing captured data.
    """

    def __init__(self, master):
        """Initialize the settings window with UI elements for selecting and saving the directory."""
        self.master = master

        # Default save directory
        self.save_directory = tk.StringVar(value="C:/Users/Public/OscilloscopeData")

        # Label to display save directory
        tk.Label(master, text="Save Directory:", bg="white", bd=0).grid(row=0, column=0, padx=60, pady=10)
        self.directory_entry = tk.Entry(master, textvariable=self.save_directory, width=50)
        self.directory_entry.grid(row=0, column=1, padx=10, pady=10)

        # Browse button to select directory
        browse_button = tk.Button(master, text="Browse...", command=self.browse_directory)
        browse_button.grid(row=0, column=2, padx=10, pady=10)

        # Save settings button
        save_button = tk.Button(master, text="Save Settings", command=self.save_settings)
        save_button.grid(row=1, column=1, pady=10)

        # Load existing settings if available
        self.load_settings()

    def browse_directory(self):
        """Open a file dialog to select a directory and update the entry field."""
        directory = filedialog.askdirectory(initialdir=self.save_directory.get())
        if directory:
            self.save_directory.set(directory)

    def save_settings(self):
        """Save the currently selected directory path to a configuration file."""
        selected_directory = self.save_directory.get()
        if not os.path.exists(selected_directory):
            os.makedirs(selected_directory)  # Create directory if it does not exist

        # Save directory path to a config file
        with open('config.txt', 'w') as config_file:
            config_file.write(f"SAVE_DIRECTORY={selected_directory}\n")

        messagebox.showinfo("Settings", "Settings saved successfully!")

    def load_settings(self):
        """Load previously saved settings from the configuration file."""
        try:
            with open('config.txt', 'r') as config_file:
                for line in config_file:
                    if line.startswith("SAVE_DIRECTORY="):
                        directory = line.split("=")[1].strip()
                        self.save_directory.set(directory)
        except FileNotFoundError:
            # If the config file does not exist, use the default directory
            pass


def get_save_directory():
    """Retrieve the currently set save directory from the configuration file."""
    try:
        with open('config.txt', 'r') as config_file:
            for line in config_file:
                if line.startswith("SAVE_DIRECTORY="):
                    return line.split("=")[1].strip()
    except FileNotFoundError:
        return "C:/Users/Public/OscilloscopeData"  # Return default path if no config file exists


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Settings")  # Set window title
    root.geometry("600x150")  # Set window size
    app = Setting(root)
    root.mainloop()

