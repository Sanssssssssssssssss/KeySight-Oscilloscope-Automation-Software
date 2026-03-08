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

import tkinter as tk
import json
import os
from tkinter import ttk
from tkinter import filedialog, messagebox

import openpyxl  # Importing the openpyxl module to work with Excel files
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from keysight_software.config import VISA_ADDRESS
from keysight_software.device.measure import Measure
from keysight_software.device.oscilloscope import Oscilloscope
from keysight_software.paths import project_path
from keysight_software.ui.pages import settings
from keysight_software.ui.theme import (
    COLORS,
    append_text,
    create_button,
    create_card,
    create_checkbutton,
    create_entry,
    create_label,
    create_option_menu,
    create_scrolled_text,
    create_section_heading,
    style_toplevel,
)
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
        self.frame = tk.Frame(master, bg=COLORS["background"])
        self.frame.grid(row=0, column=0, sticky="nsew")
        self.frame.grid_columnconfigure(0, weight=2)
        self.frame.grid_columnconfigure(1, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)
        self.osc = oscilloscope
        self.measure = measure
        self.is_connected = self.check_connection()  # Add this line
        self.measurement_vars = [tk.StringVar(value="") for _ in range(4)]
        self.save_directory = settings.get_save_directory()  # Using paths in setting
        self.selected_measurements = {}  # For saving the user's measurement selections
        self.last_waveforms = {}
        self.last_channel_measurements = {}
        self.last_shared_measurements = {}

        self.figure = Figure(figsize=(8, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.selected_channel_1 = 1
        self.selected_channel_2 = 2

        self.build_layout()
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

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

    def build_layout(self):
        plot_card, plot_inner = create_card(self.frame, padding=26)
        plot_card.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 10))
        plot_inner.grid_columnconfigure(0, weight=1)
        plot_inner.grid_rowconfigure(1, weight=1)

        create_section_heading(
            plot_inner,
            "Waveform canvas",
            "Capture one or more channels, inspect the trace visually and export the latest acquisition.",
        ).grid(row=0, column=0, sticky="w")
        canvas_holder = tk.Frame(plot_inner, bg=COLORS["surface"])
        canvas_holder.grid(row=1, column=0, sticky="nsew", pady=(18, 0))
        self.canvas = FigureCanvasTkAgg(self.figure, master=canvas_holder)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        right_column = tk.Frame(self.frame, bg=COLORS["background"])
        right_column.grid(row=0, column=1, rowspan=2, sticky="nsew")
        right_column.grid_columnconfigure(0, weight=1)
        right_column.grid_rowconfigure(2, weight=1)
        right_column.grid_rowconfigure(3, weight=1)

        control_card, control_inner = create_card(right_column, padding=24)
        control_card.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        control_inner.grid_columnconfigure(0, weight=1)
        create_section_heading(
            control_inner,
            "Capture controls",
            "Choose active channels and measurement presets before triggering a new acquisition.",
        ).grid(row=0, column=0, sticky="w")

        self.channel_vars = [tk.IntVar() for _ in range(4)]
        channel_row = tk.Frame(control_inner, bg=control_inner.cget("bg"))
        channel_row.grid(row=1, column=0, sticky="ew", pady=(16, 0))
        for i in range(4):
            cb = create_checkbutton(channel_row, f"Channel {i + 1}", self.channel_vars[i])
            cb.pack(anchor="w")

        action_row = tk.Frame(control_inner, bg=control_inner.cget("bg"))
        action_row.grid(row=2, column=0, sticky="w", pady=(18, 0))
        self.capture_button = create_button(action_row, "Capture Waveform", self.capture_waveform, tone="primary")
        self.capture_button.pack(side="left", padx=(0, 10))
        create_button(
            action_row,
            "Select Measurements",
            self.open_measurement_selection_window,
            tone="secondary",
        ).pack(side="left")
        self.capture_button.config(state=tk.DISABLED if not self.is_connected else tk.NORMAL)

        export_card, export_inner = create_card(right_column, padding=24)
        export_card.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        export_inner.grid_columnconfigure(0, weight=1)
        create_section_heading(
            export_inner,
            "Export",
            "Save screenshots, plots, waveform CSVs and the latest calculated measurements.",
        ).grid(row=0, column=0, sticky="w")

        self.save_options = [tk.IntVar(value=1) for _ in range(4)]
        self.save_labels = ["Save Screenshot", "Save Plot", "Save CSV", "Save Measurements"]
        for index, label in enumerate(self.save_labels):
            create_checkbutton(export_inner, label, self.save_options[index]).grid(
                row=index + 1, column=0, sticky="w", pady=(12 if index == 0 else 8, 0)
            )

        name_field = tk.Frame(export_inner, bg=export_inner.cget("bg"))
        name_field.grid(row=5, column=0, sticky="ew", pady=(16, 0))
        name_field.grid_columnconfigure(0, weight=1)
        create_label(name_field, "File Name", muted=True).grid(row=0, column=0, sticky="w")
        self.filename_entry = create_entry(name_field)
        self.filename_entry.grid(row=1, column=0, sticky="ew", pady=(8, 0), ipady=10)

        create_button(export_inner, "Save Data", self.save_data, tone="primary").grid(
            row=6, column=0, sticky="w", pady=(18, 0)
        )

        measurement_card, measurement_inner = create_card(right_column, padding=24)
        measurement_card.grid(row=2, column=0, sticky="nsew", pady=(0, 12))
        measurement_inner.grid_columnconfigure(0, weight=1)
        measurement_inner.grid_rowconfigure(1, weight=1)
        create_section_heading(
            measurement_inner,
            "Measurement results",
            "Latest scalar outputs from the selected acquisition.",
        ).grid(row=0, column=0, sticky="w")
        self.console_output = create_scrolled_text(measurement_inner, height=12, mono=True)
        self.console_output.grid(row=1, column=0, sticky="nsew", pady=(16, 0))

        coord_card, coord_inner = create_card(right_column, padding=24)
        coord_card.grid(row=3, column=0, sticky="nsew")
        coord_inner.grid_columnconfigure(0, weight=1)
        coord_inner.grid_rowconfigure(1, weight=1)
        create_section_heading(
            coord_inner,
            "Cursor coordinates",
            "Live plot coordinates while moving across the waveform.",
        ).grid(row=0, column=0, sticky="w")
        self.coordinate_output = create_scrolled_text(coord_inner, height=8, mono=True)
        self.coordinate_output.grid(row=1, column=0, sticky="nsew", pady=(16, 0))

        self.detect_active_channels()

    def open_measurement_selection_window(self):
        '''Opens a window for users to select waveform measurement parameters.'''
        self.selection_window = tk.Toplevel(self.master)
        style_toplevel(self.selection_window, "Select Measurement Parameters", "460x620")

        container = ttk.Frame(self.selection_window)
        canvas = tk.Canvas(container, bg=COLORS["background"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS["background"])

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

        self.measurement_selection_vars = {
            name: tk.IntVar(value=saved_measurements.get(name, 0))
            for name in get_measurement_names()
        }

        card, inner = create_card(scrollable_frame, padding=22)
        card.pack(fill="both", expand=True, padx=16, pady=16)
        create_section_heading(
            inner,
            "Measurement preset",
            "Choose scalar measurements to calculate after each capture.",
        ).pack(anchor="w")
        for name, var in self.measurement_selection_vars.items():
            create_checkbutton(inner, name, var).pack(anchor='w', pady=(10, 0))

        dual_card, dual_inner = create_card(scrollable_frame, padding=22)
        dual_card.pack(fill="x", padx=16, pady=(0, 16))
        create_section_heading(
            dual_inner,
            "Dual-channel measurements",
            "Set the channel pair used for phase calculations.",
        ).pack(anchor="w")

        self.channel_1_var = tk.IntVar(value=self.selected_channel_1)
        self.channel_2_var = tk.IntVar(value=self.selected_channel_2)
        create_label(dual_inner, "Channel 1", muted=True).pack(anchor="w", pady=(16, 0))
        create_option_menu(dual_inner, self.channel_1_var, [1, 2, 3, 4]).pack(anchor="w", pady=(8, 0))
        create_label(dual_inner, "Channel 2", muted=True).pack(anchor="w", pady=(16, 0))
        create_option_menu(dual_inner, self.channel_2_var, [1, 2, 3, 4]).pack(anchor="w", pady=(8, 0))

        button_row = tk.Frame(scrollable_frame, bg=COLORS["background"])
        button_row.pack(fill="x", padx=16, pady=(0, 16))
        create_button(button_row, "Save Preset", self.save_measurement_selection, tone="primary").pack(anchor="e")

        self.selection_window.transient(self.master)
        self.selection_window.grab_set()
        self.master.wait_window(self.selection_window)

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
            self.osc.get_active_channels()
            return True
        except Exception as e:
            return False

    def on_mouse_move(self, event):
        '''Displays cursor coordinates in real-time when the mouse moves over the waveform plot.'''
        if event.inaxes:  # Make sure the mouse is in the drawing area
            x_data = event.xdata
            y_data = event.ydata
            append_text(self.coordinate_output, f"X: {x_data:.5f}, Y: {y_data:.5f}\n")

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
                append_text(self.console_output, f"{line}\n")

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
            append_text(self.console_output, f"{line}\n")

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
            append_text(self.console_output, f"Screenshot saved at {screenshot_path}\n")

        # Saving Matplotlib Waveforms
        if self.save_options[1].get():
            figure_path = os.path.join(full_save_dir, f"{file_name}_waveform_plot.png")
            self.figure.savefig(figure_path)
            append_text(self.console_output, f"Waveform plot saved at {figure_path}\n")

        # Save CSV file
        if self.save_options[2].get():
            csv_path = os.path.join(full_save_dir, f"{file_name}_waveform_data.csv")
            write_waveforms_to_csv(csv_path, self.last_waveforms)
            append_text(self.console_output, f"Waveform data saved at {csv_path}\n")

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
            append_text(self.console_output, f"Measurements saved at {excel_path}\n")


if __name__ == "__main__":
    root = tk.Tk()
    osc = Oscilloscope(VISA_ADDRESS, 10000)
    measure = Measure(osc)
    app = WaveformCapture(root, osc, measure)
    root.mainloop()
