"""
===================================================
Created on: 21-07-2024
Author: Chang Xu
File: waveform_capture.py
Version: 2.1
Language: Python 3.12.3
Description:
This script defines the WaveformCapture class, which
provides a GUI-based tool for capturing, analyzing,
and saving waveform data from an oscilloscope. It
supports real-time visualization, measurement selection,
and data storage in multiple formats.
===================================================
"""

import os
import json
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from tkinter import filedialog, messagebox

import openpyxl  # Importing the openpyxl module to work with Excel files
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from keysight_software.config import VISA_ADDRESS
from keysight_software.device.measure import Measure
from keysight_software.device.oscilloscope import Oscilloscope
from keysight_software.paths import project_path
from keysight_software.ui.pages import settings
from keysight_software.utils.waveform import (
    build_measurement_row,
    collect_channel_measurements,
    collect_shared_measurements,
    format_channel_measurement_lines,
    format_shared_measurement_lines,
    get_measurement_names,
    get_selected_measurement_headers,
    write_waveforms_to_csv,
)


MEASUREMENT_CONFIG_FILE = project_path("measurement_config.json")


class WaveformCapture:
    def __init__(self, master, oscilloscope, measure):
        '''nitializes the waveform capture GUI, establishes a connection with the oscilloscope, and loads previous settings.'''
        self.master = master
        self.osc = oscilloscope
        self.measure = measure
        self.is_connected = self.check_connection()  # Add this line
        self.measurement_vars = [tk.StringVar(value="") for _ in range(4)]
        self.save_directory = settings.get_save_directory()  # Using paths in setting
        self.selected_measurements = {}  # For saving the user's measurement selections
        self.last_waveforms = {}
        self.last_channel_measurements = {}
        self.last_shared_measurements = {}

        # Create Matplotlib Figure
        self.figure = Figure(figsize=(8, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.master)
        self.canvas.get_tk_widget().grid(row=0, column=0, columnspan=4, pady=10)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

        # Console output for displaying measurement results
        self.console_output = scrolledtext.ScrolledText(master, width=50, height=10, wrap=tk.WORD, bg="black",
                                                        fg="white", bd=0)
        self.console_output.grid(row=4, column=0, columnspan=2, pady=10, sticky='we')

        # Console output for displaying mouse movement coordinates
        self.coordinate_output = scrolledtext.ScrolledText(master, width=30, height=10, wrap=tk.WORD, bg="black",
                                                           fg="white", bd=0)
        self.coordinate_output.grid(row=4, column=2, columnspan=2, pady=10, sticky='we')

        # Channel selection checkboxes
        self.channel_vars = [tk.IntVar() for _ in range(4)]
        self.channel_checkbuttons = []
        for i in range(4):
            cb = tk.Checkbutton(master, text=f"Channel {i + 1}", variable=self.channel_vars[i], bg="white", bd=0)
            cb.grid(row=1, column=i, padx=60, pady=10, sticky='w')

        # Automatically detect and select active channels
        self.detect_active_channels()

        self.capture_button = tk.Button(master, text="Capture Waveform", command=self.capture_waveform)
        self.capture_button.grid(row=3, column=0, columnspan=4, pady=0)

        # Disable the Capture button if not connected to the oscilloscope
        self.capture_button.config(state=tk.DISABLED if not self.is_connected else tk.NORMAL)

        # Add a button to open the measurement selection window
        self.select_measurements_button = tk.Button(master, text="Select Measurements",
                                                    command=self.open_measurement_selection_window)
        self.select_measurements_button.grid(row=3, column=2, columnspan=2, pady=10, padx=10, sticky='e')

        # Save options and button
        self.save_options = [tk.IntVar(value=1) for _ in range(4)]
        self.save_labels = ["Save Screenshot", "Save Matplotlib Waveform", "Save CSV", "Save Measurements"]
        self.save_checkbuttons = []
        for i, label in enumerate(self.save_labels):
            cb = tk.Checkbutton(master, text=label, variable=self.save_options[i], bg="white", bd=0)
            cb.grid(row=5, column=i, sticky='w')
            self.save_checkbuttons.append(cb)

        # Save Data button
        self.save_button = tk.Button(master, text="Save Data", command=self.save_data)
        self.save_button.grid(row=6, column=1, columnspan=4, pady=10, padx=30)

        # Filename input boxes and labels (remain unchanged)
        self.filename_label = tk.Label(master, text="File Name:", bg="white", bd=0)
        self.filename_label.grid(row=6, column=0, sticky='e', pady=10)

        self.filename_entry = tk.Entry(master, bg="white")  # Added bg="white" for consistency
        self.filename_entry.grid(row=6, column=1, pady=10, sticky='w')

        # Try to load the previously saved configuration from a file
        try:
            with open(MEASUREMENT_CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                self.selected_measurements = config.get("selected_measurements", {})
                self.selected_channel_1 = config.get("selected_channel_1", 1)
                self.selected_channel_2 = config.get("selected_channel_2", 2)
        except FileNotFoundError:
            # If the file does not exist, use the default value
            self.selected_measurements = {}
            self.selected_channel_1 = 1
            self.selected_channel_2 = 2

    def open_measurement_selection_window(self):
        '''Opens a window for users to select waveform measurement parameters.'''
        self.selection_window = tk.Toplevel(self.master)
        self.selection_window.title("Select Measurement Parameters")
        self.selection_window.geometry("400x400")

        # Creating a scrolling area
        container = ttk.Frame(self.selection_window)
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        container.pack(fill="both", expand=True)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Load previously saved selections from the JSON file
        try:
            with open(MEASUREMENT_CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            saved_measurements = config.get("selected_measurements", {})
            self.selected_channel_1 = config.get("selected_channel_1", 1)
            self.selected_channel_2 = config.get("selected_channel_2", 2)
        except FileNotFoundError:
            saved_measurements = {}
            self.selected_channel_1 = 1
            self.selected_channel_2 = 2

        # Initialize measurement selection variables
        self.measurement_selection_vars = {
            name: tk.IntVar(value=saved_measurements.get(name, 0))
            for name in get_measurement_names()
        }

        # Create a selection screen
        for name, var in self.measurement_selection_vars.items():
            cb = tk.Checkbutton(scrollable_frame, text=name, variable=var)
            cb.pack(anchor='w')

        # Add channel selection for dual-channel measurements
        tk.Label(scrollable_frame, text="Select channels for dual-channel measurements:").pack(anchor='w')

        self.channel_1_var = tk.IntVar(value=self.selected_channel_1)
        self.channel_2_var = tk.IntVar(value=self.selected_channel_2)

        tk.Label(scrollable_frame, text="Channel 1:").pack(anchor='w')
        tk.OptionMenu(scrollable_frame, self.channel_1_var, *[1, 2, 3, 4]).pack(anchor='w')

        tk.Label(scrollable_frame, text="Channel 2:").pack(anchor='w')
        tk.OptionMenu(scrollable_frame, self.channel_2_var, *[1, 2, 3, 4]).pack(anchor='w')

        # Save button
        save_button = tk.Button(self.selection_window, text="Save", command=self.save_measurement_selection)
        save_button.pack(pady=10)

        self.selection_window.transient(self.master)  # Keep the window on top
        self.selection_window.grab_set()  # Make it modal
        self.master.wait_window(self.selection_window)  # Wait until window is closed

    def save_measurement_selection(self):
        '''Saves selected measurement settings to a JSON file.'''
        # Save the current selections from the child window
        self.selected_measurements = {name: var.get() for name, var in self.measurement_selection_vars.items()}
        self.selected_channel_1 = self.channel_1_var.get()
        self.selected_channel_2 = self.channel_2_var.get()

        # Save the selections to a JSON file
        config = {
            "selected_measurements": self.selected_measurements,
            "selected_channel_1": self.selected_channel_1,
            "selected_channel_2": self.selected_channel_2
        }
        with open(MEASUREMENT_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f)

        self.selection_window.destroy()  # Close the child window after saving

    def check_connection(self):
        '''Checks whether the oscilloscope is properly connected.'''
        try:
            # Attempt a simple command to check if the oscilloscope is connected
            self.osc.get_active_channels()
            return True
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to the oscilloscope: {e}")
            return False

    def on_mouse_move(self, event):
        '''Displays cursor coordinates in real-time when the mouse moves over the waveform plot.'''
        if event.inaxes:  # Make sure the mouse is in the drawing area
            x_data = event.xdata
            y_data = event.ydata
            self.coordinate_output.insert(tk.END, f"X: {x_data:.5f}, Y: {y_data:.5f}\n")
            self.coordinate_output.see(tk.END)

    def detect_active_channels(self):
        '''Automatically detects and selects active oscilloscope channels.'''
        if not self.is_connected:
            return  # Exit if not connected to the oscilloscope

        active_channels = self.osc.get_active_channels()
        for i in range(4):
            if i + 1 in active_channels:
                self.channel_vars[i].set(1)
            else:
                self.channel_vars[i].set(0)

    def get_selected_channels(self):
        return [index + 1 for index, var in enumerate(self.channel_vars) if var.get() == 1]

    def capture_waveform(self):
        '''Captures waveform data from selected channels and displays the results.'''
        if not self.is_connected:
            messagebox.showerror("Error", "Oscilloscope is not connected. Cannot capture waveform.")
            return

        selected_channels = self.get_selected_channels()

        if not selected_channels:
            messagebox.showwarning("No Channel Selected", "Please select at least one channel.")
            return

        self.console_output.delete("1.0", tk.END)
        waveforms = {}
        channel_measurements = {}
        for channel in selected_channels:
            time_values, waveform_data = self.osc.capture_waveform(channel=channel)
            waveforms[channel] = (time_values, waveform_data)
            channel_measurements[channel] = collect_channel_measurements(
                self.measure,
                self.selected_measurements,
                channel,
            )
            for line in format_channel_measurement_lines(channel, channel_measurements[channel]):
                self.console_output.insert(tk.END, f"{line}\n")

        shared_measurements = collect_shared_measurements(
            self.measure,
            self.selected_measurements,
            self.selected_channel_1,
            self.selected_channel_2,
        )
        for line in format_shared_measurement_lines(
            shared_measurements,
            self.selected_channel_1,
            self.selected_channel_2,
        ):
            self.console_output.insert(tk.END, f"{line}\n")

        self.last_waveforms = waveforms
        self.last_channel_measurements = channel_measurements
        self.last_shared_measurements = shared_measurements
        self.console_output.see(tk.END)
        self.osc.plot_all_waveforms(waveforms, self.ax, self.canvas)

    def save_data(self):
        '''Saves captured waveform data in different formats (screenshot, CSV, Excel).'''
        # Get the file name entered by the user
        file_name = self.filename_entry.get()
        if not file_name:
            messagebox.showwarning("Invalid File Name", "Please enter a valid file name.")
            return

        if not self.last_waveforms:
            messagebox.showwarning("No Waveform Data", "Capture waveform data before saving.")
            return

        # Use setting.SAVE_DIRECTORY as the default path
        save_dir = self.save_directory
        if not save_dir:
            save_dir = filedialog.askdirectory(title="Select Directory to Save Data")
        if not save_dir:
            return

        # Create a subdirectory with the filename as the subdirectory name
        full_save_dir = os.path.join(save_dir, file_name)

        # Checks if the folder exists and asks if it is overwritten if it exists
        if os.path.exists(full_save_dir):
            result = messagebox.askyesno("File Exists",
                                         "A folder with this name already exists. Do you want to overwrite it?")
            if not result:
                return

        os.makedirs(full_save_dir, exist_ok=True)

        # Save Screenshot
        if self.save_options[0].get():
            screenshot_path = os.path.join(full_save_dir, f"{file_name}_screenshot.png")
            self.osc.capture_screenshot(screenshot_path)
            self.console_output.insert(tk.END, f"Screenshot saved at {screenshot_path}\n")

        # Saving Matplotlib Waveforms
        if self.save_options[1].get():
            figure_path = os.path.join(full_save_dir, f"{file_name}_waveform_plot.png")
            self.figure.savefig(figure_path)
            self.console_output.insert(tk.END, f"Waveform plot saved at {figure_path}\n")

        # Save CSV file
        if self.save_options[2].get():
            csv_path = os.path.join(full_save_dir, f"{file_name}_waveform_data.csv")
            write_waveforms_to_csv(csv_path, self.last_waveforms)
            self.console_output.insert(tk.END, f"Waveform data saved at {csv_path}\n")

        if self.save_options[3].get():
            excel_path = os.path.join(full_save_dir, f"{file_name}_measurements.xlsx")
            workbook = openpyxl.Workbook()
            sheet = workbook.active
            sheet.title = "Measurements"

            # Write the title according to the selected measurement
            headers = ["Channel"] + get_selected_measurement_headers(self.selected_measurements)
            sheet.append(headers)

            # Write data for each channel
            for channel in sorted(self.last_waveforms):
                channel_data = build_measurement_row(
                    channel,
                    self.selected_measurements,
                    self.last_channel_measurements.get(channel, {}),
                    self.last_shared_measurements,
                )
                sheet.append(channel_data)

            workbook.save(excel_path)
            self.console_output.insert(tk.END, f"Measurements saved at {excel_path}\n")


if __name__ == "__main__":
    root = tk.Tk()
    osc = Oscilloscope(VISA_ADDRESS, 10000)
    measure = Measure(osc)
    app = WaveformCapture(root, osc, measure)
    root.mainloop()
