"""
===================================================
Created on: 22-7-2024
Author: Chang Xu
File: run_script_page.py
Version: 3.3
Language: Python 3.12.3
Description:
This script defines the Run Script interface for the
oscilloscope control system. It loads scripts from a
JSON file and executes tasks like waveform capture
and axis control.
===================================================
"""


import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, simpledialog
import json
import os
import openpyxl
from matplotlib import pyplot as plt

from oscilloscope import Oscilloscope
from measure import Measure
from tkinter import filedialog, messagebox

from config import VISA_ADDRESS  # Import global variables


class RunScriptPage(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.grid(sticky=tk.NSEW)
        self.script_path = tk.StringVar(value="")  # Variable to store the script path
        # Attempt to initialize the oscilloscope
        try:
            self.oscilloscope = Oscilloscope(VISA_ADDRESS, 10000)
            self.measure = Measure(self.oscilloscope)
            messagebox.showinfo("Connection Status", "Successfully connected to the oscilloscope.")
        except Exception as e:
            messagebox.showerror("Connection Failed", f"Could not connect to the oscilloscope: {e}")
            self.oscilloscope = None
            self.measure = None

        # Create UI elements
        self.create_widgets()

    def create_widgets(self):
        # Script path selection area
        tk.Label(self, text="Script Path:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        tk.Entry(self, textvariable=self.script_path, width=94).grid(row=0, column=1, padx=10, pady=5)
        tk.Button(self, text="Browse", command=self.browse_script).grid(row=0, column=2, padx=10, pady=5)

        # Console to display script sequence
        tk.Label(self, text="Script Sequence:").grid(row=1, column=0, columnspan=3, sticky=tk.W, padx=10, pady=5)
        self.script_console = scrolledtext.ScrolledText(self, height=10, bg='lightgray')
        self.script_console.grid(row=2, column=0, columnspan=3, padx=10, pady=5, sticky=tk.NSEW)

        # Console to display execution status
        tk.Label(self, text="Status:").grid(row=3, column=0, columnspan=3, sticky=tk.W, padx=10, pady=5)
        self.status_console = scrolledtext.ScrolledText(self, height=10, bg='lightgray')
        self.status_console.grid(row=4, column=0, columnspan=3, padx=10, pady=5, sticky=tk.NSEW)

        # Run script button
        tk.Button(self, text="Run Script", command=self.run_script).grid(row=5, column=0, columnspan=3, pady=10)

        # Configure window layout for proper resizing
        self.master.grid_rowconfigure(2, weight=1)
        self.master.grid_rowconfigure(4, weight=1)
        self.master.grid_columnconfigure(1, weight=1)

    def browse_script(self):
        """Browse and select the folder containing the script to run"""
        directory = filedialog.askdirectory()
        if directory:
            # Look for the sequence.json file within the selected directory
            script_filepath = os.path.join(directory, "sequence.json")
            if os.path.exists(script_filepath):
                self.script_path.set(script_filepath)
                self.load_script(script_filepath)
            else:
                messagebox.showerror("File Not Found", "sequence.json not found in the selected directory.")

    def load_script(self, filepath):
        """Load and display script content"""
        self.script_console.delete(1.0, tk.END)
        try:
            with open(filepath, 'r') as f:
                script_data = json.load(f)
                for i, module in enumerate(script_data.get("modules", [])):
                    self.script_console.insert(tk.END, f"{i + 1}. {module['type']}\n")
        except Exception as e:
            messagebox.showerror("Load Error", f"Cannot Load Script: {e}")

    def run_script(self):
        """Main logic for running the script"""
        self.status_console.delete(1.0, tk.END)
        script_filepath = self.script_path.get()

        if not script_filepath:
            messagebox.showwarning("Running Error", "Please select a script first.")
            return

        try:
            with open(script_filepath, 'r') as f:
                script_data = json.load(f)

            for module in script_data.get("modules", []):
                module_type = module.get("type")
                self.status_console.insert(tk.END, f"Running: {module_type}\n")
                self.status_console.update()

                if module_type == "Delay":
                    delay_time = module.get("delay", 1.0)
                    self.status_console.insert(tk.END, f"Waiting for {delay_time} seconds...\n")
                    self.status_console.update()
                    self.master.after(int(delay_time * 1000))

                elif module_type == "Wave Cap":
                    self.status_console.insert(tk.END, "Executing Waveform Capture...\n")
                    self.status_console.update()
                    self.execute_waveform_capture()  # Use the function defined before

                elif module_type == "Axis Control":
                    self.status_console.insert(tk.END, "Executing Axis Control...\n")
                    self.status_console.update()
                    self.execute_axis_control()      # Use the function defined before

                self.status_console.insert(tk.END, f"{module_type} completed\n\n")
                self.status_console.update()

            messagebox.showinfo("Execution Complete", "The script has been successfully executed.")
        except Exception as e:
            messagebox.showerror("Execution Error", f"An error occurred while running the script: {e}")

    def execute_waveform_capture(self):
        if not self.oscilloscope or not self.measure:
            self.status_console.insert(tk.END, "Oscilloscope is not connected.\n")
            return

        try:
            config_directory = os.path.dirname(self.script_path.get())  # Get sequence.json path
            config_path = os.path.join(config_directory, "waveform_config.json")

            with open(config_path, 'r') as config_file:
                config = json.load(config_file)

            # Get the save path and file name
            save_dir = config.get('save_directory')
            if not save_dir:
                save_dir = filedialog.askdirectory(title="Select Directory to Save Data")
            if not save_dir:
                self.status_console.insert(tk.END, "No save directory selected.\n")
                return

            # Get the file name entered by the user
            file_name = simpledialog.askstring("Input", "Enter file name:")
            if not file_name:
                self.status_console.insert(tk.END, "No file name provided.\n")
                return

            # Create a subdirectory with the filename as the subdirectory name
            full_save_dir = os.path.join(save_dir, file_name)
            if os.path.exists(full_save_dir):
                result = messagebox.askyesno("File Exists",
                                             "A folder with this name already exists. Do you want to overwrite it?")
                if not result:
                    return

            os.makedirs(full_save_dir, exist_ok=True)

            # Parsing Save Options
            save_screenshot = config['save_options'][0] == 1
            save_waveform_plot = config['save_options'][1] == 1
            save_csv = config['save_options'][2] == 1
            save_excel = config['save_options'][3] == 1

            # Save Screenshot
            if save_screenshot:
                screenshot_path = os.path.join(full_save_dir, f"{file_name}_screenshot.png")
                self.oscilloscope.capture_screenshot(screenshot_path)
                self.status_console.insert(tk.END, f"Screenshot saved at {screenshot_path}\n")
                # Plotting and saving Matplotlib waveforms
            if save_waveform_plot:
                # Assuming that waveforms are obtained from all the waveform data captured
                active_channels, waveforms = self.oscilloscope.capture_all_waveforms()

                if not waveforms:
                    self.status_console.insert(tk.END, "No waveform data captured.\n")
                    return

                # If the figure and ax are not set up in advance, they can be created here.
                figure = plt.figure(figsize=(8, 4), dpi=100)
                ax = figure.add_subplot(111)

                # Calling oscilloscope's drawing methods
                try:
                    self.oscilloscope.plot_all_waveforms(waveforms, ax, None)  # None is here because of don't need to show it in the GUI.

                    figure_path = os.path.join(full_save_dir, f"{file_name}_waveform_plot.png")
                    figure.savefig(figure_path)
                    plt.close(figure)  # Turn off figure to avoid memory leaks
                    self.status_console.insert(tk.END, f"Waveform plot saved at {figure_path}\n")
                except Exception as e:
                    self.status_console.insert(tk.END, f"Failed to plot waveform: {e}\n")

            # Save waveform data to CSV file
            if save_csv:
                csv_path = os.path.join(full_save_dir, f"{file_name}_waveform_data.csv")
                with open(csv_path, 'w') as f:
                    f.write("Time (s)")
                    for i in range(4):
                        if config['channels'][i] == 1:
                            f.write(f", Channel {i + 1} Amplitude (V)")
                    f.write("\n")

                    all_waveforms = []
                    for i in range(4):
                        if config['channels'][i] == 1:
                            time_values, waveform_data = self.oscilloscope.capture_waveform(i + 1)
                            all_waveforms.append((time_values, waveform_data))

                    for j in range(len(all_waveforms[0][0])):
                        f.write(f"{all_waveforms[0][0][j]}")
                        for _, waveform_data in all_waveforms:
                            f.write(f", {waveform_data[j]}")
                        f.write("\n")

            # Save measurements to Excel file
            if save_excel:
                excel_path = os.path.join(full_save_dir, f"{file_name}_measurements.xlsx")
                workbook = openpyxl.Workbook()
                sheet = workbook.active
                sheet.title = "Measurements"

                headers = ["Channel"] + [key for key, selected in config['measurements'].items() if selected == 1]
                sheet.append(headers)

                for i in range(4):
                    if config['channels'][i] == 1:
                        channel_data = [f"Channel {i + 1}"]

                        if config['measurements'].get("Vpp") == 1:
                            channel_data.append(self.measure.measure_vpp(i + 1))
                        if config['measurements'].get("Vmin") == 1:
                            channel_data.append(self.measure.measure_vmin(i + 1))
                        if config['measurements'].get("Vmax") == 1:
                            channel_data.append(self.measure.measure_vmax(i + 1))
                        if config['measurements'].get("Frequency") == 1:
                            channel_data.append(self.measure.measure_frequency(i + 1))
                        if config['measurements'].get("Pulse Width") == 1:
                            channel_data.append(self.measure.measure_pulse_width(i + 1))
                        if config['measurements'].get("Fall Time") == 1:
                            channel_data.append(self.measure.measure_fall_time(i + 1))
                        if config['measurements'].get("Rise Time") == 1:
                            channel_data.append(self.measure.measure_rise_time(i + 1))
                        if config['measurements'].get("Duty Cycle") == 1:
                            channel_data.append(self.measure.measure_duty_cycle(i + 1))
                        if config['measurements'].get("RMS Voltage") == 1:
                            channel_data.append(self.measure.measure_rms_voltage(i + 1))
                        if config['measurements'].get("Average Voltage") == 1:
                            channel_data.append(self.measure.measure_average_voltage(i + 1))
                        if config['measurements'].get("Amplitude") == 1:
                            channel_data.append(self.measure.measure_amplitude(i + 1))
                        if config['measurements'].get("Overshoot") == 1:
                            channel_data.append(self.measure.measure_overshoot(i + 1))
                        if config['measurements'].get("Preshoot") == 1:
                            channel_data.append(self.measure.measure_preshoot(i + 1))
                        if config['measurements'].get("Phase") == 1:
                            self.selected_channel_1 = 2  # Channel 2 is selected by default
                            self.selected_channel_2 = 3  # Channel 3 is selected by default
                            phase = self.measure.measure_phase(self.selected_channel_1, self.selected_channel_2)
                            channel_data.append(phase)
                        if config['measurements'].get("Edge Count") == 1:
                            channel_data.append(self.measure.measure_edge_count(i + 1))
                        if config['measurements'].get("Positive Edges") == 1:
                            channel_data.append(self.measure.measure_pos_edge_count(i + 1))
                        if config['measurements'].get("Negative Pulses") == 1:
                            channel_data.append(self.measure.measure_n_pulses(i + 1))
                        if config['measurements'].get("Positive Pulses") == 1:
                            channel_data.append(self.measure.measure_p_pulses(i + 1))
                        if config['measurements'].get("XMin") == 1:
                            channel_data.append(self.measure.measure_xmin(i + 1))
                        if config['measurements'].get("XMax") == 1:
                            channel_data.append(self.measure.measure_xmax(i + 1))
                        if config['measurements'].get("VTop") == 1:
                            channel_data.append(self.measure.measure_vtop(i + 1))
                        if config['measurements'].get("VBase") == 1:
                            channel_data.append(self.measure.measure_vbase(i + 1))
                        if config['measurements'].get("VRatio") == 1:
                            channel_data.append(self.measure.measure_vratio(i + 1))

                        sheet.append(channel_data)

                workbook.save(excel_path)
                self.status_console.insert(tk.END, f"Measurements saved at {excel_path}\n")

            self.status_console.insert(tk.END, "Waveform Capture completed.\n")
        except Exception as e:
            self.status_console.insert(tk.END, f"Waveform Capture failed: {e}\n")

    def execute_axis_control(self):
        if not self.oscilloscope:
            self.status_console.insert(tk.END, "Oscilloscope is not connected.\n")
            return

        try:
            # Use the last selected directory path
            config_directory = os.path.dirname(self.script_path.get())
            config_path = os.path.join(config_directory, "axis_config.json")

            with open(config_path, 'r') as config_file:
                config = json.load(config_file)

            # Set timebase settings
            timebase_scale = config['timebase']['scale']
            timebase_position = config['timebase']['position']
            self.oscilloscope.set_timebase_scale(timebase_scale)
            self.oscilloscope.set_timebase_position(timebase_position)
            self.status_console.insert(tk.END,
                                       f"Timebase set to scale: {timebase_scale}, position: {timebase_position}\n")

            # Configure channels
            for channel, settings in config['channels'].items():
                channel_num = int(channel.split('_')[-1])  # Extraction Channel Number
                scale = settings['scale']
                position = settings['position']
                self.oscilloscope.set_channel_scale(channel_num, scale)
                self.oscilloscope.set_channel_position(channel_num, position)
                self.status_console.insert(tk.END,
                                           f"Channel {channel_num} set to scale: {scale}, position: {position}\n")

            # Set markers
            for i, marker in enumerate(config['markers']):
                x = marker['x']
                y = marker['y']
                if i == 0:
                    self.oscilloscope.add_marker_x1(x)
                    self.oscilloscope.add_marker_y1(y)
                    self.status_console.insert(tk.END, f"Marker 1 set to x: {x}, y: {y}\n")
                elif i == 1:
                    self.oscilloscope.add_marker_x2(x)
                    self.oscilloscope.add_marker_y2(y)
                    self.status_console.insert(tk.END, f"Marker 2 set to x: {x}, y: {y}\n")

            self.status_console.insert(tk.END, "Axis Control completed.\n")
        except Exception as e:
            self.status_console.insert(tk.END, f"Axis Control failed: {e}\n")


# Test main function
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1000x750")
    app = RunScriptPage(master=root)
    root.mainloop()
