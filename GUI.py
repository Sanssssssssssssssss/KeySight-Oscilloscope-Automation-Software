"""
===================================================
Created on: 21-7-2024
Author: Chang Xu
File: GUI.py
Version: 1.0
Language: Python 3.12.3
Description:
This script defines the main GUI for the Keysight
oscilloscope control software. It provides an interactive
interface to configure settings, capture waveforms,
execute scripts, and process batch data.
===================================================
"""

import tkinter as tk
from tkinter import messagebox
from config_home import ConfigHome
from config import VISA_ADDRESS  # Import global variable
from waveform_capture import WaveformCapture
from setting import Setting
from oscilloscope import Oscilloscope
from measure import Measure
from batch_process import BatchProcessPage
from AxisControlWindow import AxisControlPage
from ScriptEditor import ScriptEditor
from run_script_page import RunScriptPage


class MainGUI:
    def __init__(self, master):
        """
        Initialize the main GUI for oscilloscope control.
        """
        self.master = master
        master.title("Oscilloscope Control Software")

        # Set up main window size
        master.geometry("1000x750")

        # Left-side menu frame
        self.menu_frame = tk.Frame(master, bg='lightgrey', width=100, padx=10, pady=10)
        self.menu_frame.grid(row=0, column=0, sticky='nswe')

        # Ensure the left-side menu frame has a fixed width
        self.menu_frame.grid_propagate(False)

        # Configure column layout
        master.grid_columnconfigure(0, weight=0, minsize=100)  # Fixed width for menu
        master.grid_columnconfigure(1, weight=1)  # Expand the main content area

        # Navigation buttons
        self.home_button = tk.Button(self.menu_frame, text="Home", command=self.show_home)
        self.home_button.pack(fill=tk.X, pady=5)

        self.axis_control_button = tk.Button(self.menu_frame, text="Axis Control", command=self.show_axis_control)
        self.axis_control_button.pack(fill=tk.X, pady=5)

        self.capture_button = tk.Button(self.menu_frame, text="Waveform Capture", command=self.show_waveform_capture)
        self.capture_button.pack(fill=tk.X, pady=5)

        self.script_editor_button = tk.Button(self.menu_frame, text="Script Editor", command=self.show_script_editor)
        self.script_editor_button.pack(fill=tk.X, pady=5)

        self.run_script_button = tk.Button(self.menu_frame, text="Run Script", command=self.show_run_script)
        self.run_script_button.pack(fill=tk.X, pady=5)

        self.process_button = tk.Button(self.menu_frame, text="Batch Process", command=self.show_batch_process)
        self.process_button.pack(fill=tk.X, pady=5)

        self.setting_button = tk.Button(self.menu_frame, text="Settings", command=self.show_settings)
        self.setting_button.pack(fill=tk.X, pady=5)

        # Main display area
        self.display_frame = tk.Frame(master, bg='white')
        self.display_frame.grid(row=0, column=1, sticky='nsew', padx=10, pady=10)
        master.grid_rowconfigure(0, weight=1)

        # Default to showing the Home page
        self.show_home()

        # Attempt to initialize the oscilloscope connection
        try:
            self.oscilloscope = Oscilloscope(VISA_ADDRESS, 10000)
            self.measure = Measure(self.oscilloscope)
            messagebox.showinfo("Connection Status", "Successfully connected to the oscilloscope.")
        except Exception as e:
            messagebox.showerror("Connection Failed", f"Could not connect to the oscilloscope: {e}")
            self.oscilloscope = None
            self.measure = None

    def show_home(self):
        """Display the Home configuration page."""
        self.clear_display_frame()
        ConfigHome(self.display_frame)

    def show_axis_control(self):
        """Display the Axis Control page."""
        self.clear_display_frame()
        AxisControlPage(self.display_frame, self.oscilloscope)

    def show_waveform_capture(self):
        """Display the Waveform Capture page."""
        self.clear_display_frame()
        WaveformCapture(self.display_frame, self.oscilloscope, self.measure)

    def show_script_editor(self):
        """Display the Script Editor page."""
        self.clear_display_frame()
        ScriptEditor(self.display_frame)

    def show_run_script(self):
        """Display the Run Script page."""
        self.clear_display_frame()
        RunScriptPage(self.display_frame)

    def show_batch_process(self):
        """Display the Batch Processing page."""
        self.clear_display_frame()
        BatchProcessPage(self.display_frame)

    def show_settings(self):
        """Display the Settings page."""
        self.clear_display_frame()
        Setting(self.display_frame)

    def clear_display_frame(self):
        """Remove all widgets from the display frame."""
        for widget in self.display_frame.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = MainGUI(root)
    root.mainloop()
