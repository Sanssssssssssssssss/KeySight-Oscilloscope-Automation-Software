from __future__ import annotations

import json
import os
import time
from typing import Callable

from PySide6.QtWidgets import (
    QFileDialog,
    QDoubleSpinBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from keysight_software.paths import config_path
from keysight_software.qt_app.widgets import create_card, create_inline_status, create_log


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


class ScriptEditorPage(QWidget):
    def __init__(self, open_page: Callable[[str], None], run_script: Callable[[str], None], status_provider: Callable[[], tuple[str, str, bool]]):
        super().__init__()
        self.open_page = open_page
        self.run_script_callback = run_script
        self.status_provider = status_provider
        self.sequence: list[dict] = []
        self.selected_index: int | None = None
        self.current_script_path: str | None = None
        self.save_directory = ""
        self.dirty = False
        self.connection_badge: QLabel | None = None
        self.connection_hint: QLabel | None = None
        self.sequence_list = QListWidget()
        self.delay_input = QDoubleSpinBox()
        self.delay_input.setRange(0.01, 86400.0)
        self.delay_input.setDecimals(2)
        self.delay_input.setValue(1.0)
        self.detail_title = QLabel("Select a step")
        self.detail_title.setObjectName("SectionTitle")
        self.detail_description = QLabel("Choose a sequence item to edit its behavior.")
        self.detail_description.setObjectName("MutedBody")
        self.detail_description.setWordWrap(True)
        self.config_status = QLabel("")
        self.config_status.setObjectName("MutedBody")
        self.config_status.setWordWrap(True)
        self.config_button = QPushButton("Open related page")
        self.config_button.setObjectName("GhostButton")
        self.config_button.clicked.connect(self.open_selected_config)
        self.validation_badge: QLabel | None = None
        self.path_label = QLabel("Save folder: not selected")
        self.path_label.setObjectName("MutedBody")
        self.path_label.setWordWrap(True)
        self.log_output = create_log(180)
        self.build_ui()
        self.load_editor_state()
        if not self.sequence:
            self.new_sequence()
        else:
            self.refresh_sequence_view()
            self.select_index(0)
        self.refresh_status()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        header, header_layout = create_card("Script editor", "Build automation sequences as ordered steps instead of dragging modules across a canvas.")
        status_shell, self.connection_badge = create_inline_status("Connection", "Disconnected", "warn")
        self.connection_hint = QLabel()
        self.connection_hint.setObjectName("MutedBody")
        self.connection_hint.setWordWrap(True)
        header_layout.addWidget(status_shell)
        header_layout.addWidget(self.connection_hint)
        root.addWidget(header)

        workspace = QHBoxLayout()
        workspace.setSpacing(14)
        workspace.addWidget(self.build_library_card(), 1)
        workspace.addWidget(self.build_sequence_card(), 2)
        workspace.addWidget(self.build_detail_card(), 1)
        root.addLayout(workspace)

        footer, footer_layout = create_card("Editor activity", "Validation notes, save actions, and workflow feedback appear here.")
        footer_layout.addWidget(self.log_output)
        path_row = QHBoxLayout()
        browse = QPushButton("Browse Save Folder")
        browse.setObjectName("GhostButton")
        browse.clicked.connect(self.browse_save_directory)
        load = QPushButton("Load Script")
        load.setObjectName("GhostButton")
        load.clicked.connect(self.load_script)
        save = QPushButton("Save Script")
        save.setObjectName("PrimaryButton")
        save.clicked.connect(self.save_script)
        run = QPushButton("Run Script")
        run.setObjectName("GhostButton")
        run.clicked.connect(self.run_script)
        for button in (browse, load, save, run):
            path_row.addWidget(button)
        path_row.addStretch(1)
        footer_layout.addLayout(path_row)
        footer_layout.addWidget(self.path_label)
        root.addWidget(footer)

    def build_library_card(self):
        card, layout = create_card("Module library", "Insert modules into the current sequence. Start and End are kept as anchors.")
        for module_type in MODULE_ORDER:
            button = QPushButton(f"Add {module_type}")
            button.setObjectName("GhostButton")
            button.clicked.connect(lambda _checked=False, module=module_type: self.add_step(module))
            layout.addWidget(button)
        actions = QVBoxLayout()
        actions.setSpacing(8)
        new_button = QPushButton("New Sequence")
        new_button.setObjectName("PrimaryButton")
        new_button.clicked.connect(self.new_sequence)
        clear_button = QPushButton("Clear Middle Steps")
        clear_button.setObjectName("GhostButton")
        clear_button.clicked.connect(self.clear_middle_steps)
        actions.addWidget(new_button)
        actions.addWidget(clear_button)
        layout.addLayout(actions)
        return card

    def build_sequence_card(self):
        card, layout = create_card("Sequence builder", "Select a step to edit its details, reorder it, or validate the final execution flow.")
        status_shell, self.validation_badge = create_inline_status("Validation", "Draft", "warn")
        layout.addWidget(status_shell)
        toolbar = QGridLayout()
        toolbar.setHorizontalSpacing(8)
        toolbar.setVerticalSpacing(8)
        for label_text, callback, primary in (
            ("Move Up", lambda: self.move_selected(-1), False),
            ("Move Down", lambda: self.move_selected(1), False),
            ("Duplicate", self.duplicate_selected, False),
            ("Remove", self.remove_selected, False),
        ):
            button = QPushButton(label_text)
            button.setObjectName("PrimaryButton" if primary else "GhostButton")
            button.clicked.connect(callback)
            row, column = divmod(toolbar.count(), 2)
            toolbar.addWidget(button, row, column)
        layout.addLayout(toolbar)
        self.sequence_list.currentRowChanged.connect(self.on_sequence_select)
        self.sequence_list.setMinimumHeight(280)
        layout.addWidget(self.sequence_list)
        return card

    def build_detail_card(self):
        card, layout = create_card("Selected step", "Fine-tune the highlighted module without leaving the script editor.")
        layout.addWidget(self.detail_title)
        layout.addWidget(self.detail_description)
        delay_label = QLabel("Delay (seconds)")
        delay_label.setObjectName("MetricLabel")
        layout.addWidget(delay_label)
        layout.addWidget(self.delay_input)
        apply_delay = QPushButton("Apply Delay")
        apply_delay.setObjectName("PrimaryButton")
        apply_delay.clicked.connect(self.apply_delay)
        layout.addWidget(apply_delay)
        layout.addWidget(self.config_status)
        layout.addWidget(self.config_button)
        actions = QVBoxLayout()
        actions.setSpacing(8)
        validate = QPushButton("Validate Sequence")
        validate.setObjectName("PrimaryButton")
        validate.clicked.connect(self.validate_sequence)
        save_state = QPushButton("Save Draft State")
        save_state.setObjectName("GhostButton")
        save_state.clicked.connect(self.save_editor_state)
        actions.addWidget(validate)
        actions.addWidget(save_state)
        layout.addLayout(actions)
        return card

    def log(self, message: str):
        self.log_output.appendPlainText(message)

    def refresh_status(self):
        label, summary, ok = self.status_provider()
        self.connection_badge.setText(label)
        self.connection_badge.setProperty("status", "ok" if ok else "warn")
        self.connection_badge.style().unpolish(self.connection_badge)
        self.connection_badge.style().polish(self.connection_badge)
        self.connection_hint.setText(summary)

    def generate_step_id(self):
        return f"step_{int(time.time() * 1000)}_{len(self.sequence)}"

    def make_step(self, module_type: str, delay: float = 1.0):
        step = {"id": self.generate_step_id(), "type": module_type}
        if module_type == "Delay":
            step["delay"] = float(delay)
        return step

    def normalize_sequence(self, raw_steps: list[dict]):
        sequence = [self.make_step("Start")]
        for step in raw_steps:
            module_type = step.get("type")
            if module_type in LOCKED_MODULES or module_type not in MODULE_DESCRIPTIONS:
                continue
            sequence.append(self.make_step(module_type, float(step.get("delay", 1.0))))
        sequence.append(self.make_step("End"))
        return sequence

    def update_path_label(self):
        text = f"Save folder: {self.save_directory}" if self.save_directory else "Save folder: not selected"
        if self.current_script_path:
            text += f" | Current script: {self.current_script_path}"
        self.path_label.setText(text)

    def load_editor_state(self):
        if not SCRIPT_EDITOR_STATE.exists():
            return
        try:
            with open(SCRIPT_EDITOR_STATE, "r", encoding="utf-8") as handle:
                state = json.load(handle)
            self.save_directory = state.get("save_directory", "")
            self.current_script_path = state.get("current_script_path")
            self.sequence = self.normalize_sequence(state.get("sequence", []))
            self.dirty = state.get("dirty", False)
            self.update_path_label()
            self.log("Loaded draft state from configs/script_editor_state.json")
        except Exception as error:
            self.log(f"Failed to restore draft state: {error}")

    def save_editor_state(self):
        state = {
            "save_directory": self.save_directory,
            "current_script_path": self.current_script_path,
            "dirty": self.dirty,
            "sequence": self.serialize_sequence(),
        }
        with open(SCRIPT_EDITOR_STATE, "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=4)
        self.log("Draft state saved.")

    def set_validation(self, text: str, ok: bool):
        self.validation_badge.setText(text)
        self.validation_badge.setProperty("status", "ok" if ok else "warn")
        self.validation_badge.style().unpolish(self.validation_badge)
        self.validation_badge.style().polish(self.validation_badge)

    def refresh_sequence_view(self):
        self.sequence_list.clear()
        for index, step in enumerate(self.sequence, start=1):
            description = step["type"]
            if step["type"] == "Delay":
                description += f" | {step.get('delay', 1.0):.2f}s"
            self.sequence_list.addItem(f"{index:02d}. {description}")
        self.validate_sequence(show_message=False)

    def select_index(self, index: int | None):
        if index is None or not self.sequence:
            self.selected_index = None
            self.sequence_list.clearSelection()
            self.refresh_detail_panel()
            return
        index = max(0, min(index, len(self.sequence) - 1))
        self.selected_index = index
        self.sequence_list.setCurrentRow(index)
        self.refresh_detail_panel()

    def on_sequence_select(self, index: int):
        self.selected_index = index if index >= 0 else None
        self.refresh_detail_panel()

    def refresh_detail_panel(self):
        if self.selected_index is None:
            self.detail_title.setText("Select a step")
            self.detail_description.setText("Choose a sequence item to edit its behavior.")
            self.config_status.setText("")
            self.config_button.setVisible(False)
            self.delay_input.setEnabled(False)
            return
        step = self.sequence[self.selected_index]
        module_type = step["type"]
        self.detail_title.setText(module_type)
        self.detail_description.setText(MODULE_DESCRIPTIONS[module_type])
        self.delay_input.setEnabled(module_type == "Delay")
        self.delay_input.setValue(float(step.get("delay", 1.0)))
        if module_type == "Wave Cap":
            self.config_status.setText(self.describe_config(DEFAULT_WAVEFORM_CONFIG, "waveform"))
            self.config_button.setText("Open Capture Page")
            self.config_button.setVisible(True)
        elif module_type == "Axis Control":
            self.config_status.setText(self.describe_config(DEFAULT_AXIS_CONFIG, "axis control"))
            self.config_button.setText("Open Axis Page")
            self.config_button.setVisible(True)
        elif module_type == "Delay":
            self.config_status.setText("Delay steps accept positive decimal values in seconds.")
            self.config_button.setVisible(False)
        else:
            self.config_status.setText("This anchor step does not require extra configuration.")
            self.config_button.setVisible(False)

    def describe_config(self, path, label: str):
        if path.exists():
            return f"Using {label} preset at {path}"
        return f"No saved {label} preset found yet. Visit the related page to create one."

    def mark_dirty(self):
        self.dirty = True
        self.set_validation("Draft", False)
        self.save_editor_state()

    def new_sequence(self):
        self.sequence = [self.make_step("Start"), self.make_step("Wave Cap"), self.make_step("End")]
        self.current_script_path = None
        self.dirty = False
        self.refresh_sequence_view()
        self.select_index(1)
        self.update_path_label()
        self.save_editor_state()
        self.log("Started a new sequence template.")

    def clear_middle_steps(self):
        self.sequence = [self.make_step("Start"), self.make_step("End")]
        self.current_script_path = None
        self.mark_dirty()
        self.refresh_sequence_view()
        self.select_index(0)
        self.log("Cleared all executable steps between Start and End.")

    def insert_index_for_new_step(self):
        if self.selected_index is None:
            return max(len(self.sequence) - 1, 0)
        if self.sequence[self.selected_index]["type"] == "End":
            return self.selected_index
        return self.selected_index + 1

    def add_step(self, module_type: str):
        if module_type in LOCKED_MODULES:
            existing = next((index for index, step in enumerate(self.sequence) if step["type"] == module_type), None)
            if existing is not None:
                self.select_index(existing)
                self.log(f"{module_type} already exists and was selected.")
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
        self.log(f"Inserted {module_type} into the sequence.")

    def move_selected(self, offset: int):
        if self.selected_index is None:
            return
        step = self.sequence[self.selected_index]
        if step["type"] in LOCKED_MODULES:
            self.log(f"{step['type']} stays pinned in place.")
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
            self.log(f"{step['type']} cannot be duplicated.")
            return
        clone = self.make_step(step["type"], float(step.get("delay", 1.0)))
        self.sequence.insert(self.selected_index + 1, clone)
        self.mark_dirty()
        self.refresh_sequence_view()
        self.select_index(self.selected_index + 1)
        self.log(f"Duplicated {step['type']}.")

    def remove_selected(self):
        if self.selected_index is None:
            return
        step = self.sequence[self.selected_index]
        if step["type"] in LOCKED_MODULES:
            self.log(f"{step['type']} cannot be removed.")
            return
        del self.sequence[self.selected_index]
        new_index = min(self.selected_index, len(self.sequence) - 1)
        self.mark_dirty()
        self.refresh_sequence_view()
        self.select_index(new_index)
        self.log(f"Removed {step['type']} from the sequence.")

    def apply_delay(self):
        if self.selected_index is None:
            return
        step = self.sequence[self.selected_index]
        if step["type"] != "Delay":
            return
        delay = self.delay_input.value()
        if delay <= 0:
            QMessageBox.warning(self, "Invalid Delay", "Delay must be greater than zero.")
            return
        step["delay"] = delay
        self.mark_dirty()
        self.refresh_sequence_view()
        self.select_index(self.selected_index)
        self.log(f"Updated delay to {delay:.2f} seconds.")

    def open_selected_config(self):
        if self.selected_index is None:
            return
        step_type = self.sequence[self.selected_index]["type"]
        if step_type == "Wave Cap":
            self.open_page("capture")
        elif step_type == "Axis Control":
            self.open_page("axis")

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

    def validate_sequence(self, show_message: bool = True):
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
            self.set_validation("Needs fixes", False)
            if show_message:
                QMessageBox.warning(self, "Sequence Validation", "\n".join(errors))
                for error in errors:
                    self.log(f"- {error}")
            return False
        self.set_validation("Ready" if not self.dirty else "Valid draft", True)
        if show_message:
            self.log("Sequence validation passed.")
        return True

    def browse_save_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Save Directory", self.save_directory)
        if directory:
            self.save_directory = directory
            self.update_path_label()
            self.save_editor_state()

    def save_script(self, show_message: bool = True):
        if not self.validate_sequence(show_message=show_message):
            return None
        if not self.save_directory:
            QMessageBox.warning(self, "Save Script", "Please select a save directory first.")
            return None
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        save_folder = os.path.join(self.save_directory, f"script_{timestamp}")
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
        self.update_path_label()
        self.refresh_sequence_view()
        self.save_editor_state()
        self.log(f"Saved script package to {save_folder}")
        if show_message:
            QMessageBox.information(self, "Save Script", f"Script saved successfully to {save_folder}")
        return sequence_filepath

    def load_script(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Script Package")
        if not directory:
            return
        script_filepath = os.path.join(directory, "sequence.json")
        if not os.path.exists(script_filepath):
            QMessageBox.critical(self, "File Not Found", "sequence.json not found in the selected directory.")
            return
        try:
            with open(script_filepath, "r", encoding="utf-8") as handle:
                script_data = json.load(handle)
            self.sequence = self.normalize_sequence(script_data.get("modules", []))
            self.current_script_path = script_filepath
            self.save_directory = os.path.dirname(directory)
            self.dirty = False
            self.update_path_label()
            self.refresh_sequence_view()
            self.select_index(0)
            self.save_editor_state()
            self.log(f"Loaded script from {script_filepath}")
        except Exception as error:
            QMessageBox.critical(self, "Load Error", f"Cannot load script: {error}")

    def run_script(self):
        sequence_path = self.current_script_path
        if self.dirty or not sequence_path or not os.path.exists(sequence_path):
            sequence_path = self.save_script(show_message=False)
        if not sequence_path:
            return
        self.run_script_callback(sequence_path)
        self.log(f"Opened runner for {sequence_path}")
