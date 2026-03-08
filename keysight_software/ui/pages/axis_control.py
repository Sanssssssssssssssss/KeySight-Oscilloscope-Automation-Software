import tkinter as tk
import json

from keysight_software.paths import project_path
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


DEFAULT_AXIS_CONFIG = project_path("axis_config.json")
RESPONSIVE_BREAKPOINT = 1220


class AxisControlPage(tk.Frame):
    def __init__(self, master, oscilloscope, config_file=DEFAULT_AXIS_CONFIG):
        super().__init__(master, bg=COLORS["background"])
        self.oscilloscope = oscilloscope
        self.config_file = config_file
        self.grid(row=0, column=0, sticky="nsew")
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.bind("<Configure>", self.on_resize)

        try:
            self.active_channels = self.oscilloscope.get_active_channels() if self.oscilloscope else []
            if not self.active_channels:
                raise ValueError("No active channels detected.")
        except Exception:
            self.active_channels = []

        self.is_connected = bool(self.active_channels)

        self.channel_controls = {}
        self.build_controls()
        self.build_console()
        self.load_settings()
        self.update_connection_state(log_message=False)
        self.update_responsive_layout()

    def build_controls(self):
        self.top_shell = tk.Frame(self, bg=COLORS["background"])
        self.top_shell.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 18))
        self.top_shell.grid_columnconfigure(0, weight=1)
        self.top_shell.grid_columnconfigure(1, weight=1)

        time_card, time_inner = create_card(self.top_shell, padding=26)
        time_card.grid(row=0, column=0, sticky="nsew", padx=(0, 9))
        time_inner.grid_columnconfigure((0, 1), weight=1)
        create_section_heading(
            time_inner,
            "Timebase",
            "Tune horizontal scale and position before applying channel and marker adjustments.",
        ).grid(row=0, column=0, columnspan=2, sticky="w")
        status_row = tk.Frame(time_inner, bg=time_inner.cget("bg"))
        status_row.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        create_label(status_row, "Scope status", muted=True).pack(side="left")
        self.connection_badge = create_badge(status_row, "Checking", tone="neutral")
        self.connection_badge.pack(side="left", padx=(10, 0))
        self.connection_hint = create_label(
            time_inner,
            "Checking whether channel controls can be applied live.",
            muted=True,
            wraplength=320,
            justify="left",
        )
        self.connection_hint.grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self.x_scale_var = tk.DoubleVar(value=1.0)
        self.x_pos_var = tk.DoubleVar(value=0.0)
        self.add_field(time_inner, 3, 0, "Scale (s/div)", self.x_scale_var)
        self.add_field(time_inner, 3, 1, "Position (s)", self.x_pos_var)

        marker_card, marker_inner = create_card(self.top_shell, padding=26)
        marker_card.grid(row=0, column=1, sticky="nsew", padx=(9, 0))
        marker_inner.grid_columnconfigure((0, 1), weight=1)
        create_section_heading(
            marker_inner,
            "Markers",
            "Place one or two analysis markers with direct X and Y coordinates.",
        ).grid(row=0, column=0, columnspan=2, sticky="w")
        self.marker_count_var = tk.IntVar(value=2)
        self.add_field(marker_inner, 1, 0, "Number of Markers", self.marker_count_var)
        self.marker_entries = []
        for index in range(1, 3):
            x_marker_var = tk.DoubleVar(value=0.0)
            y_marker_var = tk.DoubleVar(value=0.0)
            self.add_field(marker_inner, 1 + index, 0, f"X Marker {index} (s)", x_marker_var)
            self.add_field(marker_inner, 1 + index, 1, f"Y Marker {index} (V)", y_marker_var)
            self.marker_entries.extend([x_marker_var, y_marker_var])

        self.channels_card, channels_inner = create_card(self, padding=26)
        self.channels_card.grid(row=1, column=0, sticky="nsew", padx=(0, 9))
        channels_inner.grid_columnconfigure((0, 1), weight=1)
        create_section_heading(
            channels_inner,
            "Channel scaling",
            (
                f"Active channels: {', '.join(f'CH{channel}' for channel in self.active_channels)}"
                if self.active_channels
                else "No live channels detected. You can still edit and save presets offline."
            ),
        ).grid(row=0, column=0, columnspan=2, sticky="w")
        for channel in range(1, 5):
            card = tk.Frame(channels_inner, bg=COLORS["surface_alt"], padx=18, pady=18)
            card.grid(row=1 + (channel - 1) // 2, column=(channel - 1) % 2, sticky="nsew", padx=6, pady=6)
            create_label(card, f"Channel {channel}", font=("SF Pro Text", 11, "bold")).pack(anchor="w")
            scale_var = tk.DoubleVar(value=0.0 if channel not in self.active_channels else 1.0)
            pos_var = tk.DoubleVar(value=0.0)
            scale_entry = self.add_field(card, 1, 0, "Scale (V/div)", scale_var, use_pack=True)
            pos_entry = self.add_field(card, 2, 0, "Position (V)", pos_var, use_pack=True)
            self.channel_controls[channel] = {
                "scale_var": scale_var,
                "position_var": pos_var,
                "scale_entry": scale_entry,
                "position_entry": pos_entry,
            }

        action_row = tk.Frame(channels_inner, bg=channels_inner.cget("bg"))
        action_row.grid(row=3, column=0, columnspan=2, sticky="w", pady=(14, 0))
        self.apply_button = create_button(action_row, "Apply Settings", self.apply_settings, tone="primary")
        self.apply_button.pack(side="left")
        create_button(action_row, "Save Preset", self.save_settings, tone="secondary").pack(side="left", padx=(10, 0))

    def build_console(self):
        self.log_card, log_inner = create_card(self, padding=26)
        self.log_card.grid(row=1, column=1, sticky="nsew", padx=(9, 0))
        log_inner.grid_columnconfigure(0, weight=1)
        log_inner.grid_rowconfigure(1, weight=1)
        create_section_heading(
            log_inner,
            "Activity log",
            "Application feedback appears here after loading or applying axis changes.",
        ).grid(row=0, column=0, sticky="w")
        self.console_output = create_scrolled_text(log_inner, height=20, mono=True)
        self.console_output.grid(row=1, column=0, sticky="nsew", pady=(18, 0))

    def add_field(self, parent, row, column, label, variable, use_pack=False):
        wrapper = tk.Frame(parent, bg=parent.cget("bg"))
        if use_pack:
            wrapper.pack(fill="x", pady=(14, 0))
        else:
            wrapper.grid(row=row, column=column, sticky="ew", padx=8, pady=(14, 0))
            parent.grid_columnconfigure(column, weight=1)
        create_label(wrapper, label, muted=True).pack(anchor="w")
        entry = create_entry(wrapper, textvariable=variable)
        entry.pack(fill="x", pady=(8, 0), ipady=9)
        return entry

    def on_resize(self, event):
        if event.widget is self:
            self.update_responsive_layout(event.width)

    def update_responsive_layout(self, width=None):
        width = width or self.winfo_width()
        stacked = bool(width and width < RESPONSIVE_BREAKPOINT)
        if stacked:
            self.grid_columnconfigure(0, weight=1)
            self.grid_columnconfigure(1, weight=0)
            self.top_shell.grid_configure(row=0, column=0, columnspan=1)
            self.channels_card.grid_configure(row=1, column=0, padx=0, pady=(0, 12))
            self.log_card.grid_configure(row=2, column=0, padx=0)
            self.top_shell.grid_columnconfigure(0, weight=1)
            self.top_shell.grid_columnconfigure(1, weight=1)
        else:
            self.grid_columnconfigure(0, weight=2)
            self.grid_columnconfigure(1, weight=1)
            self.top_shell.grid_configure(row=0, column=0, columnspan=2)
            self.channels_card.grid_configure(row=1, column=0, padx=(0, 9), pady=0)
            self.log_card.grid_configure(row=1, column=1, padx=(9, 0))

    def update_connection_state(self, log_message=True):
        self.is_connected = bool(self.active_channels)
        if self.is_connected:
            self.connection_badge.configure(text="Connected", bg="#e7f6ec", fg=COLORS["success"])
            self.connection_hint.configure(text="Live oscilloscope detected. Applying settings will update the bench.")
            if log_message:
                append_text(self.console_output, "Oscilloscope detected. Live axis control is available.\n")
        else:
            self.connection_badge.configure(text="Offline", bg="#fff5e6", fg=COLORS["warning"])
            self.connection_hint.configure(
                text="No oscilloscope connection detected. Presets can be edited and saved, but not applied."
            )
            if log_message:
                append_text(self.console_output, "Offline mode active. Apply is disabled until a scope reconnects.\n")
        self.apply_button.configure(state=tk.NORMAL if self.is_connected else tk.DISABLED)

    def apply_settings(self):
        try:
            if not self.oscilloscope or not self.is_connected:
                append_text(self.console_output, "Apply skipped because no oscilloscope is connected.\n")
                return

            self.oscilloscope.set_timebase_scale(self.x_scale_var.get())
            self.oscilloscope.set_timebase_position(self.x_pos_var.get())
            append_text(self.console_output, "Timebase settings applied.\n")

            for channel in range(1, 5):
                controls = self.channel_controls[channel]
                if channel in self.active_channels:
                    self.oscilloscope.set_channel_scale(channel, controls["scale_var"].get())
                    self.oscilloscope.set_channel_position(channel, controls["position_var"].get())
                    append_text(self.console_output, f"Channel {channel} settings applied.\n")
                else:
                    append_text(self.console_output, f"Channel {channel} skipped because it is not active.\n")

            marker_count = self.marker_count_var.get()
            if marker_count >= 1:
                x1_marker_var = self.marker_entries[0]
                y1_marker_var = self.marker_entries[1]
                self.oscilloscope.add_marker_x1(x1_marker_var.get())
                self.oscilloscope.add_marker_y1(y1_marker_var.get())
                append_text(self.console_output, "Marker 1 settings applied.\n")
            if marker_count == 2:
                x2_marker_var = self.marker_entries[2]
                y2_marker_var = self.marker_entries[3]
                self.oscilloscope.add_marker_x2(x2_marker_var.get())
                self.oscilloscope.add_marker_y2(y2_marker_var.get())
                append_text(self.console_output, "Marker 2 settings applied.\n")

            self.save_settings()
            append_text(self.console_output, "Settings applied and preset saved successfully.\n")
        except Exception as error:
            append_text(self.console_output, f"Error: {error}\n")

    def save_settings(self):
        settings = {
            "timebase": {
                "scale": self.x_scale_var.get(),
                "position": self.x_pos_var.get()
            },
            "channels": {},
            "markers": []
        }

        for channel in range(1, 5):
            controls = self.channel_controls[channel]
            y_scale_var = controls["scale_var"].get()
            y_pos_var = controls["position_var"].get()
            settings["channels"][f'channel_{channel}'] = {
                "scale": y_scale_var,
                "position": y_pos_var
            }

        marker_count = self.marker_count_var.get()
        for i in range(marker_count):
            x_marker_var = self.marker_entries[i * 2].get()
            y_marker_var = self.marker_entries[i * 2 + 1].get()
            settings["markers"].append({"x": x_marker_var, "y": y_marker_var})

        with open(self.config_file, 'w', encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
        append_text(self.console_output, f"Preset saved to {self.config_file}.\n")

    def load_settings(self):
        try:
            with open(self.config_file, 'r', encoding="utf-8") as f:
                settings = json.load(f)
            self.x_scale_var.set(settings["timebase"]["scale"])
            self.x_pos_var.set(settings["timebase"]["position"])

            channel_settings = settings.get("channels", settings.get("channel_settings", {}))
            for channel in range(1, 5):
                if f'channel_{channel}' in channel_settings:
                    y_scale_var = channel_settings[f'channel_{channel}']["scale"]
                    y_pos_var = channel_settings[f'channel_{channel}']["position"]
                    self.channel_controls[channel]["scale_var"].set(y_scale_var)
                    self.channel_controls[channel]["position_var"].set(y_pos_var)

            markers = settings.get("markers", settings.get("marker_positions", []))
            marker_count = len(markers)
            self.marker_count_var.set(marker_count)
            for i in range(marker_count):
                x_marker_var = markers[i]["x"]
                y_marker_var = markers[i]["y"]
                self.marker_entries[i * 2].set(x_marker_var)
                self.marker_entries[i * 2 + 1].set(y_marker_var)
            append_text(self.console_output, "Settings loaded successfully.\n")
        except FileNotFoundError:
            append_text(self.console_output, "No saved settings found.\n")
        except Exception as error:
            append_text(self.console_output, f"Failed to load settings: {error}\n")
