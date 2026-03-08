import tkinter as tk
from tkinter import filedialog, messagebox

from keysight_software import config
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

try:
    import pyvisa
except ImportError:  # pragma: no cover - optional at import time
    pyvisa = None


class ConfigHome(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=COLORS["background"])
        self.grid(row=0, column=0, sticky="nsew")
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.build_overview()
        self.build_forms()
        self.build_log()
        self.try_auto_detect_visa_address()

    def build_overview(self):
        card, inner = create_card(self, padding=28)
        card.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 18))
        inner.grid_columnconfigure((0, 1, 2), weight=1)

        create_section_heading(
            inner,
            "Bench configuration",
            "Start with connection defaults, confirm the VISA endpoint, then save a clean workspace baseline.",
        ).grid(row=0, column=0, columnspan=3, sticky="w")

        stats = [
            ("Default VISA", config.VISA_ADDRESS),
            ("Timeout", f"{config.GLOBAL_TIMEOUT} ms"),
            ("Base output", config.BASE_DIRECTORY),
        ]
        for column, (label, value) in enumerate(stats):
            stat = tk.Frame(inner, bg=COLORS["surface_alt"], padx=16, pady=16)
            stat.grid(row=1, column=column, sticky="ew", padx=(0, 12 if column < 2 else 0), pady=(20, 0))
            create_label(stat, label, muted=True).pack(anchor="w")
            create_label(stat, value, font=("SF Pro Text", 11, "bold"), wraplength=240, justify="left").pack(
                anchor="w", pady=(8, 0)
            )

    def build_forms(self):
        instrument_card, instrument = create_card(self, padding=28)
        instrument_card.grid(row=1, column=0, sticky="nsew", padx=(0, 9), pady=(0, 18))
        instrument.grid_columnconfigure(0, weight=1)

        create_section_heading(
            instrument,
            "Instrument",
            "Find the active VISA resource, adjust the communication timeout and verify the link live.",
        ).grid(row=0, column=0, sticky="w")

        self.visa_entry = self.create_labeled_entry(instrument, 1, "VISA Address", config.VISA_ADDRESS)
        self.timeout_entry = self.create_labeled_entry(instrument, 2, "Global Timeout (ms)", config.GLOBAL_TIMEOUT)

        action_row = tk.Frame(instrument, bg=instrument.cget("bg"))
        action_row.grid(row=3, column=0, sticky="w", pady=(14, 0))
        create_button(action_row, "Detect VISA Address", self.detect_visa_address, tone="secondary").pack(
            side="left", padx=(0, 10)
        )
        create_button(action_row, "Connect", self.connect_visa, tone="primary").pack(side="left")

        storage_card, storage = create_card(self, padding=28)
        storage_card.grid(row=1, column=1, sticky="nsew", padx=(9, 0), pady=(0, 18))
        storage.grid_columnconfigure(0, weight=1)

        create_section_heading(
            storage,
            "Workspace defaults",
            "Define where captures land and the filename prefix used by the rest of the workflow.",
        ).grid(row=0, column=0, sticky="w")

        self.directory_entry = self.create_labeled_entry(storage, 1, "Base Directory", config.BASE_DIRECTORY)
        browse_row = tk.Frame(storage, bg=storage.cget("bg"))
        browse_row.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        create_button(browse_row, "Browse Folder", self.browse_directory, tone="secondary").pack(side="left")

        self.filename_entry = self.create_labeled_entry(storage, 3, "Base File Name", config.BASE_FILENAME)

        save_row = tk.Frame(storage, bg=storage.cget("bg"))
        save_row.grid(row=4, column=0, sticky="w", pady=(18, 0))
        create_button(save_row, "Save Configuration", self.save_config, tone="primary").pack(side="left")

    def build_log(self):
        log_card, log = create_card(self, padding=28)
        log_card.grid(row=2, column=0, columnspan=2, sticky="nsew")
        log.grid_columnconfigure(0, weight=1)
        log.grid_rowconfigure(1, weight=1)

        create_section_heading(
            log,
            "Connection log",
            "Lightweight diagnostics for VISA discovery and connection attempts.",
        ).grid(row=0, column=0, sticky="w")

        self.log_output = create_scrolled_text(log, height=14, mono=True)
        self.log_output.grid(row=1, column=0, sticky="nsew", pady=(18, 0))

    def create_labeled_entry(self, parent, row, label, value):
        wrapper = tk.Frame(parent, bg=parent.cget("bg"))
        wrapper.grid(row=row, column=0, sticky="ew", pady=(18 if row > 1 else 20, 0))
        wrapper.grid_columnconfigure(0, weight=1)
        create_label(wrapper, label, muted=True).grid(row=0, column=0, sticky="w")
        entry = create_entry(wrapper)
        entry.grid(row=1, column=0, sticky="ew", pady=(8, 0), ipady=10)
        entry.insert(0, value)
        return entry

    def log_message(self, message):
        append_text(self.log_output, message + "\n")

    def try_auto_detect_visa_address(self):
        if pyvisa is None:
            self.log_message("pyvisa is not installed. Please enter the VISA address manually.")
            return
        try:
            rm = pyvisa.ResourceManager()
            resources = rm.list_resources()
            if resources:
                self.visa_entry.delete(0, tk.END)
                self.visa_entry.insert(0, resources[0])
                self.log_message(f"Found VISA address: {resources[0]}")
            else:
                self.log_message("No devices found. Please enter the VISA address manually.")
        except Exception as error:
            self.log_message(f"Auto detection failed: {error}")

    def detect_visa_address(self):
        self.try_auto_detect_visa_address()

    def connect_visa(self):
        if pyvisa is None:
            messagebox.showerror("Connection Failed", "pyvisa is not installed in the current Python environment.")
            return
        try:
            rm = pyvisa.ResourceManager()
            scope = rm.open_resource(self.visa_entry.get())
            self.log_message(f"Connected to: {scope.query('*IDN?').strip()}")
            scope.close()
        except pyvisa.errors.VisaIOError as error:
            messagebox.showerror("Connection Failed", f"Could not connect to the oscilloscope: {error}")
        except Exception as error:
            messagebox.showerror("Connection Failed", f"An unexpected error occurred: {error}")

    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.directory_entry.delete(0, tk.END)
            self.directory_entry.insert(0, directory)

    def save_config(self):
        config.update_visa_address(self.visa_entry.get())
        config.update_global_timeout(int(self.timeout_entry.get()))
        config.update_base_directory(self.directory_entry.get())
        config.update_base_filename(self.filename_entry.get())

        self.log_message(f"Saved VISA address: {config.VISA_ADDRESS}")
        self.log_message(f"Saved timeout: {config.GLOBAL_TIMEOUT}")
        self.log_message(f"Saved base directory: {config.BASE_DIRECTORY}")
        self.log_message(f"Saved base file name: {config.BASE_FILENAME}")
        self.log_message("Configuration saved successfully.")
