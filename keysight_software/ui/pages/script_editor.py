import json
import os
import time
import tkinter as tk
from tkinter import Toplevel, filedialog, messagebox

from keysight_software import config
from keysight_software.device.measure import Measure
from keysight_software.device.oscilloscope import Oscilloscope
from keysight_software.paths import config_path
from keysight_software.ui.dialogs.axis_control_config import AxisControlConfig
from keysight_software.ui.dialogs.waveform_config import WaveformConfig
from keysight_software.ui.pages.run_script import RunScriptPage
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


SCRIPT_EDITOR_STATE = config_path("script_editor_state.json")
DEFAULT_WAVEFORM_CONFIG = config_path("waveform_config.json")
DEFAULT_AXIS_CONFIG = config_path("axis_config.json")
LOCKED_MODULES = {"Start", "End"}
MODULE_ORDER = ["Start", "Wave Cap", "Axis Control", "Delay", "End"]
MODULE_DESCRIPTIONS = {
    "Start": "Required sequence entry point.",
    "Wave Cap": "Capture waveform data using the saved waveform preset.",
    "Axis Control": "Apply saved axis and marker settings to the instrument.",
    "Delay": "Pause execution between bench actions.",
    "End": "Required sequence exit point.",
}
MODULE_TONES = {
    "Start": ("#edf4ff", COLORS["accent"]),
    "Wave Cap": ("#eef6ff", COLORS["accent"]),
    "Axis Control": ("#edf8f0", COLORS["success"]),
    "Delay": ("#fff5e6", COLORS["warning"]),
    "End": ("#f3f3f5", COLORS["text_muted"]),
}
RESPONSIVE_BREAKPOINT = 1320


