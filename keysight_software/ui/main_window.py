import tkinter as tk
from tkinter import messagebox

from keysight_software.config import VISA_ADDRESS
from keysight_software.device.measure import Measure
from keysight_software.device.oscilloscope import Oscilloscope
from keysight_software.ui.pages.axis_control import AxisControlPage
from keysight_software.ui.pages.batch_process import BatchProcessPage
from keysight_software.ui.pages.home import ConfigHome
from keysight_software.ui.pages.run_script import RunScriptPage
from keysight_software.ui.pages.script_editor import ScriptEditor
from keysight_software.ui.pages.settings import Setting
from keysight_software.ui.pages.waveform_capture import WaveformCapture
from keysight_software.ui.theme import COLORS, FONTS, configure_root


class MainGUI:
    def __init__(self, master):
        self.master = master
        self.current_page = None
        self.nav_buttons = {}
        self.oscilloscope = None
        self.measure = None

        configure_root(master)
        master.title("Keysight Automation Studio")
        master.geometry("1440x920")
        master.minsize(1200, 780)
        master.grid_columnconfigure(1, weight=1)
        master.grid_rowconfigure(0, weight=1)

        self.build_shell()
        self.initialize_connection()
        self.show_home()

    def build_shell(self):
        self.sidebar = tk.Frame(self.master, bg=COLORS["surface"], width=260, bd=1, relief="solid")
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.grid_propagate(False)

        brand = tk.Frame(self.sidebar, bg=COLORS["surface"])
        brand.pack(fill="x", padx=24, pady=(28, 20))
        tk.Label(
            brand,
            text="Keysight",
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=FONTS["hero"],
            anchor="w",
        ).pack(anchor="w")
        tk.Label(
            brand,
            text="Automation Studio",
            bg=COLORS["surface"],
            fg=COLORS["text_muted"],
            font=FONTS["body"],
            anchor="w",
        ).pack(anchor="w", pady=(4, 0))

        nav_items = [
            ("home", "Home", self.show_home),
            ("capture", "Waveform Capture", self.show_waveform_capture),
            ("axis", "Axis Control", self.show_axis_control),
            ("script", "Script Editor", self.show_script_editor),
            ("runner", "Run Script", self.show_run_script),
            ("batch", "Batch Process", self.show_batch_process),
            ("settings", "Settings", self.show_settings),
        ]
        nav_wrapper = tk.Frame(self.sidebar, bg=COLORS["surface"])
        nav_wrapper.pack(fill="x", padx=14, pady=(0, 16))
        for key, label, command in nav_items:
            button = tk.Button(
                nav_wrapper,
                text=label,
                command=lambda k=key, cmd=command: self.select_page(k, cmd),
                anchor="w",
                bg=COLORS["surface"],
                fg=COLORS["text_muted"],
                activebackground=COLORS["accent_soft"],
                activeforeground=COLORS["accent"],
                relief="flat",
                bd=0,
                highlightthickness=0,
                padx=18,
                pady=14,
                font=FONTS["body_bold"],
                cursor="hand2",
            )
            button.pack(fill="x", pady=4)
            self.nav_buttons[key] = button

        footer = tk.Frame(self.sidebar, bg=COLORS["surface"])
        footer.pack(side="bottom", fill="x", padx=24, pady=24)
        tk.Label(
            footer,
            text="White, minimal and task-focused.\nDesigned for bench automation workflows.",
            bg=COLORS["surface"],
            fg=COLORS["text_muted"],
            font=FONTS["caption"],
            justify="left",
            anchor="w",
        ).pack(anchor="w")

        self.content_shell = tk.Frame(self.master, bg=COLORS["background"])
        self.content_shell.grid(row=0, column=1, sticky="nsew")
        self.content_shell.grid_rowconfigure(1, weight=1)
        self.content_shell.grid_columnconfigure(0, weight=1)

        header = tk.Frame(self.content_shell, bg=COLORS["background"], padx=32, pady=24)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title_box = tk.Frame(header, bg=COLORS["background"])
        title_box.grid(row=0, column=0, sticky="w")
        tk.Label(
            title_box,
            text="Instrument workspace",
            bg=COLORS["background"],
            fg=COLORS["text"],
            font=FONTS["title"],
        ).pack(anchor="w")
        self.page_subtitle = tk.Label(
            title_box,
            text="Configure, capture and process oscilloscope data in one place.",
            bg=COLORS["background"],
            fg=COLORS["text_muted"],
            font=FONTS["body"],
        )
        self.page_subtitle.pack(anchor="w", pady=(6, 0))

        status_card = tk.Frame(header, bg=COLORS["surface"], bd=1, relief="solid", padx=18, pady=14)
        status_card.grid(row=0, column=1, sticky="e")
        tk.Label(
            status_card,
            text="Connection",
            bg=COLORS["surface"],
            fg=COLORS["text_muted"],
            font=FONTS["caption"],
        ).pack(anchor="w")
        self.connection_label = tk.Label(
            status_card,
            text="Checking...",
            bg=COLORS["surface"],
            fg=COLORS["text_muted"],
            font=FONTS["body_bold"],
        )
        self.connection_label.pack(anchor="w", pady=(4, 0))

        self.display_frame = tk.Frame(self.content_shell, bg=COLORS["background"], padx=32, pady=0)
        self.display_frame.grid(row=1, column=0, sticky="nsew")
        self.display_frame.grid_columnconfigure(0, weight=1)
        self.display_frame.grid_rowconfigure(0, weight=1)

    def initialize_connection(self):
        try:
            self.oscilloscope = Oscilloscope(VISA_ADDRESS, 10000)
            self.measure = Measure(self.oscilloscope)
            self.set_connection_status("Connected to oscilloscope", COLORS["success"])
            messagebox.showinfo("Connection Status", "Successfully connected to the oscilloscope.")
        except Exception as error:
            self.oscilloscope = None
            self.measure = None
            self.set_connection_status("Disconnected", COLORS["danger"])
            messagebox.showerror("Connection Failed", f"Could not connect to the oscilloscope: {error}")

    def set_connection_status(self, text, color):
        self.connection_label.configure(text=text, fg=color)

    def select_page(self, key, callback):
        self.current_page = key
        self.update_nav_state()
        callback()

    def update_nav_state(self):
        for key, button in self.nav_buttons.items():
            if key == self.current_page:
                button.configure(bg=COLORS["accent_soft"], fg=COLORS["accent"])
            else:
                button.configure(bg=COLORS["surface"], fg=COLORS["text_muted"])

    def set_page_context(self, subtitle):
        self.page_subtitle.configure(text=subtitle)

    def clear_display_frame(self):
        for widget in self.display_frame.winfo_children():
            widget.destroy()

    def show_home(self):
        self.current_page = "home"
        self.update_nav_state()
        self.set_page_context("Connection setup, workspace defaults and live instrument discovery.")
        self.clear_display_frame()
        ConfigHome(self.display_frame)

    def show_axis_control(self):
        self.current_page = "axis"
        self.update_nav_state()
        self.set_page_context("Dial in timebase, channel scaling and markers with a cleaner control surface.")
        self.clear_display_frame()
        AxisControlPage(self.display_frame, self.oscilloscope)

    def show_waveform_capture(self):
        self.current_page = "capture"
        self.update_nav_state()
        self.set_page_context("Capture waveforms, inspect measurements and export results with fewer clicks.")
        self.clear_display_frame()
        WaveformCapture(self.display_frame, self.oscilloscope, self.measure)

    def show_script_editor(self):
        self.current_page = "script"
        self.update_nav_state()
        self.set_page_context("Build repeatable automation flows with a more structured visual editor.")
        self.clear_display_frame()
        ScriptEditor(self.display_frame)

    def show_run_script(self):
        self.current_page = "runner"
        self.update_nav_state()
        self.set_page_context("Load saved sequences and monitor execution status in real time.")
        self.clear_display_frame()
        RunScriptPage(self.display_frame)

    def show_batch_process(self):
        self.current_page = "batch"
        self.update_nav_state()
        self.set_page_context("Merge repeated measurement runs into a clean consolidated output package.")
        self.clear_display_frame()
        BatchProcessPage(self.display_frame)

    def show_settings(self):
        self.current_page = "settings"
        self.update_nav_state()
        self.set_page_context("Control default save locations and workspace preferences.")
        self.clear_display_frame()
        Setting(self.display_frame)


if __name__ == "__main__":
    root = tk.Tk()
    MainGUI(root)
    root.mainloop()
