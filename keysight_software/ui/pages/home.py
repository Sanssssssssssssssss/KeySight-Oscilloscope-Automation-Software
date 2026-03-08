import tkinter as tk
from tkinter import filedialog

from keysight_software import config
from keysight_software.ui.theme import (
    COLORS,
    append_text,
    create_badge,
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


RESPONSIVE_BREAKPOINT = 1280


class ConfigHome(tk.Frame):
    def __init__(self, master, connect_callback=None, connection_error=None):
        super().__init__(master, bg=COLORS["background"])
        self.connect_callback = connect_callback
        self.connection_error = connection_error
        self.grid(row=0, column=0, sticky="nsew")
        self.grid_columnconfigure(0, weight=7)
        self.grid_columnconfigure(1, weight=5)
        self.grid_rowconfigure(2, weight=1)
        self.bind("<Configure>", self.on_resize)

        self.build_hero()
        self.build_forms()
        self.build_log()
        self.try_auto_detect_visa_address()

    def build_hero(self):
        self.hero_card = tk.Frame(self, bg="#f7fbff", bd=1, relief="solid", padx=24, pady=24)
        self.hero_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 16))
        self.hero_card.grid_columnconfigure(0, weight=1)

        accent_bar = tk.Frame(self.hero_card, bg=COLORS["accent"], height=4)
        accent_bar.grid(row=0, column=0, sticky="ew")

        top = tk.Frame(self.hero_card, bg="#f7fbff")
        top.grid(row=1, column=0, sticky="ew", pady=(18, 0))
        top.grid_columnconfigure(0, weight=1)

        badge_row = tk.Frame(top, bg="#f7fbff")
        badge_row.grid(row=0, column=0, sticky="w")
        create_badge(badge_row, "Bench onboarding", tone="accent").pack(side="left")
        create_badge(badge_row, "Offline-ready", tone="neutral").pack(side="left", padx=(10, 0))

        create_label(top, "Set up the bench like a product dashboard.", font=("SF Pro Display", 22, "bold")).grid(
            row=1, column=0, sticky="w", pady=(18, 0)
        )
        create_label(
            top,
            "Confirm the VISA target, lock down the output location, and keep the rest of the workflow aligned before you start capturing live data.",
            muted=True,
            wraplength=620,
            justify="left",
        ).grid(row=2, column=0, sticky="w", pady=(10, 0))

        action_row = tk.Frame(top, bg="#f7fbff")
        action_row.grid(row=3, column=0, sticky="w", pady=(20, 0))
        create_button(action_row, "Detect VISA Address", self.detect_visa_address, tone="secondary").pack(side="left")
        create_button(action_row, "Connect Instrument", self.connect_visa, tone="primary").pack(side="left", padx=(10, 0))

        self.stats_row = tk.Frame(self.hero_card, bg="#f7fbff")
        self.stats_row.grid(row=2, column=0, sticky="ew", pady=(22, 0))
        self.stats_row.grid_columnconfigure((0, 1, 2), weight=1)
        self.metric_cards = {}
        for column, (label, value, wrap) in enumerate(
            [
                ("Default VISA", config.VISA_ADDRESS, 280),
                ("Timeout", f"{config.GLOBAL_TIMEOUT} ms", 160),
                ("Base output", config.BASE_DIRECTORY, 220),
            ]
        ):
            card = tk.Frame(self.stats_row, bg=COLORS["surface"], padx=16, pady=16)
            card.grid(row=0, column=column, sticky="ew", padx=(0, 10 if column < 2 else 0))
            create_label(card, label, muted=True).pack(anchor="w")
            value_label = create_label(
                card,
                value,
                font=("SF Pro Text", 11, "bold"),
                wraplength=wrap,
                justify="left",
            )
            value_label.pack(anchor="w", pady=(8, 0))
            self.metric_cards[label] = value_label

        self.status_card = tk.Frame(self, bg=COLORS["surface"], bd=1, relief="solid", padx=22, pady=22)
        self.status_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=(0, 16))
        self.status_card.grid_columnconfigure(0, weight=1)

        create_section_heading(
            self.status_card,
            "Connection pulse",
            "A compact view of whether the app can talk to the instrument right now.",
        ).grid(row=0, column=0, sticky="w")

        badge_line = tk.Frame(self.status_card, bg=COLORS["surface"])
        badge_line.grid(row=1, column=0, sticky="w", pady=(18, 0))
        create_label(badge_line, "Status", muted=True).pack(side="left")
        tone = "warning" if self.connection_error else "success"
        text = "Offline mode" if self.connection_error else "Ready"
        self.connection_badge = create_badge(badge_line, text, tone=tone)
        self.connection_badge.pack(side="left", padx=(10, 0))

        self.connection_summary = create_label(
            self.status_card,
            "Detection and connection feedback will appear here.",
            muted=True,
            wraplength=320,
            justify="left",
        )
        self.connection_summary.grid(row=2, column=0, sticky="w", pady=(12, 0))

        quick_notes = tk.Frame(self.status_card, bg=COLORS["surface"])
        quick_notes.grid(row=3, column=0, sticky="ew", pady=(18, 0))
        quick_notes.grid_columnconfigure((0, 1), weight=1)
        self.build_note_tile(
            quick_notes,
            0,
            "Live capture",
            "Disabled until the scope responds successfully.",
            "#fff8ec",
        )
        self.build_note_tile(
            quick_notes,
            1,
            "Workspace profile",
            "Saved settings here feed the rest of the UI.",
            "#f7f7fb",
        )

    def build_note_tile(self, parent, column, title, body, background):
        tile = tk.Frame(parent, bg=background, padx=16, pady=14)
        tile.grid(row=0, column=column, sticky="ew", padx=(0, 10 if column == 0 else 0))
        create_label(tile, title, font=("SF Pro Text", 10, "bold")).pack(anchor="w")
        create_label(tile, body, muted=True, wraplength=150, justify="left").pack(anchor="w", pady=(6, 0))

    def build_forms(self):
        self.instrument_card, instrument = create_card(self, padding=22)
        self.instrument_card.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=(0, 16))
        instrument.grid_columnconfigure(0, weight=1)
        instrument.grid_columnconfigure(1, weight=1)

        create_section_heading(
            instrument,
            "Instrument",
            "Use compact controls here to refine the connection target without opening a separate dialog.",
        ).grid(row=0, column=0, columnspan=2, sticky="w")

        self.visa_entry = self.create_compact_field(instrument, 1, 0, "VISA Address", config.VISA_ADDRESS, columnspan=2)
        self.timeout_entry = self.create_compact_field(
            instrument, 2, 0, "Global Timeout (ms)", config.GLOBAL_TIMEOUT
        )

        action_box = tk.Frame(instrument, bg=instrument.cget("bg"))
        action_box.grid(row=2, column=1, sticky="e", pady=(18, 0))
        create_button(action_box, "Detect", self.detect_visa_address, tone="secondary").pack(side="left")
        create_button(action_box, "Connect", self.connect_visa, tone="primary").pack(side="left", padx=(10, 0))

        self.storage_card, storage = create_card(self, padding=22)
        self.storage_card.grid(row=1, column=1, sticky="nsew", padx=(10, 0), pady=(0, 16))
        storage.grid_columnconfigure(0, weight=1)
        storage.grid_columnconfigure(1, weight=1)

        create_section_heading(
            storage,
            "Workspace defaults",
            "Keep naming and output consistent so later export steps require fewer manual fixes.",
        ).grid(row=0, column=0, columnspan=2, sticky="w")

        self.directory_entry = self.create_compact_field(storage, 1, 0, "Base Directory", config.BASE_DIRECTORY, columnspan=2)
        self.filename_entry = self.create_compact_field(storage, 2, 0, "Base File Name", config.BASE_FILENAME)

        utility_box = tk.Frame(storage, bg=storage.cget("bg"))
        utility_box.grid(row=2, column=1, sticky="e", pady=(18, 0))
        create_button(utility_box, "Browse", self.browse_directory, tone="secondary").pack(side="left")
        create_button(utility_box, "Save", self.save_config, tone="primary").pack(side="left", padx=(10, 0))

    def build_log(self):
        self.log_card, log = create_card(self, padding=22)
        self.log_card.grid(row=2, column=0, columnspan=2, sticky="nsew")
        log.grid_columnconfigure(0, weight=1)
        log.grid_rowconfigure(1, weight=1)

        create_section_heading(
            log,
            "Connection log",
            "A denser event stream for VISA discovery, validation, and save activity.",
        ).grid(row=0, column=0, sticky="w")

        self.log_output = create_scrolled_text(log, height=8, mono=True)
        self.log_output.grid(row=1, column=0, sticky="nsew", pady=(14, 0))

    def create_compact_field(self, parent, row, column, label, value, columnspan=1):
        wrapper = tk.Frame(parent, bg=parent.cget("bg"))
        wrapper.grid(row=row, column=column, columnspan=columnspan, sticky="ew", pady=(18, 0), padx=(0, 10 if column == 0 and columnspan == 1 else 0))
        wrapper.grid_columnconfigure(0, weight=1)
        create_label(wrapper, label, muted=True).grid(row=0, column=0, sticky="w")
        entry = create_entry(wrapper)
        entry.grid(row=1, column=0, sticky="ew", pady=(6, 0), ipady=8)
        entry.insert(0, value)
        return entry

    def on_resize(self, _event):
        width = self.winfo_width()
        stacked = bool(width and width < RESPONSIVE_BREAKPOINT)
        if stacked:
            self.hero_card.grid_configure(row=0, column=0, columnspan=2, padx=0)
            self.status_card.grid_configure(row=1, column=0, columnspan=2, padx=0)
            self.instrument_card.grid_configure(row=2, column=0, columnspan=2, padx=0)
            self.storage_card.grid_configure(row=3, column=0, columnspan=2, padx=0)
            self.log_card.grid_configure(row=4, column=0, columnspan=2)
        else:
            self.hero_card.grid_configure(row=0, column=0, columnspan=1, padx=(0, 10))
            self.status_card.grid_configure(row=0, column=1, columnspan=1, padx=(10, 0))
            self.instrument_card.grid_configure(row=1, column=0, columnspan=1, padx=(0, 10))
            self.storage_card.grid_configure(row=1, column=1, columnspan=1, padx=(10, 0))
            self.log_card.grid_configure(row=2, column=0, columnspan=2)

    def set_connection_badge(self, text, tone, summary=None):
        self.connection_badge.configure(text=text)
        palette = {
            "success": ("#e7f6ec", COLORS["success"]),
            "warning": ("#fff5e6", COLORS["warning"]),
            "danger": ("#fff1f2", COLORS["danger"]),
        }
        bg, fg = palette[tone]
        self.connection_badge.configure(bg=bg, fg=fg)
        if summary:
            self.connection_summary.configure(text=summary)

    def update_metric_cards(self):
        self.metric_cards["Default VISA"].configure(text=config.VISA_ADDRESS)
        self.metric_cards["Timeout"].configure(text=f"{config.GLOBAL_TIMEOUT} ms")
        self.metric_cards["Base output"].configure(text=config.BASE_DIRECTORY)

    def log_message(self, message):
        append_text(self.log_output, message + "\n")

    def try_auto_detect_visa_address(self):
        if pyvisa is None:
            self.set_connection_badge(
                "Manual setup",
                "warning",
                "pyvisa is not installed, so automatic discovery is unavailable in this environment.",
            )
            self.log_message("pyvisa is not installed. Please enter the VISA address manually.")
            return
        try:
            rm = pyvisa.ResourceManager()
            resources = rm.list_resources()
            if resources:
                self.visa_entry.delete(0, tk.END)
                self.visa_entry.insert(0, resources[0])
                self.set_connection_badge(
                    "Device found",
                    "success",
                    "An address was discovered automatically. You can connect immediately or refine the timeout first.",
                )
                self.log_message(f"Found VISA address: {resources[0]}")
            else:
                self.set_connection_badge(
                    "No device found",
                    "warning",
                    "No VISA resource responded during discovery. Manual entry is still available.",
                )
                self.log_message("No devices found. Please enter the VISA address manually.")
        except Exception as error:
            self.set_connection_badge(
                "Auto detect failed",
                "warning",
                "Automatic discovery failed. Manual configuration is still available.",
            )
            self.log_message(f"Auto detection failed: {error}")

    def detect_visa_address(self):
        self.try_auto_detect_visa_address()

    def connect_visa(self):
        try:
            timeout = int(self.timeout_entry.get())
        except ValueError:
            self.set_connection_badge("Invalid timeout", "danger", "Timeout must be an integer value in milliseconds.")
            self.log_message("Timeout must be an integer value in milliseconds.")
            return

        config.update_visa_address(self.visa_entry.get().strip())
        config.update_global_timeout(timeout)
        self.update_metric_cards()

        if pyvisa is None:
            self.set_connection_badge(
                "Manual setup",
                "warning",
                "pyvisa is missing in the current environment, so live verification cannot be performed here.",
            )
            self.log_message("pyvisa is not installed in the current Python environment.")
            return

        try:
            rm = pyvisa.ResourceManager()
            scope = rm.open_resource(config.VISA_ADDRESS)
            scope.timeout = timeout
            self.set_connection_badge(
                "Connected",
                "success",
                "Live communication succeeded. The rest of the workflow can use this device immediately.",
            )
            self.log_message(f"Connected to: {scope.query('*IDN?').strip()}")
            scope.close()
            if self.connect_callback is not None:
                self.connect_callback(show_dialog=False)
        except pyvisa.errors.VisaIOError as error:
            self.set_connection_badge(
                "Connection failed",
                "warning",
                "The VISA target did not respond. Check cable, address, and vendor IO libraries.",
            )
            self.log_message(f"Could not connect to the oscilloscope: {error}")
        except Exception as error:
            self.set_connection_badge(
                "Connection failed",
                "warning",
                "The connection attempt ended unexpectedly. Review the log below for the raw error.",
            )
            self.log_message(f"An unexpected error occurred: {error}")

    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.directory_entry.delete(0, tk.END)
            self.directory_entry.insert(0, directory)

    def save_config(self):
        try:
            timeout = int(self.timeout_entry.get())
        except ValueError:
            self.set_connection_badge("Invalid timeout", "danger", "Timeout must be an integer value in milliseconds.")
            self.log_message("Timeout must be an integer value in milliseconds.")
            return

        config.update_visa_address(self.visa_entry.get().strip())
        config.update_global_timeout(timeout)
        config.update_base_directory(self.directory_entry.get())
        config.update_base_filename(self.filename_entry.get())
        self.update_metric_cards()

        self.set_connection_badge(
            "Profile saved",
            "success",
            "Workspace defaults were stored successfully and are now reflected across the app.",
        )
        self.log_message(f"Saved VISA address: {config.VISA_ADDRESS}")
        self.log_message(f"Saved timeout: {config.GLOBAL_TIMEOUT}")
        self.log_message(f"Saved base directory: {config.BASE_DIRECTORY}")
        self.log_message(f"Saved base file name: {config.BASE_FILENAME}")
        self.log_message("Configuration saved successfully.")
