import tkinter as tk

from keysight_software.ui.main_window import MainGUI


class Application:
    """Main application class that initializes the GUI."""

    def __init__(self, root):
        self.master = root
        self.app = MainGUI(self.master)


def main():
    root = tk.Tk()
    Application(root)
    root.mainloop()


if __name__ == "__main__":
    main()
