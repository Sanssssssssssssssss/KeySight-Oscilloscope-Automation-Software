"""
===================================================
Created on: 20-07-2024
Author: Chang Xu
File: main.py
Version: 1.14
Language: Python 3.12.3
Description:
This script serves as the main entry point for the oscilloscope
control application. It initializes the GUI and manages the
interaction between different modules, including oscilloscope
communication and measurement functions.
===================================================
"""


from oscilloscope import Oscilloscope
from measure import Measure
import config
from GUI import MainGUI
import tkinter as tk
from tkinter import messagebox


class Application:
    """Main application class that initializes the GUI and manages the
    overall functionality of the oscilloscope control software."""
    def __init__(self, root):
        self.master = root

        # Initialize the main GUI interface
        self.app = MainGUI(self.master)


def main():
    root = tk.Tk()
    app = Application(root)
    root.mainloop()


if __name__ == "__main__":
    main()

