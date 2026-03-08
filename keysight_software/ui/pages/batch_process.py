import shutil

import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox

from keysight_software.ui.theme import (
    COLORS,
    append_text,
    create_button,
    create_card,
    create_entry,
    create_label,
    create_scrolled_text,
    create_section_heading,
)


class BatchProcessPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=COLORS["background"])
        self.master = master
        self.grid(row=0, column=0, sticky="nsew")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.directory_var = tk.StringVar()
        self.build_controls()
        self.build_console()

    def build_controls(self):
        card, inner = create_card(self, padding=28)
        card.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        inner.grid_columnconfigure(0, weight=1)

        create_section_heading(
            inner,
            "Batch merge",
            "Select a parent folder containing repeated run directories and merge the resulting measurement sheets.",
        ).grid(row=0, column=0, sticky="w")

        field = tk.Frame(inner, bg=inner.cget("bg"))
        field.grid(row=1, column=0, sticky="ew", pady=(20, 0))
        field.grid_columnconfigure(0, weight=1)
        create_label(field, "Main Directory", muted=True).grid(row=0, column=0, sticky="w")
        self.dir_entry = create_entry(field, textvariable=self.directory_var)
        self.dir_entry.grid(row=1, column=0, sticky="ew", pady=(8, 0), ipady=10)

        actions = tk.Frame(inner, bg=inner.cget("bg"))
        actions.grid(row=2, column=0, sticky="w", pady=(18, 0))
        create_button(actions, "Browse Folder", self.browse_directory, tone="secondary").pack(
            side="left", padx=(0, 10)
        )
        create_button(actions, "Start Batch Processing", self.start_batch_processing, tone="primary").pack(side="left")

    def build_console(self):
        card, inner = create_card(self, padding=28)
        card.grid(row=1, column=0, sticky="nsew")
        inner.grid_columnconfigure(0, weight=1)
        inner.grid_rowconfigure(1, weight=1)

        create_section_heading(
            inner,
            "Processing log",
            "Each subfolder is scanned, merged and copied into a final consolidated output package.",
        ).grid(row=0, column=0, sticky="w")

        self.console_output = create_scrolled_text(inner, height=22, mono=True)
        self.console_output.grid(row=1, column=0, sticky="nsew", pady=(18, 0))

    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.directory_var.set(directory)
            append_text(self.console_output, f"Selected directory: {directory}\n")
            self.list_subdirectories(directory)

    def list_subdirectories(self, directory):
        subdirs = [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d)) and d != "Final_Process"]
        if subdirs:
            append_text(self.console_output, "Loaded the following file IDs:\n")
            for subdir in subdirs:
                append_text(self.console_output, f"- {subdir}\n")
        else:
            append_text(self.console_output, "No subdirectories found.\n")

    def start_batch_processing(self):
        main_directory = self.dir_entry.get()
        if not main_directory:
            messagebox.showwarning("No Directory Selected", "Please select a main directory first.")
            return

        append_text(self.console_output, "Starting batch processing...\n")
        self.master.update_idletasks()

        final_process_dir = os.path.join(main_directory, "Final_Process")
        os.makedirs(final_process_dir, exist_ok=True)

        merged_data = pd.DataFrame()

        for subdir in os.listdir(main_directory):
            subdir_path = os.path.join(main_directory, subdir)
            if os.path.isdir(subdir_path) and subdir != "Final_Process":
                append_text(self.console_output, f"Processing {subdir}...\n")

                measurement_files = self.find_measurement_files(subdir_path)
                if measurement_files:
                    for file in measurement_files:
                        data = pd.read_excel(file)
                        if 'Unnamed' in data.columns[0]:
                            data.rename(columns={data.columns[0]: 'Channel'}, inplace=True)
                        elif 'Channel' not in data.columns:
                            data.insert(0, 'Channel', data.columns[0])
                        data.insert(0, 'ID', subdir)
                        merged_data = pd.concat([merged_data, data], ignore_index=True)
                    append_text(self.console_output, f"Merged measurement data for {subdir}\n")

                for file_name in os.listdir(subdir_path):
                    if not file_name.lower().startswith('measurements'):
                        shutil.copy(os.path.join(subdir_path, file_name), final_process_dir)
                        append_text(self.console_output, f"Copied {file_name} to Final_Process\n")

        if not merged_data.empty:
            merged_data.to_excel(os.path.join(final_process_dir, "final_merged_measurements.xlsx"), index=False)
            append_text(self.console_output, "Final merged measurements saved.\n")
        else:
            append_text(self.console_output, "No measurement files found for merging.\n")

        append_text(self.console_output, "Batch processing completed.\n")
        messagebox.showinfo("Process Completed", "Batch processing has been completed.")

    def find_measurement_files(self, directory):
        measurement_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if 'measurements' in file.lower() and file.endswith('.xlsx'):
                    measurement_files.append(os.path.join(root, file))
        return measurement_files


if __name__ == "__main__":
    root = tk.Tk()
    app = BatchProcessPage(root)
    root.mainloop()
