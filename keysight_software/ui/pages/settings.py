import os
import tkinter as tk
from tkinter import filedialog, messagebox

from keysight_software.paths import project_path
from keysight_software.ui.theme import (
    COLORS,
    create_button,
    create_card,
    create_entry,
    create_label,
    create_section_heading,
)


CONFIG_FILE = project_path("config.txt")


def read_config_lines():
    for encoding in ("utf-8", "gbk", "cp1252", "latin-1"):
        try:
            with open(CONFIG_FILE, 'r', encoding=encoding) as config_file:
                return config_file.readlines()
        except (FileNotFoundError, UnicodeDecodeError):
            continue
    return []


class Setting(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=COLORS["background"])
        self.grid(row=0, column=0, sticky="nsew")
        self.grid_columnconfigure(0, weight=1)
        self.save_directory = tk.StringVar(value="C:/Users/Public/OscilloscopeData")
        self.build_page()
        self.load_settings()

    def build_page(self):
        card, inner = create_card(self, padding=30)
        card.grid(row=0, column=0, sticky="nsew")
        inner.grid_columnconfigure(0, weight=1)

        create_section_heading(
            inner,
            "Export preferences",
            "Set the default destination for screenshots, waveforms and measurement exports.",
        ).grid(row=0, column=0, sticky="w")

        field = tk.Frame(inner, bg=inner.cget("bg"))
        field.grid(row=1, column=0, sticky="ew", pady=(22, 0))
        field.grid_columnconfigure(0, weight=1)
        create_label(field, "Save Directory", muted=True).grid(row=0, column=0, sticky="w")
        self.directory_entry = create_entry(field, textvariable=self.save_directory)
        self.directory_entry.grid(row=1, column=0, sticky="ew", pady=(8, 0), ipady=10)

        actions = tk.Frame(inner, bg=inner.cget("bg"))
        actions.grid(row=2, column=0, sticky="w", pady=(18, 0))
        create_button(actions, "Browse Folder", self.browse_directory, tone="secondary").pack(
            side="left", padx=(0, 10)
        )
        create_button(actions, "Save Settings", self.save_settings, tone="primary").pack(side="left")

    def browse_directory(self):
        directory = filedialog.askdirectory(initialdir=self.save_directory.get())
        if directory:
            self.save_directory.set(directory)

    def save_settings(self):
        selected_directory = self.save_directory.get()
        if not os.path.exists(selected_directory):
            os.makedirs(selected_directory)

        with open(CONFIG_FILE, 'w', encoding="utf-8") as config_file:
            config_file.write(f"SAVE_DIRECTORY={selected_directory}\n")

        messagebox.showinfo("Settings", "Settings saved successfully!")

    def load_settings(self):
        for line in read_config_lines():
            if line.startswith("SAVE_DIRECTORY="):
                directory = line.split("=", 1)[1].strip()
                self.save_directory.set(directory)
                break


def get_save_directory():
    """Retrieve the currently set save directory from the configuration file."""
    for line in read_config_lines():
        if line.startswith("SAVE_DIRECTORY="):
            return line.split("=", 1)[1].strip()
    return "C:/Users/Public/OscilloscopeData"


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Settings")
    root.geometry("600x150")
    Setting(root)
    root.mainloop()

