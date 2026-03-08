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


import json
import os

import openpyxl
import tkinter as tk
from matplotlib import pyplot as plt
from tkinter import filedialog, messagebox, simpledialog

from keysight_software.config import VISA_ADDRESS
from keysight_software.device.measure import Measure
from keysight_software.device.oscilloscope import Oscilloscope
from keysight_software.ui.theme import (
    COLORS,
    append_text,
    create_button,
    create_card,
    create_entry,
    create_scrolled_text,
    create_section_heading,
)
from keysight_software.utils.waveform import (
    build_measurement_row,
    collect_channel_measurements,
    collect_shared_measurements,
    get_selected_measurement_headers,
    write_waveforms_to_csv,
)


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
        self.configure(bg=COLORS["background"])
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        picker_card, picker = create_card(self, padding=24)
        picker_card.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        picker.grid_columnconfigure(0, weight=1)
        create_section_heading(
            picker,
            "Script runner",
            "Pick a saved automation sequence, preview the module order and execute it against the instrument.",
        ).grid(row=0, column=0, sticky="w")
        self.path_entry = create_entry(picker, textvariable=self.script_path)
        self.path_entry.grid(row=1, column=0, sticky="ew", pady=(16, 0), ipady=10)
        action_row = tk.Frame(picker, bg=picker.cget("bg"))
        action_row.grid(row=2, column=0, sticky="w", pady=(16, 0))
        create_button(action_row, "Browse Script Folder", self.browse_script, tone="secondary").pack(
            side="left", padx=(0, 10)
        )
        create_button(action_row, "Run Script", self.run_script, tone="primary").pack(side="left")

        sequence_card, sequence = create_card(self, padding=24)
        sequence_card.grid(row=1, column=0, sticky="nsew", pady=(0, 12))
        sequence.grid_columnconfigure(0, weight=1)
        sequence.grid_rowconfigure(1, weight=1)
        create_section_heading(sequence, "Script sequence").grid(row=0, column=0, sticky="w")
        self.script_console = create_scrolled_text(sequence, height=12, mono=True)
        self.script_console.grid(row=1, column=0, sticky="nsew", pady=(16, 0))

        status_card, status = create_card(self, padding=24)
        status_card.grid(row=2, column=0, sticky="nsew")
        status.grid_columnconfigure(0, weight=1)
        status.grid_rowconfigure(1, weight=1)
        create_section_heading(status, "Execution status").grid(row=0, column=0, sticky="w")
        self.status_console = create_scrolled_text(status, height=12, mono=True)
        self.status_console.grid(row=1, column=0, sticky="nsew", pady=(16, 0))

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
                    append_text(self.script_console, f"{i + 1}. {module['type']}\n")
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
                append_text(self.status_console, f"Running: {module_type}\n")
                self.status_console.update()

                if module_type == "Delay":
                    delay_time = module.get("delay", 1.0)
                    append_text(self.status_console, f"Waiting for {delay_time} seconds...\n")
                    self.status_console.update()
                    self.master.after(int(delay_time * 1000))

                elif module_type == "Wave Cap":
                    append_text(self.status_console, "Executing Waveform Capture...\n")
                    self.status_console.update()
                    self.execute_waveform_capture()  # Use the function defined before

                elif module_type == "Axis Control":
                    append_text(self.status_console, "Executing Axis Control...\n")
                    self.status_console.update()
                    self.execute_axis_control()      # Use the function defined before

                append_text(self.status_console, f"{module_type} completed\n\n")
                self.status_console.update()

            messagebox.showinfo("Execution Complete", "The script has been successfully executed.")
        except Exception as e:
            messagebox.showerror("Execution Error", f"An error occurred while running the script: {e}")

    def execute_waveform_capture(self):
        if not self.oscilloscope or not self.measure:
            append_text(self.status_console, "Oscilloscope is not connected.\n")
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
                append_text(self.status_console, "No save directory selected.\n")
                return

            # Get the file name entered by the user
            file_name = simpledialog.askstring("Input", "Enter file name:")
            if not file_name:
                append_text(self.status_console, "No file name provided.\n")
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

            selected_channels = [
                index + 1
                for index, enabled in enumerate(config.get('channels', []))
                if enabled == 1
            ]
            if not selected_channels:
                append_text(self.status_console, "No channels selected in the waveform configuration.\n")
                return

            selected_measurements = config.get('measurements', {})
            waveforms = {}
            if save_waveform_plot or save_csv:
                for channel in selected_channels:
                    waveforms[channel] = self.oscilloscope.capture_waveform(channel)

            # Save Screenshot
            if save_screenshot:
                screenshot_path = os.path.join(full_save_dir, f"{file_name}_screenshot.png")
                self.oscilloscope.capture_screenshot(screenshot_path)
                append_text(self.status_console, f"Screenshot saved at {screenshot_path}\n")
                # Plotting and saving Matplotlib waveforms
            if save_waveform_plot:
                if not waveforms:
                    append_text(self.status_console, "No waveform data captured.\n")
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
                    append_text(self.status_console, f"Waveform plot saved at {figure_path}\n")
                except Exception as e:
                    append_text(self.status_console, f"Failed to plot waveform: {e}\n")

            # Save waveform data to CSV file
            if save_csv:
                csv_path = os.path.join(full_save_dir, f"{file_name}_waveform_data.csv")
                write_waveforms_to_csv(csv_path, waveforms)
                append_text(self.status_console, f"Waveform data saved at {csv_path}\n")

            # Save measurements to Excel file
            if save_excel:
                excel_path = os.path.join(full_save_dir, f"{file_name}_measurements.xlsx")
                workbook = openpyxl.Workbook()
                sheet = workbook.active
                sheet.title = "Measurements"

                headers = ["Channel"] + get_selected_measurement_headers(selected_measurements)
                sheet.append(headers)

                phase_channels = selected_channels[:2] if len(selected_channels) >= 2 else [1, 2]
                shared_measurements = collect_shared_measurements(
                    self.measure,
                    selected_measurements,
                    phase_channels[0],
                    phase_channels[1],
                )
                for channel in selected_channels:
                    channel_measurements = collect_channel_measurements(
                        self.measure,
                        selected_measurements,
                        channel,
                    )
                    channel_data = build_measurement_row(
                        channel,
                        selected_measurements,
                        channel_measurements,
                        shared_measurements,
                    )
                    sheet.append(channel_data)

                workbook.save(excel_path)
                append_text(self.status_console, f"Measurements saved at {excel_path}\n")

            append_text(self.status_console, "Waveform Capture completed.\n")
        except Exception as e:
            append_text(self.status_console, f"Waveform Capture failed: {e}\n")

    def execute_axis_control(self):
        if not self.oscilloscope:
            append_text(self.status_console, "Oscilloscope is not connected.\n")
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
            append_text(self.status_console, f"Timebase set to scale: {timebase_scale}, position: {timebase_position}\n")

            # Configure channels
            for channel, settings in config['channels'].items():
                channel_num = int(channel.split('_')[-1])  # Extraction Channel Number
                scale = settings['scale']
                position = settings['position']
                self.oscilloscope.set_channel_scale(channel_num, scale)
                self.oscilloscope.set_channel_position(channel_num, position)
                append_text(self.status_console, f"Channel {channel_num} set to scale: {scale}, position: {position}\n")

            # Set markers
            for i, marker in enumerate(config['markers']):
                x = marker['x']
                y = marker['y']
                if i == 0:
                    self.oscilloscope.add_marker_x1(x)
                    self.oscilloscope.add_marker_y1(y)
                    append_text(self.status_console, f"Marker 1 set to x: {x}, y: {y}\n")
                elif i == 1:
                    self.oscilloscope.add_marker_x2(x)
                    self.oscilloscope.add_marker_y2(y)
                    append_text(self.status_console, f"Marker 2 set to x: {x}, y: {y}\n")

            append_text(self.status_console, "Axis Control completed.\n")
        except Exception as e:
            append_text(self.status_console, f"Axis Control failed: {e}\n")


# Test main function
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1000x750")
    app = RunScriptPage(master=root)
    root.mainloop()
