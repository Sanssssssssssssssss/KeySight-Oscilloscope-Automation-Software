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


RESPONSIVE_BREAKPOINT = 1320


class ConfigHome(tk.Frame):
    def __init__(self, master, connect_callback=None, connection_error=None):
        super().__init__(master, bg=COLORS["background"])
        self.connect_callback = connect_callback
        self.connection_error = connection_error
        self.metric_labels = {}

        self.grid(row=0, column=0, sticky="nsew")
        self.grid_columnconfigure(0, weight=8)
        self.grid_columnconfigure(1, weight=4)
        self.grid_rowconfigure(2, weight=1)
        self.bind("<Configure>", self.on_resize)

        self.build_hero()
        self.build_control_center()
        self.build_log()
        self.try_auto_detect_visa_address()

    def build_hero(self):
        self.hero_card = tk.Canvas(
            self,
            height=280,
            bg=COLORS["surface"],
            bd=0,
            highlightthickness=1,
            highlightbackground="#d8e6fb",
        )
        self.hero_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 16))
        self.hero_card.bind("<Configure>", self.draw_hero_background)

        self.hero_content = tk.Frame(self.hero_card, bg=COLORS["surface"])
        self.hero_window = self.hero_card.create_window((0, 0), window=self.hero_content, anchor="nw")
        self.hero_content.grid_columnconfigure(0, weight=1)

        badge_row = tk.Frame(self.hero_content, bg=COLORS["surface"])
        badge_row.grid(row=0, column=0, sticky="w", pady=(22, 0))
        create_badge(badge_row, "Bench dashboard", tone="accent").pack(side="left")
        create_badge(badge_row, "Frontend-style preview", tone="neutral").pack(side="left", padx=(10, 0))

        create_label(
            self.hero_content,
            "A cleaner bench homepage with more product-like hierarchy.",
            font=("Segoe UI", 22, "bold"),
            wraplength=620,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(18, 0))
        create_label(
            self.hero_content,
            "The goal here is not to look like stock Tk. This screen behaves more like a compact dashboard: stronger headline, denser controls, clearer metrics, and less dead vertical space.",
            muted=True,
            wraplength=640,
            justify="left",
        ).grid(row=2, column=0, sticky="w", pady=(10, 0))

        action_row = tk.Frame(self.hero_content, bg=COLORS["surface"])
        action_row.grid(row=3, column=0, sticky="w", pady=(20, 0))
        create_button(action_row, "Detect VISA Address", self.detect_visa_address, tone="secondary").pack(side="left")
        create_button(action_row, "Connect Instrument", self.connect_visa, tone="primary").pack(side="left", padx=(10, 0))

        self.metric_row = tk.Frame(self.hero_content, bg=COLORS["surface"])
        self.metric_row.grid(row=4, column=0, sticky="ew", pady=(22, 0))
        self.metric_row.grid_columnconfigure((0, 1, 2), weight=1)

        metrics = [
            ("Default VISA", config.VISA_ADDRESS, 260),
            ("Timeout", f"{config.GLOBAL_TIMEOUT} ms", 150),
            ("Base output", config.BASE_DIRECTORY, 220),
        ]
        for column, (label, value, wraplength) in enumerate(metrics):
            card = tk.Frame(self.metric_row, bg="#f7faff", padx=16, pady=15)
            card.grid(row=0, column=column, sticky="ew", padx=(0, 10 if column < 2 else 0))
            create_label(card, label, muted=True).pack(anchor="w")
            value_label = create_label(
                card,
                value,
                font=("Segoe UI", 11, "bold"),
                wraplength=wraplength,
                justify="left",
            )
            value_label.pack(anchor="w", pady=(8, 0))
            self.metric_labels[label] = value_label

        self.hero_footer = create_label(
            self.hero_content,
            "Try this page first. If this direction feels right, the same visual language can be rolled out across Waveform Capture, Axis Control, and Script Editor.",
            muted=True,
            wraplength=640,
            justify="left",
        )
        self.hero_footer.grid(row=5, column=0, sticky="w", pady=(18, 22))

        self.hero_card.bind("<Configure>", self.sync_hero_window, add="+")

        self.status_stack = tk.Frame(self, bg=COLORS["background"])
        self.status_stack.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=(0, 16))
        self.status_stack.grid_columnconfigure(0, weight=1)

        self.status_card, status = create_card(self.status_stack, padding=20)
        self.status_card.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        status.grid_columnconfigure(0, weight=1)
        create_section_heading(
            status,
            "Connection pulse",
            "A compact status module rather than a full-width desktop form.",
        ).grid(row=0, column=0, sticky="w")

        badge_line = tk.Frame(status, bg=status.cget("bg"))
        badge_line.grid(row=1, column=0, sticky="w", pady=(16, 0))
        create_label(badge_line, "Status", muted=True).pack(side="left")
        tone = "warning" if self.connection_error else "success"
        text = "Offline mode" if self.connection_error else "Ready"
        self.connection_badge = create_badge(badge_line, text, tone=tone)
        self.connection_badge.pack(side="left", padx=(10, 0))

        self.connection_summary = create_label(
            status,
            "Waiting for automatic discovery or a manual connection attempt.",
            muted=True,
            wraplength=280,
            justify="left",
        )
        self.connection_summary.grid(row=2, column=0, sticky="w", pady=(12, 0))

        create_button(status, "Reconnect", lambda: self.connect_visa(), tone="secondary").grid(
            row=3, column=0, sticky="w", pady=(16, 0)
        )

        self.signal_card = tk.Frame(self.status_stack, bg="#0f172a", bd=0, padx=18, pady=18)
        self.signal_card.grid(row=1, column=0, sticky="ew")
        tk.Label(
            self.signal_card,
            text="Signal Notes",
            font=("Segoe UI", 12, "bold"),
            fg="#ffffff",
            bg="#0f172a",
        ).pack(anchor="w")
        tk.Label(
            self.signal_card,
            text="Live capture stays disabled until the scope responds. Saved profile values still apply immediately across the app.",
            fg="#cbd5e1",
            bg="#0f172a",
            font=("Segoe UI", 10),
            wraplength=280,
            justify="left",
        ).pack(anchor="w", pady=(8, 0))

    def draw_hero_background(self, event):
        width = max(event.width, 200)
        height = max(event.height, 200)
        self.hero_card.delete("bg")
        self.hero_card.create_rectangle(0, 0, width, height, fill="#ffffff", outline="", tags="bg")
        self.hero_card.create_rectangle(0, 0, width, 96, fill="#eef6ff", outline="", tags="bg")
        self.hero_card.create_oval(width - 180, -30, width + 60, 170, fill="#dbeafe", outline="", tags="bg")
        self.hero_card.create_oval(width - 110, 35, width + 120, 240, fill="#bfdbfe", outline="", tags="bg")
        self.hero_card.create_oval(width - 260, 120, width - 40, 300, fill="#eff6ff", outline="", tags="bg")
        self.hero_card.tag_lower("bg")

    def sync_hero_window(self, event):
        self.hero_card.itemconfigure(self.hero_window, width=event.width - 2)

    def build_control_center(self):
        self.control_card, control = create_card(self, padding=22)
        self.control_card.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(0, 16))
        control.grid_columnconfigure(0, weight=1)
        control.grid_columnconfigure(1, weight=1)

        create_section_heading(
            control,
            "Control center",
            "A denser, front-end-like configuration surface: fewer stacked rows, more paired inputs, and clearer action clusters.",
        ).grid(row=0, column=0, columnspan=2, sticky="w")

        instrument_shell = tk.Frame(control, bg=control.cget("bg"))
        instrument_shell.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=(18, 0))
        instrument_shell.grid_columnconfigure((0, 1), weight=1)
        create_label(instrument_shell, "Instrument target", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")
        create_label(
            instrument_shell,
            "Tune address and timeout without wasting vertical space.",
            muted=True,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))

        self.visa_entry = self.create_compact_field(instrument_shell, 2, 0, "VISA Address", config.VISA_ADDRESS, columnspan=2)
        self.timeout_entry = self.create_compact_field(instrument_shell, 3, 0, "Timeout (ms)", config.GLOBAL_TIMEOUT)

        instrument_actions = tk.Frame(instrument_shell, bg=instrument_shell.cget("bg"))
        instrument_actions.grid(row=3, column=1, sticky="e", pady=(16, 0))
        create_button(instrument_actions, "Detect", self.detect_visa_address, tone="secondary").pack(side="left")
        create_button(instrument_actions, "Connect", self.connect_visa, tone="primary").pack(side="left", padx=(10, 0))

        workspace_shell = tk.Frame(control, bg=control.cget("bg"))
        workspace_shell.grid(row=1, column=1, sticky="nsew", padx=(10, 0), pady=(18, 0))
        workspace_shell.grid_columnconfigure((0, 1), weight=1)
        create_label(workspace_shell, "Workspace profile", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")
        create_label(
            workspace_shell,
            "Keep storage and naming aligned with the rest of the automation workflow.",
            muted=True,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))

        self.directory_entry = self.create_compact_field(
            workspace_shell, 2, 0, "Base Directory", config.BASE_DIRECTORY, columnspan=2
        )
        self.filename_entry = self.create_compact_field(
            workspace_shell, 3, 0, "Base File Name", config.BASE_FILENAME
        )

        workspace_actions = tk.Frame(workspace_shell, bg=workspace_shell.cget("bg"))
        workspace_actions.grid(row=3, column=1, sticky="e", pady=(16, 0))
        create_button(workspace_actions, "Browse", self.browse_directory, tone="secondary").pack(side="left")
        create_button(workspace_actions, "Save", self.save_config, tone="primary").pack(side="left", padx=(10, 0))

    def build_log(self):
        self.log_card, log = create_card(self, padding=20)
        self.log_card.grid(row=2, column=0, columnspan=2, sticky="nsew")
        log.grid_columnconfigure(0, weight=1)
        log.grid_rowconfigure(1, weight=1)

        create_section_heading(
            log,
            "Connection log",
            "A compact event stream for VISA discovery, validation, and profile saves.",
        ).grid(row=0, column=0, sticky="w")

        self.log_output = create_scrolled_text(log, height=6, mono=True)
        self.log_output.grid(row=1, column=0, sticky="nsew", pady=(12, 0))

    def create_compact_field(self, parent, row, column, label, value, columnspan=1):
        wrapper = tk.Frame(parent, bg=parent.cget("bg"))
        padx = (0, 10) if column == 0 and columnspan == 1 else 0
        wrapper.grid(row=row, column=column, columnspan=columnspan, sticky="ew", padx=padx, pady=(16, 0))
        wrapper.grid_columnconfigure(0, weight=1)
        create_label(wrapper, label, muted=True).grid(row=0, column=0, sticky="w")
        entry = create_entry(wrapper)
        entry.grid(row=1, column=0, sticky="ew", pady=(6, 0), ipady=7)
        entry.insert(0, value)
        return entry

    def on_resize(self, _event):
        width = self.winfo_width()
        stacked = bool(width and width < RESPONSIVE_BREAKPOINT)
        if stacked:
            self.hero_card.grid_configure(row=0, column=0, columnspan=2, padx=0)
            self.status_stack.grid_configure(row=1, column=0, columnspan=2, padx=0)
            self.control_card.grid_configure(row=2, column=0, columnspan=2)
            self.log_card.grid_configure(row=3, column=0, columnspan=2)
        else:
            self.hero_card.grid_configure(row=0, column=0, columnspan=1, padx=(0, 10))
            self.status_stack.grid_configure(row=0, column=1, columnspan=1, padx=(10, 0))
            self.control_card.grid_configure(row=1, column=0, columnspan=2)
            self.log_card.grid_configure(row=2, column=0, columnspan=2)

    def set_connection_badge(self, text, tone, summary=None):
        palette = {
            "success": ("#e7f6ec", COLORS["success"]),
            "warning": ("#fff5e6", COLORS["warning"]),
            "danger": ("#fff1f2", COLORS["danger"]),
        }
        bg, fg = palette[tone]
        self.connection_badge.configure(text=text, bg=bg, fg=fg)
        if summary:
            self.connection_summary.configure(text=summary)

    def update_metric_cards(self):
        self.metric_labels["Default VISA"].configure(text=config.VISA_ADDRESS)
        self.metric_labels["Timeout"].configure(text=f"{config.GLOBAL_TIMEOUT} ms")
        self.metric_labels["Base output"].configure(text=config.BASE_DIRECTORY)

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
                    "A VISA target was discovered automatically. You can connect now or refine the timeout first.",
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
                "pyvisa is missing in the current environment, so live verification cannot run here.",
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
                "Live communication succeeded. Measurement pages can use this scope immediately.",
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
