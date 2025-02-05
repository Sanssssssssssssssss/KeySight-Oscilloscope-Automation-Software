"""
===================================================
Created on: 21-7-2024
Author: Chang Xu
File: batch_process.py
Version: 1.1
Language: Python 3.12.3
Description:
This script provides a batch processing interface
for managing and merging measurement data from multiple
subdirectories. It automates data extraction, processing,
and final report generation for Keysight oscilloscope data.
===================================================
"""


import os
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import shutil
import pandas as pd


class BatchProcessPage:
    def __init__(self, master):
        self.master = master

        # Select main directory
        self.dir_label = tk.Label(master, text="Select Main Directory:", bg="white", bd=0)
        self.dir_label.grid(row=0, column=0, padx=10, pady=10, sticky='w')

        self.dir_entry = tk.Entry(master, width=80)
        self.dir_entry.grid(row=0, column=1, padx=10, pady=10)

        self.browse_button = tk.Button(master, text="Browse...", command=self.browse_directory)
        self.browse_button.grid(row=0, column=2, padx=10, pady=10)

        # Console output box
        self.console_output = scrolledtext.ScrolledText(master, width=112, height=30, wrap=tk.WORD, bg='black',
                                                        fg='white')
        self.console_output.grid(row=1, column=0, columnspan=3, padx=10, pady=10)

        # One-click processing button
        self.process_button = tk.Button(master, text="Start Batch Processing", command=self.start_batch_processing,
                                        width=20, height=3, font=('Helvetica', 16, 'bold'))
        self.process_button.grid(row=2, column=0, columnspan=3, pady=100)  # Use columnspan = 3 to center the button

    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)
            self.console_output.insert(tk.END, f"Selected directory: {directory}\n")
            self.list_subdirectories(directory)  # List subdirectories

    def list_subdirectories(self, directory):
        subdirs = [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d)) and d != "Final_Process"]
        if subdirs:
            self.console_output.insert(tk.END, "Loaded the following file IDs:\n")
            for subdir in subdirs:
                self.console_output.insert(tk.END, f"- {subdir}\n")# List subdirectories
        else:
            self.console_output.insert(tk.END, "No subdirectories found.\n")

    def start_batch_processing(self):
        """
        Start batch processing of measurement data from subdirectories.

        This function scans the selected main directory, identifies subdirectories
        containing measurement files, processes and merges them, and then saves
        the final merged dataset in a designated 'Final_Process' folder.

        - Reads measurement files from each subdirectory.
        - Merges measurement data into a single DataFrame.
        - Copies non-measurement files to the 'Final_Process' folder.
        - Saves the final merged dataset as an Excel file.
        """

        # Get the selected main directory from the input field
        main_directory = self.dir_entry.get()
        if not main_directory:
            messagebox.showwarning("No Directory Selected", "Please select a main directory first.")
            return

        # Display message in the console output
        self.console_output.insert(tk.END, "Starting batch processing...\n")
        self.master.update_idletasks()  # Update GUI to reflect changes

        # Define the final output directory
        final_process_dir = os.path.join(main_directory, "Final_Process")
        os.makedirs(final_process_dir, exist_ok=True)  # Create if not exists

        # Initialize an empty DataFrame to store merged measurement data
        merged_data = pd.DataFrame()

        # Iterate through each subdirectory inside the main directory
        for subdir in os.listdir(main_directory):
            subdir_path = os.path.join(main_directory, subdir)

            # Skip if it's not a directory or if it's the final output directory
            if os.path.isdir(subdir_path) and subdir != "Final_Process":
                self.console_output.insert(tk.END, f"Processing {subdir}...\n")

                # Find measurement files inside the current subdirectory
                measurement_files = self.find_measurement_files(subdir_path)
                if measurement_files:
                    for file in measurement_files:
                        data = pd.read_excel(file)

                        # Check if the first column is unnamed and rename it as 'Channel'
                        if 'Unnamed' in data.columns[0]:
                            data.rename(columns={data.columns[0]: 'Channel'}, inplace=True)
                        elif 'Channel' not in data.columns:
                            # If no 'Channel' column exists, use the first column as 'Channel'
                            data.insert(0, 'Channel', data.columns[0])

                            # Insert the subdirectory name as an 'ID' column for identification
                        data.insert(0, 'ID', subdir)

                        # Append the processed data to the merged DataFrame
                        merged_data = pd.concat([merged_data, data], ignore_index=True)

                    self.console_output.insert(tk.END, f"Merged measurement data for {subdir}\n")

                # Copy all non-measurement files from subdirectory to 'Final_Process' folder
                for file_name in os.listdir(subdir_path):
                    if not file_name.lower().startswith('measurements'):
                        shutil.copy(os.path.join(subdir_path, file_name), final_process_dir)
                        self.console_output.insert(tk.END, f"Copied {file_name} to Final_Process\n")

        # Save the merged dataset if there is data available
        if not merged_data.empty:
            merged_data.to_excel(os.path.join(final_process_dir, "final_merged_measurements.xlsx"), index=False)
            self.console_output.insert(tk.END, "Final merged measurements saved.\n")
        else:
            self.console_output.insert(tk.END, "No measurements files found for merging.\n")

        # Indicate that batch processing is completed
        self.console_output.insert(tk.END, "Batch processing completed.\n")
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
