"""
===================================================
Created on: 21-7-2024
Author: Chang Xu
File: config_home.py
Version: 1.0
Language: Python 3.12.3
Description:
This script defines a GUI-based configuration home
interface for the Keysight oscilloscope automation system.
It allows users to configure VISA addresses, timeout settings,
file storage paths, and establish connections to the oscilloscope.
===================================================
"""


import tkinter as tk
from tkinter import messagebox, filedialog, scrolledtext
import pyvisa
import config  # Import the global configuration file

class ConfigHome:
    def __init__(self, master):
        # Create a main frame to hold everything
        main_frame = tk.Frame(master)
        main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        # Title Label
        title_label = tk.Label(main_frame, text="Home - Configuration", font=("Arial", 16))
        title_label.grid(row=0, column=0, columnspan=3, pady=30, padx=300, sticky=tk.N)

        # VISA Address Label and Entry
        tk.Label(main_frame, text="VISA Address:").grid(row=1, column=0, sticky=tk.E, pady=5)
        self.visa_entry = tk.Entry(main_frame, width=60)
        self.visa_entry.grid(row=1, column=1, padx=10, pady=5, sticky=tk.W)
        self.visa_entry.insert(0, config.VISA_ADDRESS)  # Use default value from config

        # Global Timeout Label and Entry
        tk.Label(main_frame, text="Global Timeout:").grid(row=2, column=0, sticky=tk.E, pady=5)
        self.timeout_entry = tk.Entry(main_frame, width=60)
        self.timeout_entry.grid(row=2, column=1, padx=10, pady=5, sticky=tk.W)
        self.timeout_entry.insert(0, config.GLOBAL_TIMEOUT)  # Use default value from config

        # Base Directory Label and Entry with Browse Button
        tk.Label(main_frame, text="Base Directory:").grid(row=3, column=0, sticky=tk.E, pady=5)
        self.directory_entry = tk.Entry(main_frame, width=60)
        self.directory_entry.grid(row=3, column=1, padx=10, pady=5, sticky=tk.W)
        self.directory_entry.insert(0, config.BASE_DIRECTORY)  # Use default value from config
        browse_button = tk.Button(main_frame, text="Browse", command=self.browse_directory)
        browse_button.grid(row=3, column=2, padx=0, pady=5)

        # Base File Name Label and Entry
        tk.Label(main_frame, text="Base File Name:").grid(row=4, column=0, sticky=tk.E, pady=5)
        self.filename_entry = tk.Entry(main_frame, width=60)
        self.filename_entry.grid(row=4, column=1, padx=10, pady=5, sticky=tk.W)
        self.filename_entry.insert(0, config.BASE_FILENAME)  # Use default value from config

        # Buttons (Detect and Connect)
        button_frame = tk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=10)

        detect_button = tk.Button(button_frame, text="Detect VISA Address", command=self.detect_visa_address)
        detect_button.pack(side=tk.LEFT, padx=10)

        connect_button = tk.Button(button_frame, text="Connect", command=self.connect_visa)
        connect_button.pack(side=tk.LEFT, padx=10)

        # Log Output Window
        self.log_output = scrolledtext.ScrolledText(main_frame, width=60, height=10, wrap=tk.WORD)
        self.log_output.grid(row=6, column=0, columnspan=3, padx=10, pady=10, sticky=tk.W + tk.E)

        # Save configuration button inside the ConfigHome constructor
        save_button = tk.Button(button_frame, text="Save Configuration", command=self.save_config)
        save_button.pack(side=tk.LEFT, padx=10)

        # Try auto detect VISA Address
        self.try_auto_detect_visa_address()

    def log_message(self, message):
        """Display message in the log window."""
        self.log_output.insert(tk.END, message + "\n")
        self.log_output.see(tk.END)

    def try_auto_detect_visa_address(self):
        """Auto-detect VISA address; allow manual input if fails."""
        try:
            rm = pyvisa.ResourceManager()
            resources = rm.list_resources()
            if resources:
                self.visa_entry.delete(0, tk.END)
                self.visa_entry.insert(0, resources[0])
                self.log_message(f"Found VISA Address: {resources[0]}")
            else:
                self.log_message("No devices found. Please enter the VISA Address manually.")
        except Exception as e:
            self.log_message(f"Failed to connect: {e}")

    def detect_visa_address(self):
        """Manually trigger VISA address detection."""
        try:
            rm = pyvisa.ResourceManager()
            resources = rm.list_resources()
            if resources:
                self.visa_entry.delete(0, tk.END)
                self.visa_entry.insert(0, resources[0])
                self.log_message(f"Found VISA Address: {resources[0]}")
            else:
                self.log_message("No devices found. Please enter the VISA Address manually.")
        except Exception as e:
            self.log_message(f"Failed to connect: {e}")

    def connect_visa(self):
        """Manually connect to the oscilloscope."""
        try:
            rm = pyvisa.ResourceManager()
            visa_address = self.visa_entry.get()
            self.scope = rm.open_resource(visa_address)
            self.log_message(f"Connected to: {self.scope.query('*IDN?')}")
        except pyvisa.errors.VisaIOError as e:
            messagebox.showerror("Connection Failed", f"Could not connect to the oscilloscope: {e}")
        except Exception as e:
            messagebox.showerror("Connection Failed", f"An unexpected error occurred: {e}")

    def browse_directory(self):
        """Browse for directory to set as Base Directory."""
        directory = filedialog.askdirectory()
        if directory:
            self.directory_entry.delete(0, tk.END)
            self.directory_entry.insert(0, directory)

    def save_config(self):
        """Save the configuration settings."""
        visa_address = self.visa_entry.get()
        global_timeout = self.timeout_entry.get()
        base_directory = self.directory_entry.get()
        base_filename = self.filename_entry.get()

        # Update global configuration
        config.update_visa_address(visa_address)
        config.update_global_timeout(int(global_timeout))
        config.update_base_directory(base_directory)
        config.update_base_filename(base_filename)

        # Add logic to save configuration, such as to a file or update global variables
        self.log_message(f"VISA Address: {config.VISA_ADDRESS}")
        self.log_message(f"Global Timeout: {config.GLOBAL_TIMEOUT}")
        self.log_message(f"Base Directory: {config.BASE_DIRECTORY}")
        self.log_message(f"Base File Name: {config.BASE_FILENAME}")

        # Indicate that configuration was saved successfully
        self.log_message("Configuration saved successfully!")


if __name__ == "__main__":
    root = tk.Tk()
    app = ConfigHome(root)
    root.mainloop()
