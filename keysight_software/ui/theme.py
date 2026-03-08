import tkinter as tk
from tkinter import scrolledtext


COLORS = {
    "background": "#f5f5f7",
    "surface": "#ffffff",
    "surface_alt": "#fbfbfd",
    "border": "#d9d9de",
    "border_strong": "#c7c7cc",
    "text": "#111111",
    "text_muted": "#6e6e73",
    "accent": "#0071e3",
    "accent_hover": "#0062c4",
    "accent_soft": "#e7f1ff",
    "success": "#2e7d32",
    "warning": "#c77700",
    "danger": "#b42318",
    "shadow": "#ececf1",
}

FONTS = {
    "hero": ("Segoe UI", 24, "bold"),
    "title": ("Segoe UI", 18, "bold"),
    "heading": ("Segoe UI", 13, "bold"),
    "body": ("Segoe UI", 10),
    "body_bold": ("Segoe UI", 10, "bold"),
    "caption": ("Segoe UI", 9),
    "mono": ("Cascadia Code", 10),
}


def configure_root(window):
    window.configure(bg=COLORS["background"])
    try:
        window.option_add("*Font", FONTS["body"])
        window.option_add("*Background", COLORS["background"])
        window.option_add("*Foreground", COLORS["text"])
    except tk.TclError:
        pass


def style_toplevel(window, title=None, geometry=None):
    configure_root(window)
    if title:
        window.title(title)
    if geometry:
        window.geometry(geometry)


def create_frame(parent, bg=None, **pack_or_grid_safe):
    frame = tk.Frame(parent, bg=bg or COLORS["background"], **pack_or_grid_safe)
    return frame


def create_card(parent, padding=24):
    card = tk.Frame(
        parent,
        bg=COLORS["surface"],
        bd=1,
        relief="solid",
        highlightthickness=0,
    )
    inner = tk.Frame(card, bg=COLORS["surface"], padx=padding, pady=padding)
    inner.pack(fill="both", expand=True)
    return card, inner


def create_title(parent, text, subtitle=None):
    wrapper = tk.Frame(parent, bg=parent.cget("bg"))
    tk.Label(
        wrapper,
        text=text,
        font=FONTS["hero"],
        bg=wrapper.cget("bg"),
        fg=COLORS["text"],
        anchor="w",
    ).pack(anchor="w")
    if subtitle:
        tk.Label(
            wrapper,
            text=subtitle,
            font=FONTS["body"],
            bg=wrapper.cget("bg"),
            fg=COLORS["text_muted"],
            anchor="w",
            justify="left",
        ).pack(anchor="w", pady=(6, 0))
    return wrapper


def create_section_heading(parent, text, subtitle=None):
    wrapper = tk.Frame(parent, bg=parent.cget("bg"))
    tk.Label(
        wrapper,
        text=text,
        font=FONTS["heading"],
        bg=wrapper.cget("bg"),
        fg=COLORS["text"],
        anchor="w",
    ).pack(anchor="w")
    if subtitle:
        tk.Label(
            wrapper,
            text=subtitle,
            font=FONTS["caption"],
            bg=wrapper.cget("bg"),
            fg=COLORS["text_muted"],
            anchor="w",
            justify="left",
        ).pack(anchor="w", pady=(4, 0))
    return wrapper


def create_label(parent, text, muted=False, font=None, **kwargs):
    return tk.Label(
        parent,
        text=text,
        bg=parent.cget("bg"),
        fg=COLORS["text_muted"] if muted else COLORS["text"],
        font=font or FONTS["body"],
        **kwargs,
    )


def create_button(parent, text, command, tone="secondary", width=None):
    palette = {
        "primary": (COLORS["accent"], "#ffffff", COLORS["accent_hover"]),
        "secondary": (COLORS["surface_alt"], COLORS["text"], COLORS["shadow"]),
        "ghost": (parent.cget("bg"), COLORS["text_muted"], COLORS["accent_soft"]),
        "danger": ("#fff2f0", COLORS["danger"], "#ffe4e0"),
    }
    bg, fg, active = palette[tone]
    return tk.Button(
        parent,
        text=text,
        command=command,
        width=width,
        bg=bg,
        fg=fg,
        activebackground=active,
        activeforeground=fg,
        relief="flat",
        bd=0,
        padx=14,
        pady=8,
        cursor="hand2",
        font=FONTS["body_bold"],
        highlightthickness=0,
    )


def create_entry(parent, textvariable=None, width=None):
    return tk.Entry(
        parent,
        textvariable=textvariable,
        width=width,
        bg=COLORS["surface_alt"],
        fg=COLORS["text"],
        relief="flat",
        bd=0,
        insertbackground=COLORS["text"],
        highlightthickness=1,
        highlightbackground=COLORS["border"],
        highlightcolor=COLORS["accent"],
        font=FONTS["body"],
    )


def create_checkbutton(parent, text, variable):
    return tk.Checkbutton(
        parent,
        text=text,
        variable=variable,
        bg=parent.cget("bg"),
        fg=COLORS["text"],
        activebackground=parent.cget("bg"),
        activeforeground=COLORS["text"],
        selectcolor=COLORS["surface"],
        relief="flat",
        bd=0,
        highlightthickness=0,
        font=FONTS["body"],
    )


def create_option_menu(parent, variable, options):
    menu = tk.OptionMenu(parent, variable, *options)
    menu.configure(
        bg=COLORS["surface_alt"],
        fg=COLORS["text"],
        activebackground=COLORS["accent_soft"],
        activeforeground=COLORS["text"],
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightbackground=COLORS["border"],
        font=FONTS["body"],
    )
    menu["menu"].configure(
        bg=COLORS["surface"],
        fg=COLORS["text"],
        activebackground=COLORS["accent_soft"],
        activeforeground=COLORS["text"],
        bd=0,
        font=FONTS["body"],
    )
    return menu


def create_scrolled_text(parent, height=10, readonly=False, mono=False):
    widget = scrolledtext.ScrolledText(
        parent,
        height=height,
        wrap=tk.WORD,
        bg=COLORS["surface_alt"],
        fg=COLORS["text"],
        relief="flat",
        bd=0,
        insertbackground=COLORS["text"],
        selectbackground=COLORS["accent_soft"],
        padx=14,
        pady=14,
        font=FONTS["mono"] if mono else FONTS["body"],
        highlightthickness=1,
        highlightbackground=COLORS["border"],
        highlightcolor=COLORS["accent"],
    )
    if readonly:
        widget.configure(state="disabled")
    return widget


def create_badge(parent, text, tone="neutral"):
    mapping = {
        "neutral": (COLORS["surface_alt"], COLORS["text_muted"]),
        "success": ("#e7f6ec", COLORS["success"]),
        "warning": ("#fff5e6", COLORS["warning"]),
        "danger": ("#fff1f2", COLORS["danger"]),
        "accent": (COLORS["accent_soft"], COLORS["accent"]),
    }
    bg, fg = mapping[tone]
    return tk.Label(
        parent,
        text=text,
        bg=bg,
        fg=fg,
        font=FONTS["caption"],
        padx=9,
        pady=4,
    )


def set_text(widget, text):
    widget.configure(state="normal")
    widget.delete("1.0", tk.END)
    widget.insert("1.0", text)


def append_text(widget, text):
    widget.configure(state="normal")
    widget.insert(tk.END, text)
    widget.see(tk.END)
