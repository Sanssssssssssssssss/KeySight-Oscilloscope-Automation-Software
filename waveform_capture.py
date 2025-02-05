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
import tkinter as tk
import json
from tkinter import ttk
from tkinter import scrolledtext
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from oscilloscope import Oscilloscope
from measure import Measure
import setting  # Import the setting module
from tkinter import filedialog, messagebox
import openpyxl  # Importing the openpyxl module to work with Excel files

from config import VISA_ADDRESS  # Importing global variables


class WaveformCapture:
    def __init__(self, master, oscilloscope, measure):
        '''nitializes the waveform capture GUI, establishes a connection with the oscilloscope, and loads previous settings.'''
        self.master = master
        self.osc = oscilloscope
        self.measure = measure
        self.is_connected = self.check_connection()  # Add this line
        self.measurement_vars = [tk.StringVar(value="") for _ in range(4)]
        self.save_directory = setting.get_save_directory()  # Using paths in setting
        self.selected_measurements = {}  # For saving the user's measurement selections

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
            with open("measurement_config.json", "r") as f:
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
            with open("measurement_config.json", "r") as f:
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
            "Vpp": tk.IntVar(value=saved_measurements.get("Vpp", 0)),
            "Vmin": tk.IntVar(value=saved_measurements.get("Vmin", 0)),
            "Vmax": tk.IntVar(value=saved_measurements.get("Vmax", 0)),
            "Frequency": tk.IntVar(value=saved_measurements.get("Frequency", 0)),
            "Pulse Width": tk.IntVar(value=saved_measurements.get("Pulse Width", 0)),
            "Fall Time": tk.IntVar(value=saved_measurements.get("Fall Time", 0)),
            "Rise Time": tk.IntVar(value=saved_measurements.get("Rise Time", 0)),
            "Duty Cycle": tk.IntVar(value=saved_measurements.get("Duty Cycle", 0)),
            "RMS Voltage": tk.IntVar(value=saved_measurements.get("RMS Voltage", 0)),
            "Average Voltage": tk.IntVar(value=saved_measurements.get("Average Voltage", 0)),
            "Amplitude": tk.IntVar(value=saved_measurements.get("Amplitude", 0)),
            "Overshoot": tk.IntVar(value=saved_measurements.get("Overshoot", 0)),
            "Preshoot": tk.IntVar(value=saved_measurements.get("Preshoot", 0)),
            "Phase": tk.IntVar(value=saved_measurements.get("Phase", 0)),
            "Edge Count": tk.IntVar(value=saved_measurements.get("Edge Count", 0)),
            "Positive Edges": tk.IntVar(value=saved_measurements.get("Positive Edges", 0)),
            "Negative Pulses": tk.IntVar(value=saved_measurements.get("Negative Pulses", 0)),
            "Positive Pulses": tk.IntVar(value=saved_measurements.get("Positive Pulses", 0)),
            "XMin": tk.IntVar(value=saved_measurements.get("XMin", 0)),
            "XMax": tk.IntVar(value=saved_measurements.get("XMax", 0)),
            "VTop": tk.IntVar(value=saved_measurements.get("VTop", 0)),
            "VBase": tk.IntVar(value=saved_measurements.get("VBase", 0)),
            "VRatio": tk.IntVar(value=saved_measurements.get("VRatio", 0)),
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
        with open("measurement_config.json", "w") as f:
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

        if not self.is_connected:
            return  # Exit if not connected to the oscilloscope

        active_channels = self.osc.get_active_channels()
        for i in range(4):
            if i + 1 in active_channels:
                self.channel_vars[i].set(1)
            else:
                self.channel_vars[i].set(0)

    def capture_waveform(self):
        '''Captures waveform data from selected channels and displays the results.'''
        if not self.is_connected:
            messagebox.showerror("Error", "Oscilloscope is not connected. Cannot capture waveform.")
            return

        selected_channels = [i + 1 for i, var in enumerate(self.channel_vars) if var.get() == 1]

        if not selected_channels:
            messagebox.showwarning("No Channel Selected", "Please select at least one channel.")
            return

        waveforms = {}
        for channel in selected_channels:
            time_values, waveform_data = self.osc.capture_waveform(channel=channel)
            waveforms[channel] = (time_values, waveform_data)

            # Performs measurements based on user selection
            if self.selected_measurements.get("Vpp"):
                vpp = self.measure.measure_vpp(channel)
                self.console_output.insert(tk.END, f"Channel {channel} - Vpp: {vpp} V\n")

            if self.selected_measurements.get("Vmin"):
                vmin = self.measure.measure_vmin(channel)
                self.console_output.insert(tk.END, f"Channel {channel} - Vmin: {vmin} V\n")

            if self.selected_measurements.get("Vmax"):
                vmax = self.measure.measure_vmax(channel)
                self.console_output.insert(tk.END, f"Channel {channel} - Vmax: {vmax} V\n")

            if self.selected_measurements.get("Frequency"):
                frequency = self.measure.measure_frequency(channel)
                self.console_output.insert(tk.END, f"Channel {channel} - Frequency: {frequency} Hz\n")

            if self.selected_measurements.get("Period"):
                period = self.measure.measure_period(channel)
                self.console_output.insert(tk.END, f"Channel {channel} - Period: {period} s\n")

            if self.selected_measurements.get("Pulse Width"):
                pulse_width = self.measure.measure_pulse_width(channel)
                self.console_output.insert(tk.END, f"Channel {channel} - Pulse Width: {pulse_width} s\n")

            if self.selected_measurements.get("Fall Time"):
                fall_time = self.measure.measure_fall_time(channel)
                self.console_output.insert(tk.END, f"Channel {channel} - Fall Time: {fall_time} s\n")

            if self.selected_measurements.get("Rise Time"):
                rise_time = self.measure.measure_rise_time(channel)
                self.console_output.insert(tk.END, f"Channel {channel} - Rise Time: {rise_time} s\n")

            if self.selected_measurements.get("Duty Cycle"):
                duty_cycle = self.measure.measure_duty_cycle(channel)
                self.console_output.insert(tk.END, f"Channel {channel} - Duty Cycle: {duty_cycle} %\n")

            if self.selected_measurements.get("RMS Voltage"):
                rms_voltage = self.measure.measure_rms_voltage(channel)
                self.console_output.insert(tk.END, f"Channel {channel} - RMS Voltage: {rms_voltage} V\n")

            if self.selected_measurements.get("Average Voltage"):
                avg_voltage = self.measure.measure_average_voltage(channel)
                self.console_output.insert(tk.END, f"Channel {channel} - Average Voltage: {avg_voltage} V\n")

            if self.selected_measurements.get("Amplitude"):
                amplitude = self.measure.measure_amplitude(channel)
                self.console_output.insert(tk.END, f"Channel {channel} - Amplitude: {amplitude} V\n")

            if self.selected_measurements.get("Overshoot"):
                overshoot = self.measure.measure_overshoot(channel)
                self.console_output.insert(tk.END, f"Channel {channel} - Overshoot: {overshoot} %\n")

            if self.selected_measurements.get("Preshoot"):
                preshoot = self.measure.measure_preshoot(channel)
                self.console_output.insert(tk.END, f"Channel {channel} - Preshoot: {preshoot} %\n")

            if self.selected_measurements.get("Phase"):
                phase = self.measure.measure_phase(self.selected_channel_1, self.selected_channel_2)
                self.console_output.insert(tk.END,
                                           f"Phase between Channel {self.selected_channel_1} and {self.selected_channel_2}: {phase} degrees\n")

            if self.selected_measurements.get("Edge Count"):
                edge_count = self.measure.measure_edge_count(channel)
                self.console_output.insert(tk.END, f"Channel {channel} - Edge Count: {edge_count}\n")

            if self.selected_measurements.get("Positive Edges"):
                pos_edges = self.measure.measure_pos_edge_count(channel)
                self.console_output.insert(tk.END, f"Channel {channel} - Positive Edges: {pos_edges}\n")

            if self.selected_measurements.get("Negative Pulses"):
                neg_pulses = self.measure.measure_n_pulses(channel)
                self.console_output.insert(tk.END, f"Channel {channel} - Negative Pulses: {neg_pulses}\n")

            if self.selected_measurements.get("Positive Pulses"):
                pos_pulses = self.measure.measure_p_pulses(channel)
                self.console_output.insert(tk.END, f"Channel {channel} - Positive Pulses: {pos_pulses}\n")

            if self.selected_measurements.get("XMin"):
                xmin = self.measure.measure_xmin(channel)
                self.console_output.insert(tk.END, f"Channel {channel} - XMin: {xmin}\n")

            if self.selected_measurements.get("XMax"):
                xmax = self.measure.measure_xmax(channel)
                self.console_output.insert(tk.END, f"Channel {channel} - XMax: {xmax}\n")

            if self.selected_measurements.get("VTop"):
                vtop = self.measure.measure_vtop(channel)
                self.console_output.insert(tk.END, f"Channel {channel} - VTop: {vtop} V\n")

            if self.selected_measurements.get("VBase"):
                vbase = self.measure.measure_vbase(channel)
                self.console_output.insert(tk.END, f"Channel {channel} - VBase: {vbase} V\n")

            if self.selected_measurements.get("VRatio"):
                vratio = self.measure.measure_vratio(channel)
                self.console_output.insert(tk.END, f"Channel {channel} - VRatio: {vratio} dB\n")

        self.console_output.see(tk.END)
        self.osc.plot_all_waveforms(waveforms, self.ax, self.canvas)

    def save_data(self):
        '''Saves captured waveform data in different formats (screenshot, CSV, Excel).'''
        # Get the file name entered by the user
        file_name = self.filename_entry.get()
        if not file_name:
            messagebox.showwarning("Invalid File Name", "Please enter a valid file name.")
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
            with open(csv_path, 'w') as f:
                # Assume that the timeline is the same for each channel, so we only write the timeline once
                f.write("Time (s)")
                for i in range(4):
                    if self.channel_vars[i].get():
                        f.write(f", Channel {i + 1} Amplitude (V)")
                f.write("\n")

                # Get waveform data of all selected channels
                all_waveforms = []
                for i in range(4):
                    if self.channel_vars[i].get():
                        time_values, waveform_data = self.osc.capture_waveform(i + 1)
                        all_waveforms.append((time_values, waveform_data))

                # Assuming that each channel has the same data length, data can be written at the same time
                for j in range(len(all_waveforms[0][0])):
                    # Write Time Value
                    f.write(f"{all_waveforms[0][0][j]}")
                    for time_values, waveform_data in all_waveforms:
                        f.write(f", {waveform_data[j]}")
                    f.write("\n")

        if self.save_options[3].get():
            excel_path = os.path.join(full_save_dir, f"{file_name}_measurements.xlsx")
            workbook = openpyxl.Workbook()
            sheet = workbook.active
            sheet.title = "Measurements"

            # Write the title according to the selected measurement
            headers = ["Channel"] + [key for key, selected in self.selected_measurements.items() if selected]
            sheet.append(headers)

            # Write data for each channel
            for i in range(4):
                if self.channel_vars[i].get():
                    channel_data = [f"Channel {i + 1}"]
                    if self.selected_measurements.get("Vpp"):
                        channel_data.append(self.measure.measure_vpp(i + 1))
                    if self.selected_measurements.get("Vmin"):
                        channel_data.append(self.measure.measure_vmin(i + 1))
                    if self.selected_measurements.get("Vmax"):
                        channel_data.append(self.measure.measure_vmax(i + 1))
                    if self.selected_measurements.get("Frequency"):
                        channel_data.append(self.measure.measure_frequency(i + 1))
                    if self.selected_measurements.get("Period"):
                        channel_data.append(self.measure.measure_period(i + 1))
                    if self.selected_measurements.get("Pulse Width"):
                        channel_data.append(self.measure.measure_pulse_width(i + 1))
                    if self.selected_measurements.get("Fall Time"):
                        channel_data.append(self.measure.measure_fall_time(i + 1))
                    if self.selected_measurements.get("Rise Time"):
                        channel_data.append(self.measure.measure_rise_time(i + 1))
                    if self.selected_measurements.get("Duty Cycle"):
                        channel_data.append(self.measure.measure_duty_cycle(i + 1))
                    if self.selected_measurements.get("RMS Voltage"):
                        channel_data.append(self.measure.measure_rms_voltage(i + 1))
                    if self.selected_measurements.get("Average Voltage"):
                        channel_data.append(self.measure.measure_average_voltage(i + 1))
                    if self.selected_measurements.get("Amplitude"):
                        channel_data.append(self.measure.measure_amplitude(i + 1))
                    if self.selected_measurements.get("Overshoot"):
                        channel_data.append(self.measure.measure_overshoot(i + 1))
                    if self.selected_measurements.get("Preshoot"):
                        channel_data.append(self.measure.measure_preshoot(i + 1))
                    if self.selected_measurements.get("Edge Count"):
                        channel_data.append(self.measure.measure_edge_count(i + 1))
                    if self.selected_measurements.get("Positive Edges"):
                        channel_data.append(self.measure.measure_pos_edge_count(i + 1))
                    if self.selected_measurements.get("Negative Pulses"):
                        channel_data.append(self.measure.measure_n_pulses(i + 1))
                    if self.selected_measurements.get("Positive Pulses"):
                        channel_data.append(self.measure.measure_p_pulses(i + 1))
                    if self.selected_measurements.get("XMin"):
                        channel_data.append(self.measure.measure_xmin(i + 1))
                    if self.selected_measurements.get("XMax"):
                        channel_data.append(self.measure.measure_xmax(i + 1))
                    if self.selected_measurements.get("VTop"):
                        channel_data.append(self.measure.measure_vtop(i + 1))
                    if self.selected_measurements.get("VBase"):
                        channel_data.append(self.measure.measure_vbase(i + 1))
                    if self.selected_measurements.get("VRatio"):
                        channel_data.append(self.measure.measure_vratio(i + 1))
                    if self.selected_measurements.get("Phase"):
                        phase = self.measure.measure_phase(self.selected_channel_1, self.selected_channel_2)
                        channel_data.append(phase)

                    sheet.append(channel_data)

            workbook.save(excel_path)
            self.console_output.insert(tk.END, f"Measurements saved at {excel_path}\n")


if __name__ == "__main__":
    root = tk.Tk()
    osc = Oscilloscope(VISA_ADDRESS, 10000)
    measure = Measure(osc)
    app = WaveformCapture(root, osc, measure)
    root.mainloop()