class ScriptEditor(tk.Frame):
    def __init__(self, master=None, oscilloscope=None, measure=None, auto_connect=False):
        super().__init__(master, bg=COLORS["background"])
        self.master = master
        self.grid(row=0, column=0, sticky="nsew")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.oscilloscope = oscilloscope
        self.measure = measure
        self.connection_error = None
        self.sequence = []
        self.selected_index = None
        self.current_script_path = None
        self.dirty = False
        self.save_directory = tk.StringVar(value="")
        self.delay_var = tk.StringVar(value="1.0")

        self.build_header()
        self.build_workspace()
        self.build_footer()
        self.bind("<Configure>", self.on_resize)

        if self.oscilloscope is None and auto_connect:
            self.initialize_connection()
        else:
            self.update_connection_state()

        self.load_editor_state()
        if not self.sequence:
            self.new_sequence()
        else:
            self.refresh_sequence_view()
            self.select_index(0)

    def build_header(self):
        header = tk.Frame(self, bg=COLORS["background"])
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.grid_columnconfigure(0, weight=1)

        left = tk.Frame(header, bg=COLORS["background"])
        left.grid(row=0, column=0, sticky="w")
        create_label(left, "Script editor", font=("SF Pro Display", 18, "bold")).pack(anchor="w")
        create_label(
            left,
            "Build automation sequences as ordered steps instead of dragging modules across a canvas.",
            muted=True,
            wraplength=560,
            justify="left",
        ).pack(anchor="w", pady=(6, 0))

        self.header_status = tk.Frame(header, bg=COLORS["background"])
        self.header_status.grid(row=0, column=1, sticky="e")
        create_label(self.header_status, "Scope status", muted=True).pack(side="left")
        self.connection_badge = create_badge(self.header_status, "Checking", tone="neutral")
        self.connection_badge.pack(side="left", padx=(10, 0))
        self.connection_hint = create_label(
            header,
            "You can edit and save scripts offline. Live execution uses the shared scope connection.",
            muted=True,
            wraplength=420,
            justify="right",
        )
        self.connection_hint.grid(row=1, column=1, sticky="e", pady=(6, 0))

    def build_workspace(self):
        self.workspace = tk.Frame(self, bg=COLORS["background"])
        self.workspace.grid(row=1, column=0, sticky="nsew")
        self.workspace.grid_columnconfigure(0, weight=1, uniform="script")
        self.workspace.grid_columnconfigure(1, weight=2, uniform="script")
        self.workspace.grid_columnconfigure(2, weight=1, uniform="script")
        self.workspace.grid_rowconfigure(0, weight=1)

        self.build_module_library()
        self.build_sequence_panel()
        self.build_detail_panel()
        self.build_log_panel()

    def build_module_library(self):
        self.library_card, library = create_card(self.workspace, padding=22)
        self.library_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        library.grid_columnconfigure(0, weight=1)

        create_section_heading(
            library,
            "Module library",
            "Insert modules into the current sequence. Start and End are kept as anchors.",
        ).grid(row=0, column=0, sticky="w")

        for row, module_type in enumerate(MODULE_ORDER, start=1):
            card = tk.Frame(library, bg=COLORS["surface_alt"], padx=16, pady=14)
            card.grid(row=row, column=0, sticky="ew", pady=(14 if row == 1 else 10, 0))
            card.grid_columnconfigure(0, weight=1)
            create_label(card, module_type, font=("SF Pro Text", 11, "bold")).grid(row=0, column=0, sticky="w")
            create_label(
                card,
                MODULE_DESCRIPTIONS[module_type],
                muted=True,
                wraplength=240,
                justify="left",
            ).grid(row=1, column=0, sticky="w", pady=(6, 0))
            create_button(
                card,
                "Add to sequence",
                lambda module=module_type: self.add_step(module),
                tone="secondary",
            ).grid(row=2, column=0, sticky="w", pady=(12, 0))

        utility_row = tk.Frame(library, bg=library.cget("bg"))
        utility_row.grid(row=len(MODULE_ORDER) + 1, column=0, sticky="ew", pady=(18, 0))
        create_button(utility_row, "New Sequence", self.new_sequence, tone="primary").pack(side="left")
        create_button(utility_row, "Clear Middle Steps", self.clear_middle_steps, tone="secondary").pack(
            side="left", padx=(10, 0)
        )

    def build_sequence_panel(self):
        self.sequence_card, sequence = create_card(self.workspace, padding=22)
        self.sequence_card.grid(row=0, column=1, sticky="nsew", padx=10)
        sequence.grid_columnconfigure(0, weight=1)
        sequence.grid_rowconfigure(2, weight=1)

        heading = tk.Frame(sequence, bg=sequence.cget("bg"))
        heading.grid(row=0, column=0, sticky="ew")
        heading.grid_columnconfigure(0, weight=1)
        create_section_heading(
            heading,
            "Sequence builder",
            "Select a step to edit its details, reorder it, or validate the final execution flow.",
        ).grid(row=0, column=0, sticky="w")
        self.validation_badge = create_badge(heading, "Draft", tone="neutral")
        self.validation_badge.grid(row=0, column=1, sticky="e")

        toolbar = tk.Frame(sequence, bg=sequence.cget("bg"))
        toolbar.grid(row=1, column=0, sticky="w", pady=(16, 0))
        create_button(toolbar, "Move Up", lambda: self.move_selected(-1), tone="secondary").pack(side="left")
        create_button(toolbar, "Move Down", lambda: self.move_selected(1), tone="secondary").pack(
            side="left", padx=(10, 0)
        )
        create_button(toolbar, "Duplicate", self.duplicate_selected, tone="secondary").pack(side="left", padx=(10, 0))
        create_button(toolbar, "Remove", self.remove_selected, tone="danger").pack(side="left", padx=(10, 0))

        list_shell = tk.Frame(sequence, bg=sequence.cget("bg"))
        list_shell.grid(row=2, column=0, sticky="nsew", pady=(16, 0))
        list_shell.grid_columnconfigure(0, weight=1)
        list_shell.grid_rowconfigure(0, weight=1)

        self.sequence_list = tk.Listbox(
            list_shell,
            activestyle="none",
            bg=COLORS["surface_alt"],
            fg=COLORS["text"],
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            highlightcolor=COLORS["accent"],
            selectbackground=COLORS["accent_soft"],
            selectforeground=COLORS["accent"],
            font=("SF Pro Text", 11),
        )
        self.sequence_list.grid(row=0, column=0, sticky="nsew")
        sequence_scrollbar = tk.Scrollbar(list_shell, orient="vertical", command=self.sequence_list.yview)
        sequence_scrollbar.grid(row=0, column=1, sticky="ns")
        self.sequence_list.configure(yscrollcommand=sequence_scrollbar.set)
        self.sequence_list.bind("<<ListboxSelect>>", self.on_sequence_select)

        self.sequence_summary = create_label(
            sequence,
            "No steps in the sequence yet.",
            muted=True,
            wraplength=520,
            justify="left",
        )
        self.sequence_summary.grid(row=3, column=0, sticky="w", pady=(14, 0))

    def build_detail_panel(self):
        self.detail_card, detail = create_card(self.workspace, padding=22)
        self.detail_card.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
        detail.grid_columnconfigure(0, weight=1)

        create_section_heading(
            detail,
            "Selected step",
            "Fine-tune the highlighted module without leaving the script editor.",
        ).grid(row=0, column=0, sticky="w")

        self.detail_type = create_label(detail, "Select a step", font=("SF Pro Display", 16, "bold"))
        self.detail_type.grid(row=1, column=0, sticky="w", pady=(18, 0))
        self.detail_description = create_label(detail, "", muted=True, wraplength=280, justify="left")
        self.detail_description.grid(row=2, column=0, sticky="w", pady=(8, 0))

        self.step_badge = create_badge(detail, "No selection", tone="neutral")
        self.step_badge.grid(row=3, column=0, sticky="w", pady=(16, 0))

        self.detail_delay_wrapper = tk.Frame(detail, bg=detail.cget("bg"))
        self.detail_delay_wrapper.grid(row=4, column=0, sticky="ew", pady=(18, 0))
        self.detail_delay_wrapper.grid_columnconfigure(0, weight=1)
        create_label(self.detail_delay_wrapper, "Delay (seconds)", muted=True).grid(row=0, column=0, sticky="w")
        self.delay_entry = create_entry(self.detail_delay_wrapper, textvariable=self.delay_var)
        self.delay_entry.grid(row=1, column=0, sticky="ew", pady=(8, 0), ipady=9)
        self.delay_apply_button = create_button(
            self.detail_delay_wrapper,
            "Apply Delay",
            self.apply_delay,
            tone="primary",
        )
        self.delay_apply_button.grid(row=2, column=0, sticky="w", pady=(12, 0))

        self.config_status = create_label(detail, "", muted=True, wraplength=280, justify="left")
        self.config_status.grid(row=5, column=0, sticky="w", pady=(18, 0))

        self.config_button = create_button(detail, "Open Configuration", self.open_selected_config, tone="secondary")
        self.config_button.grid(row=6, column=0, sticky="w", pady=(12, 0))

        secondary_row = tk.Frame(detail, bg=detail.cget("bg"))
        secondary_row.grid(row=7, column=0, sticky="w", pady=(18, 0))
        create_button(secondary_row, "Validate Sequence", self.validate_sequence, tone="primary").pack(side="left")
        create_button(secondary_row, "Save Draft State", self.save_editor_state, tone="secondary").pack(
            side="left", padx=(10, 0)
        )

    def build_log_panel(self):
        self.log_card, log = create_card(self, padding=22)
        self.log_card.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        log.grid_columnconfigure(0, weight=1)
        log.grid_rowconfigure(1, weight=1)
        create_section_heading(
            log,
            "Editor activity",
            "Validation notes, save actions, and high-level workflow feedback appear here.",
        ).grid(row=0, column=0, sticky="w")
        self.console = create_scrolled_text(log, height=8, mono=True)
        self.console.grid(row=1, column=0, sticky="nsew", pady=(16, 0))

    def build_footer(self):
        footer = tk.Frame(self, bg=COLORS["background"])
        footer.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        footer.grid_columnconfigure(1, weight=1)

        action_row = tk.Frame(footer, bg=COLORS["background"])
        action_row.grid(row=0, column=0, sticky="w")
        create_button(action_row, "Browse Save Folder", self.browse_save_directory, tone="secondary").pack(side="left")
        create_button(action_row, "Load Script", self.load_script, tone="secondary").pack(side="left", padx=(10, 0))
        create_button(action_row, "Save Script", self.save_script, tone="primary").pack(side="left", padx=(10, 0))
        create_button(action_row, "Run Script", self.run_script, tone="secondary").pack(side="left", padx=(10, 0))

        self.save_path_label = create_label(footer, "Save folder: not selected", muted=True, wraplength=720, justify="left")
        self.save_path_label.grid(row=0, column=1, sticky="e", padx=(16, 0))

    def initialize_connection(self):
        try:
            self.oscilloscope = Oscilloscope(config.VISA_ADDRESS, config.GLOBAL_TIMEOUT)
            self.measure = Measure(self.oscilloscope)
            self.connection_error = None
        except Exception as error:
            self.oscilloscope = None
            self.measure = None
            self.connection_error = str(error)
        self.update_connection_state()

    def update_connection_state(self):
        if self.oscilloscope and self.measure:
            self.connection_badge.configure(text="Connected", bg="#e7f6ec", fg=COLORS["success"])
            self.connection_hint.configure(text="Shared oscilloscope connection is available for script execution.")
        else:
            self.connection_badge.configure(text="Offline", bg="#fff5e6", fg=COLORS["warning"])
            if self.connection_error:
                self.connection_hint.configure(text=f"Instrument unavailable: {self.connection_error}")
            else:
                self.connection_hint.configure(
                    text="No shared oscilloscope connection is available. Editing, saving, and validation remain available."
                )

    def on_resize(self, event):
        if event.widget is not self:
            return
        stacked = event.width < RESPONSIVE_BREAKPOINT
        if stacked:
            self.workspace.grid_columnconfigure(0, weight=1, uniform="")
            self.workspace.grid_columnconfigure(1, weight=1, uniform="")
            self.workspace.grid_columnconfigure(2, weight=1, uniform="")
            self.library_card.grid_configure(row=0, column=0, padx=0, pady=(0, 12))
            self.sequence_card.grid_configure(row=1, column=0, padx=0, pady=(0, 12))
            self.detail_card.grid_configure(row=2, column=0, padx=0)
        else:
            self.workspace.grid_columnconfigure(0, weight=1, uniform="script")
            self.workspace.grid_columnconfigure(1, weight=2, uniform="script")
            self.workspace.grid_columnconfigure(2, weight=1, uniform="script")
            self.library_card.grid_configure(row=0, column=0, padx=(0, 10), pady=0)
            self.sequence_card.grid_configure(row=0, column=1, padx=10, pady=0)
            self.detail_card.grid_configure(row=0, column=2, padx=(10, 0), pady=0)

    def generate_step_id(self):
        return f"step_{int(time.time() * 1000)}_{len(self.sequence)}"

    def make_step(self, module_type, delay=1.0):
        step = {"id": self.generate_step_id(), "type": module_type}
        if module_type == "Delay":
            step["delay"] = float(delay)
        return step

    def normalize_sequence(self, raw_steps):
        sequence = [self.make_step("Start")]
        for step in raw_steps:
            module_type = step.get("type")
            if module_type in LOCKED_MODULES:
                continue
            if module_type not in MODULE_DESCRIPTIONS:
                continue
            sequence.append(self.make_step(module_type, step.get("delay", 1.0)))
        sequence.append(self.make_step("End"))
        return sequence

    def load_editor_state(self):
        if not SCRIPT_EDITOR_STATE.exists():
            return
        try:
            with open(SCRIPT_EDITOR_STATE, "r", encoding="utf-8") as handle:
                state = json.load(handle)
            self.save_directory.set(state.get("save_directory", ""))
            self.current_script_path = state.get("current_script_path")
            self.sequence = self.normalize_sequence(state.get("sequence", []))
            self.dirty = state.get("dirty", False)
            self.update_save_path_label()
            append_text(self.console, "Loaded draft state from configs/script_editor_state.json\n")
        except Exception as error:
            append_text(self.console, f"Failed to restore draft state: {error}\n")

    def save_editor_state(self):
        state = {
            "save_directory": self.save_directory.get(),
            "current_script_path": self.current_script_path,
            "dirty": self.dirty,
            "sequence": self.serialize_sequence(),
        }
        with open(SCRIPT_EDITOR_STATE, "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=4)
        append_text(self.console, "Draft state saved.\n")

    def update_save_path_label(self):
        directory = self.save_directory.get()
        text = f"Save folder: {directory}" if directory else "Save folder: not selected"
        if self.current_script_path:
            text += f" | Current script: {self.current_script_path}"
        self.save_path_label.configure(text=text)

    def mark_dirty(self):
        self.dirty = True
        self.refresh_validation_badge("Draft", "neutral")
        self.save_editor_state()

    def refresh_validation_badge(self, text, tone):
        colors = {
            "neutral": (COLORS["surface_alt"], COLORS["text_muted"]),
            "success": ("#e7f6ec", COLORS["success"]),
            "warning": ("#fff5e6", COLORS["warning"]),
            "danger": ("#fff1f2", COLORS["danger"]),
        }
        bg, fg = colors[tone]
        self.validation_badge.configure(text=text, bg=bg, fg=fg)

    def refresh_sequence_view(self):
        self.sequence_list.delete(0, tk.END)
        for index, step in enumerate(self.sequence, start=1):
            description = step["type"]
            if step["type"] == "Delay":
                description += f"  |  {step.get('delay', 1.0):.2f}s"
            self.sequence_list.insert(tk.END, f"{index:02d}. {description}")
        middle_count = max(len(self.sequence) - 2, 0)
        suffix = "unsaved changes" if self.dirty else "saved draft"
        self.sequence_summary.configure(text=f"{len(self.sequence)} total steps, {middle_count} executable modules, {suffix}.")
        self.validate_sequence(show_message=False)

    def select_index(self, index):
        if index is None or not self.sequence:
            self.selected_index = None
            self.sequence_list.selection_clear(0, tk.END)
            self.refresh_detail_panel()
            return
        index = max(0, min(index, len(self.sequence) - 1))
        self.selected_index = index
        self.sequence_list.selection_clear(0, tk.END)
        self.sequence_list.selection_set(index)
        self.sequence_list.activate(index)
        self.sequence_list.see(index)
        self.refresh_detail_panel()

    def on_sequence_select(self, _event=None):
        selection = self.sequence_list.curselection()
        if not selection:
            return
        self.selected_index = selection[0]
        self.refresh_detail_panel()

    def refresh_detail_panel(self):
        if self.selected_index is None or not self.sequence:
            self.detail_type.configure(text="Select a step")
            self.detail_description.configure(text="Choose a sequence item to edit its behavior.")
            self.step_badge.configure(text="No selection", bg=COLORS["surface_alt"], fg=COLORS["text_muted"])
            self.detail_delay_wrapper.grid_remove()
            self.config_button.grid_remove()
            self.config_status.configure(text="")
            return

        step = self.sequence[self.selected_index]
        module_type = step["type"]
        self.detail_type.configure(text=module_type)
        self.detail_description.configure(text=MODULE_DESCRIPTIONS[module_type])
        bg, fg = MODULE_TONES[module_type]
        self.step_badge.configure(text=f"Step {self.selected_index + 1}", bg=bg, fg=fg)

        if module_type == "Delay":
            self.delay_var.set(f"{step.get('delay', 1.0):.2f}")
            self.detail_delay_wrapper.grid()
            self.config_status.configure(text="Delay steps accept positive decimal values in seconds.")
            self.config_button.grid_remove()
        else:
            self.detail_delay_wrapper.grid_remove()
            if module_type == "Wave Cap":
                self.config_status.configure(text=self.describe_config(DEFAULT_WAVEFORM_CONFIG, "waveform"))
                self.config_button.configure(text="Open Waveform Preset")
                self.config_button.grid()
            elif module_type == "Axis Control":
                self.config_status.configure(text=self.describe_config(DEFAULT_AXIS_CONFIG, "axis control"))
                self.config_button.configure(text="Open Axis Preset")
                self.config_button.grid()
            else:
                self.config_status.configure(text="This anchor step does not require extra configuration.")
                self.config_button.grid_remove()

    def describe_config(self, path, label):
        if path.exists():
            return f"Using {label} preset at {path}"
        return f"No saved {label} preset found yet. Open the configuration dialog to create one."

    def new_sequence(self):
        self.sequence = [self.make_step("Start"), self.make_step("Wave Cap"), self.make_step("End")]
        self.current_script_path = None
        self.dirty = False
        self.refresh_sequence_view()
        self.select_index(1)
        self.update_save_path_label()
        self.save_editor_state()
        append_text(self.console, "Started a new sequence template.\n")

    def clear_middle_steps(self):
        self.sequence = [self.make_step("Start"), self.make_step("End")]
        self.current_script_path = None
        self.mark_dirty()
        self.refresh_sequence_view()
        self.select_index(0)
        append_text(self.console, "Cleared all executable steps between Start and End.\n")

    def insert_index_for_new_step(self):
        if self.selected_index is None:
            return max(len(self.sequence) - 1, 0)
        selected_type = self.sequence[self.selected_index]["type"]
        if selected_type == "End":
            return self.selected_index
        return self.selected_index + 1

    def add_step(self, module_type):
        if module_type in LOCKED_MODULES:
            existing = next((index for index, step in enumerate(self.sequence) if step["type"] == module_type), None)
            if existing is not None:
                self.select_index(existing)
                append_text(self.console, f"{module_type} already exists and was selected.\n")
                return

        step = self.make_step(module_type)
        if module_type == "Start":
            self.sequence.insert(0, step)
            index = 0
        elif module_type == "End":
            self.sequence.append(step)
            index = len(self.sequence) - 1
        else:
            index = self.insert_index_for_new_step()
            self.sequence.insert(index, step)

        self.mark_dirty()
        self.refresh_sequence_view()
        self.select_index(index)
        append_text(self.console, f"Inserted {module_type} into the sequence.\n")

    def move_selected(self, offset):
        if self.selected_index is None:
            return
        step = self.sequence[self.selected_index]
        if step["type"] in LOCKED_MODULES:
            append_text(self.console, f"{step['type']} stays pinned in place.\n")
            return
        target = self.selected_index + offset
        if target <= 0 or target >= len(self.sequence) - 1:
            return
        self.sequence[self.selected_index], self.sequence[target] = self.sequence[target], self.sequence[self.selected_index]
        self.mark_dirty()
        self.refresh_sequence_view()
        self.select_index(target)

    def duplicate_selected(self):
        if self.selected_index is None:
            return
        step = self.sequence[self.selected_index]
        if step["type"] in LOCKED_MODULES:
            append_text(self.console, f"{step['type']} cannot be duplicated.\n")
            return
        clone = self.make_step(step["type"], step.get("delay", 1.0))
        index = self.selected_index + 1
        self.sequence.insert(index, clone)
        self.mark_dirty()
        self.refresh_sequence_view()
        self.select_index(index)
        append_text(self.console, f"Duplicated {step['type']}.\n")

    def remove_selected(self):
        if self.selected_index is None:
            return
        step = self.sequence[self.selected_index]
        if step["type"] in LOCKED_MODULES:
            append_text(self.console, f"{step['type']} cannot be removed.\n")
            return
        del self.sequence[self.selected_index]
        new_index = min(self.selected_index, len(self.sequence) - 1)
        self.mark_dirty()
        self.refresh_sequence_view()
        self.select_index(new_index)
        append_text(self.console, f"Removed {step['type']} from the sequence.\n")

    def apply_delay(self):
        if self.selected_index is None:
            return
        step = self.sequence[self.selected_index]
        if step["type"] != "Delay":
            return
        try:
            delay = float(self.delay_var.get())
        except ValueError:
            messagebox.showwarning("Invalid Delay", "Delay must be a numeric value in seconds.")
            return
        if delay <= 0:
            messagebox.showwarning("Invalid Delay", "Delay must be greater than zero.")
            return
        step["delay"] = delay
        self.mark_dirty()
        self.refresh_sequence_view()
        self.select_index(self.selected_index)
        append_text(self.console, f"Updated delay to {delay:.2f} seconds.\n")

    def open_selected_config(self):
        if self.selected_index is None:
            return
        step_type = self.sequence[self.selected_index]["type"]
        if step_type == "Wave Cap":
            window = tk.Toplevel(self.master)
            dialog = WaveformConfig(window)
            if DEFAULT_WAVEFORM_CONFIG.exists():
                dialog.load_configuration()
        elif step_type == "Axis Control":
            window = tk.Toplevel(self.master)
            dialog = AxisControlConfig(window)
            if DEFAULT_AXIS_CONFIG.exists():
                dialog.load_configuration()
        else:
            return
        append_text(self.console, f"Opened {step_type} configuration.\n")
        self.after(100, self.refresh_detail_panel)

    def serialize_sequence(self):
        payload = []
        for step in self.sequence:
            entry = {"type": step["type"]}
            if step["type"] == "Delay":
                entry["delay"] = step.get("delay", 1.0)
            elif step["type"] == "Wave Cap":
                entry["config"] = "configs/waveform_config.json"
            elif step["type"] == "Axis Control":
                entry["config"] = "configs/axis_config.json"
            payload.append(entry)
        return payload

    def validate_sequence(self, show_message=True):
        errors = []
        if not self.sequence:
            errors.append("Sequence is empty.")
        if self.sequence and self.sequence[0]["type"] != "Start":
            errors.append("First step must be Start.")
        if self.sequence and self.sequence[-1]["type"] != "End":
            errors.append("Last step must be End.")
        if len([step for step in self.sequence if step["type"] == "Start"]) != 1:
            errors.append("Sequence must contain exactly one Start step.")
        if len([step for step in self.sequence if step["type"] == "End"]) != 1:
            errors.append("Sequence must contain exactly one End step.")
        if len(self.sequence) <= 2:
            errors.append("Add at least one executable step between Start and End.")
        for index, step in enumerate(self.sequence, start=1):
            if step["type"] == "Delay" and float(step.get("delay", 0)) <= 0:
                errors.append(f"Delay on step {index} must be greater than zero.")

        if errors:
            self.refresh_validation_badge("Needs fixes", "warning")
            if show_message:
                messagebox.showwarning("Sequence Validation", "\n".join(errors))
                append_text(self.console, "Validation failed:\n")
                for error in errors:
                    append_text(self.console, f"  - {error}\n")
            return False

        badge_text = "Unsaved but valid" if self.dirty else "Ready"
        self.refresh_validation_badge(badge_text, "success")
        if show_message:
            append_text(self.console, "Sequence validation passed.\n")
        return True

    def browse_save_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.save_directory.set(directory)
            self.update_save_path_label()
            self.save_editor_state()

    def save_script(self, show_message=True):
        if not self.validate_sequence(show_message=show_message):
            return None
        if not self.save_directory.get():
            messagebox.showwarning("Save Script", "Please select a save directory first.")
            return None

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        save_folder = os.path.join(self.save_directory.get(), f"script_{timestamp}")
        os.makedirs(save_folder, exist_ok=True)
        configs_folder = os.path.join(save_folder, "configs")
        os.makedirs(configs_folder, exist_ok=True)

        sequence_filepath = os.path.join(save_folder, "sequence.json")
        with open(sequence_filepath, "w", encoding="utf-8") as handle:
            json.dump({"modules": self.serialize_sequence()}, handle, indent=4)

        for source in (DEFAULT_WAVEFORM_CONFIG, DEFAULT_AXIS_CONFIG):
            if source.exists():
                destination = os.path.join(configs_folder, source.name)
                with open(source, "r", encoding="utf-8") as src, open(destination, "w", encoding="utf-8") as dst:
                    dst.write(src.read())

        self.current_script_path = sequence_filepath
        self.dirty = False
        self.update_save_path_label()
        self.refresh_sequence_view()
        self.save_editor_state()
        append_text(self.console, f"Saved script package to {save_folder}\n")
        if show_message:
            messagebox.showinfo("Save Script", f"Script saved successfully to {save_folder}")
        return sequence_filepath

    def load_script(self):
        directory = filedialog.askdirectory()
        if not directory:
            return

        script_filepath = os.path.join(directory, "sequence.json")
        if not os.path.exists(script_filepath):
            messagebox.showerror("File Not Found", "sequence.json not found in the selected directory.")
            return

        try:
            with open(script_filepath, "r", encoding="utf-8") as handle:
                script_data = json.load(handle)
            self.sequence = self.normalize_sequence(script_data.get("modules", []))
            self.current_script_path = script_filepath
            self.save_directory.set(os.path.dirname(directory))
            self.dirty = False
            self.update_save_path_label()
            self.refresh_sequence_view()
            self.select_index(0)
            self.save_editor_state()
            append_text(self.console, f"Loaded script from {script_filepath}\n")
            messagebox.showinfo("Load Script", "Script loaded successfully.")
        except Exception as error:
            messagebox.showerror("Load Error", f"Cannot load script: {error}")

    def run_script(self):
        sequence_path = self.current_script_path
        if self.dirty or not sequence_path or not os.path.exists(sequence_path):
            sequence_path = self.save_script(show_message=False)
        if not sequence_path:
            return

        script_window = Toplevel(self.master)
        script_window.title("Run Script")
        script_window.geometry("920x680")

        run_page = RunScriptPage(script_window, self.oscilloscope, self.measure)
        run_page.script_path.set(sequence_path)
        run_page.load_script(sequence_path)
        script_window.grab_set()
        script_window.transient(self.master)
        append_text(self.console, f"Opened runner for {sequence_path}\n")


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1200x900")
    ScriptEditor(master=root, auto_connect=True)
    root.mainloop()
