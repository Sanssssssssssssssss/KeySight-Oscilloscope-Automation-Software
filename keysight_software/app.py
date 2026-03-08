import os
import sys
from pathlib import Path

from keysight_software.paths import bundled_path


class Application:
    """Main application class that initializes the GUI."""

    def __init__(self, root):
        self.master = root
        from keysight_software.ui.main_window import MainGUI

        self.app = MainGUI(self.master)


def configure_tk_runtime():
    """Point Tkinter at a Tcl/Tk runtime that matches the active Python."""
    bundled_root = bundled_path("_internal")
    bundled_tcl = bundled_path("_internal", "_tcl_data")
    bundled_tk = bundled_path("_internal", "_tk_data")
    base_prefix = getattr(sys, "base_prefix", sys.prefix)
    system_tcl = Path(base_prefix) / "tcl" / "tcl8.6"
    system_tk = Path(base_prefix) / "tcl" / "tk8.6"

    if bundled_root.exists():
        try:
            os.add_dll_directory(str(bundled_root))
        except (AttributeError, FileNotFoundError):
            pass

    if system_tcl.exists():
        os.environ["TCL_LIBRARY"] = str(system_tcl)
    elif bundled_tcl.exists() and "TCL_LIBRARY" not in os.environ:
        os.environ["TCL_LIBRARY"] = str(bundled_tcl)

    if system_tk.exists():
        os.environ["TK_LIBRARY"] = str(system_tk)
    elif bundled_tk.exists() and "TK_LIBRARY" not in os.environ:
        os.environ["TK_LIBRARY"] = str(bundled_tk)


def main():
    configure_tk_runtime()
    import tkinter as tk

    root = tk.Tk()
    Application(root)
    root.mainloop()


if __name__ == "__main__":
    main()
