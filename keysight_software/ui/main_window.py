import tkinter as tk
from tkinter import messagebox

from keysight_software import config
from keysight_software.device.measure import Measure
from keysight_software.device.oscilloscope import Oscilloscope
from keysight_software.ui.pages.axis_control import AxisControlPage
from keysight_software.ui.pages.batch_process import BatchProcessPage
from keysight_software.ui.pages.home import ConfigHome
from keysight_software.ui.pages.run_script import RunScriptPage
from keysight_software.ui.pages.script_editor import ScriptEditor
from keysight_software.ui.pages.settings import Setting
from keysight_software.ui.pages.waveform_capture import WaveformCapture
from keysight_software.ui.theme import COLORS, FONTS, configure_root, create_badge, create_button


class MainGUI:
    def __init__(self, master):
        self.master = master
        self.current_page = None
        self.nav_buttons = {}
        self.oscilloscope = None
        self.measure = None
        self.current_page_factory = None
        self.last_connection_error = None
        self.page_window_id = None
        self.mousewheel_bound = False

        configure_root(master)
        master.title("Keysight Automation Studio")
        master.geometry("1380x900")
        master.minsize(980, 680)
        master.grid_columnconfigure(1, weight=1)
        master.grid_rowconfigure(0, weight=1)
        master.bind("<Configure>", self.on_window_resize)

        self.build_shell()
        self.refresh_connection(show_dialog=False)
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

        self.header = tk.Frame(self.content_shell, bg=COLORS["background"], padx=32, pady=24)
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.grid_columnconfigure(0, weight=1)

        self.title_box = tk.Frame(self.header, bg=COLORS["background"])
        self.title_box.grid(row=0, column=0, sticky="w")
        tk.Label(
            self.title_box,
            text="Instrument workspace",
            bg=COLORS["background"],
            fg=COLORS["text"],
            font=FONTS["title"],
        ).pack(anchor="w")
        self.page_subtitle = tk.Label(
            self.title_box,
            text="Configure, capture and process oscilloscope data in one place.",
            bg=COLORS["background"],
            fg=COLORS["text_muted"],
            font=FONTS["body"],
            justify="left",
        )
        self.page_subtitle.pack(anchor="w", pady=(6, 0))

        self.status_card = tk.Frame(self.header, bg=COLORS["surface"], bd=1, relief="solid", padx=16, pady=14)
        self.status_card.grid(row=0, column=1, sticky="e")
        self.status_card.grid_columnconfigure(0, weight=1)

        top_row = tk.Frame(self.status_card, bg=COLORS["surface"])
        top_row.grid(row=0, column=0, sticky="ew")
        tk.Label(
            top_row,
            text="Connection",
            bg=COLORS["surface"],
            fg=COLORS["text_muted"],
            font=FONTS["caption"],
        ).pack(side="left")
        self.connection_label = create_badge(top_row, "Checking", tone="neutral")
        self.connection_label.pack(side="left", padx=(10, 0))
        create_button(
            top_row,
            "Reconnect",
            lambda: self.refresh_connection(show_dialog=True),
            tone="secondary",
        ).pack(side="right")
        self.connection_hint = tk.Label(
            self.status_card,
            text="You can work offline and reconnect later.",
            bg=COLORS["surface"],
            fg=COLORS["text_muted"],
            font=FONTS["caption"],
            justify="left",
            wraplength=280,
        )
        self.connection_hint.grid(row=1, column=0, sticky="w", pady=(10, 0))

        self.display_frame = tk.Frame(self.content_shell, bg=COLORS["background"], padx=32, pady=0)
        self.display_frame.grid(row=1, column=0, sticky="nsew")
        self.display_frame.grid_columnconfigure(0, weight=1)
        self.display_frame.grid_rowconfigure(0, weight=1)

        self.scroll_canvas = tk.Canvas(
            self.display_frame,
            bg=COLORS["background"],
            highlightthickness=0,
            bd=0,
        )
        self.scroll_canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar = tk.Scrollbar(
            self.display_frame,
            orient="vertical",
            command=self.scroll_canvas.yview,
            troughcolor=COLORS["background"],
            bg=COLORS["surface_alt"],
            activebackground=COLORS["shadow"],
            relief="flat",
            bd=0,
        )
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.scroll_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.page_container = tk.Frame(self.scroll_canvas, bg=COLORS["background"])
        self.page_container.grid_columnconfigure(0, weight=1)
        self.page_window_id = self.scroll_canvas.create_window((0, 0), window=self.page_container, anchor="nw")
        self.page_container.bind("<Configure>", self.on_page_container_configure)
        self.scroll_canvas.bind("<Configure>", self.on_scroll_canvas_configure)
        self.scroll_canvas.bind("<Enter>", self.bind_mousewheel)
        self.scroll_canvas.bind("<Leave>", self.unbind_mousewheel)

    def on_window_resize(self, event):
        if event.widget is not self.master:
            return
        compact = event.width < 1120
        self.sidebar.configure(width=220 if compact else 260)
        header_stacked = event.width < 1380
        if header_stacked:
            self.header.grid_columnconfigure(1, weight=0)
            self.status_card.grid_configure(row=1, column=0, sticky="ew", pady=(16, 0))
        else:
            self.header.grid_columnconfigure(1, weight=0)
            self.status_card.grid_configure(row=0, column=1, sticky="e", pady=0)
        self.page_subtitle.configure(wraplength=max(360, event.width - 760))
        self.connection_hint.configure(wraplength=240 if header_stacked else 280)

    def on_page_container_configure(self, _event):
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

    def on_scroll_canvas_configure(self, event):
        self.scroll_canvas.itemconfigure(self.page_window_id, width=event.width)

    def bind_mousewheel(self, _event=None):
        if not self.mousewheel_bound:
            self.master.bind_all("<MouseWheel>", self.on_mousewheel)
            self.master.bind_all("<Button-4>", self.on_mousewheel)
            self.master.bind_all("<Button-5>", self.on_mousewheel)
            self.mousewheel_bound = True

    def unbind_mousewheel(self, _event=None):
        if self.mousewheel_bound:
            self.master.unbind_all("<MouseWheel>")
            self.master.unbind_all("<Button-4>")
            self.master.unbind_all("<Button-5>")
            self.mousewheel_bound = False

    def on_mousewheel(self, event):
        if event.num == 4:
            self.scroll_canvas.yview_scroll(-1, "units")
            return
        if event.num == 5:
            self.scroll_canvas.yview_scroll(1, "units")
            return
        delta = int(-event.delta / 120) if event.delta else 0
        if delta:
            self.scroll_canvas.yview_scroll(delta, "units")

    def refresh_connection(self, show_dialog=False):
        try:
            if self.oscilloscope is not None:
                try:
                    self.oscilloscope.close()
                except Exception:
                    pass
            self.oscilloscope = Oscilloscope(config.VISA_ADDRESS, config.GLOBAL_TIMEOUT)
            self.measure = Measure(self.oscilloscope)
            self.last_connection_error = None
            self.set_connection_status("Connected to oscilloscope", COLORS["success"])
            self.connection_hint.configure(text="Live instrument detected. Measurement pages are fully enabled.")
            if show_dialog:
                messagebox.showinfo("Connection Status", "Successfully connected to the oscilloscope.")
        except Exception as error:
            self.oscilloscope = None
            self.measure = None
            self.last_connection_error = str(error)
            self.set_connection_status("Disconnected", COLORS["warning"])
            self.connection_hint.configure(text="Offline mode is active. Live capture controls will stay disabled.")
            if show_dialog:
                messagebox.showwarning("Connection Unavailable", f"Could not connect to the oscilloscope: {error}")

        if self.current_page_factory is not None:
            self.current_page_factory()

    def set_connection_status(self, text, color):
        tone = "success" if color == COLORS["success"] else "warning"
        background = "#e7f6ec" if tone == "success" else "#fff5e6"
        self.connection_label.configure(text=text, bg=background, fg=color)

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
        for widget in self.page_container.winfo_children():
            widget.destroy()
        self.scroll_canvas.yview_moveto(0)

    def show_home(self):
        self.current_page = "home"
        self.current_page_factory = self.show_home
        self.update_nav_state()
        self.set_page_context("Connection setup, workspace defaults and live instrument discovery.")
        self.clear_display_frame()
        ConfigHome(
            self.page_container,
            connect_callback=lambda show_dialog=True: self.refresh_connection(show_dialog=show_dialog),
            connection_error=self.last_connection_error,
        )

    def show_axis_control(self):
        self.current_page = "axis"
        self.current_page_factory = self.show_axis_control
        self.update_nav_state()
        self.set_page_context("Dial in timebase, channel scaling and markers with a cleaner control surface.")
        self.clear_display_frame()
        AxisControlPage(self.page_container, self.oscilloscope)

    def show_waveform_capture(self):
        self.current_page = "capture"
        self.current_page_factory = self.show_waveform_capture
        self.update_nav_state()
        self.set_page_context("Capture waveforms, inspect measurements and export results with fewer clicks.")
        self.clear_display_frame()
        WaveformCapture(self.page_container, self.oscilloscope, self.measure)

    def show_script_editor(self):
        self.current_page = "script"
        self.current_page_factory = self.show_script_editor
        self.update_nav_state()
        self.set_page_context("Build repeatable automation flows with a more structured visual editor.")
        self.clear_display_frame()
        ScriptEditor(self.page_container, self.oscilloscope, self.measure)

    def show_run_script(self):
        self.current_page = "runner"
        self.current_page_factory = self.show_run_script
        self.update_nav_state()
        self.set_page_context("Load saved sequences and monitor execution status in real time.")
        self.clear_display_frame()
        RunScriptPage(self.page_container, self.oscilloscope, self.measure)

    def show_batch_process(self):
        self.current_page = "batch"
        self.current_page_factory = self.show_batch_process
        self.update_nav_state()
        self.set_page_context("Merge repeated measurement runs into a clean consolidated output package.")
        self.clear_display_frame()
        BatchProcessPage(self.page_container)

    def show_settings(self):
        self.current_page = "settings"
        self.current_page_factory = self.show_settings
        self.update_nav_state()
        self.set_page_context("Control default save locations and workspace preferences.")
        self.clear_display_frame()
        Setting(self.page_container)


if __name__ == "__main__":
    root = tk.Tk()
    MainGUI(root)
    root.mainloop()
