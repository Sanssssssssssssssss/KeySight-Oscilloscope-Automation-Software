"""
===================================================
Created on: 21-7--2024
Author: Chang Xu
File: ScriptEditor.py
Version: 3.2
Language: Python 3.12.3
Description:
This script defines the Script Editor interface
for managing and executing oscilloscope control
sequences. Users can create, edit, save, load,
and run measurement scripts in a visual manner.
===================================================
"""


import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox,Toplevel
import json
import time
from waveform_config import WaveformConfig
from oscilloscope import Oscilloscope
from waveform_capture import WaveformCapture  # Import the existing class
from measure import Measure
from AxisControlConfig import AxisControlConfig
import os
from run_script_page import RunScriptPage  # Adjust the import path if necessary

from config import VISA_ADDRESS  # Import global variable


class ScriptEditor(tk.Frame):
    def __init__(self, master=None):
        """Initialize the ScriptEditor UI, set up the canvas, slots, and buttons for creating, saving, and running scripts."""
        super().__init__(master)
        self.master = master
        self.grid(sticky=tk.NSEW)  # Extraction Channel Number

        # Canvas for drawing modules, slots, and connections
        self.canvas = tk.Canvas(self, width=800, height=500, bg='white')
        self.canvas.grid(row=0, column=0, pady=10, sticky=tk.NSEW)  # Instead, use grid() and set the fill property

        # Console for displaying the sequence
        self.console = tk.Text(self, height=10, bg='black', fg='white')
        self.console.grid(row=1, column=0, sticky=tk.NSEW)  # Use grid() to place
        self.save_directory = tk.StringVar(value="")

        # Attempt to initialize the WaveformCapture instance
        try:
            osc = Oscilloscope(VISA_ADDRESS, 10000)
            measure = Measure(osc)
            self.oscilloscope = osc
            self.measure = measure
            messagebox.showinfo("Connection Status", "Successfully connected to the oscilloscope.")
        except Exception as e:
            messagebox.showerror("Connection Failed", f"Could not connect to the oscilloscope: {e}")

        # Define slots
        self.slots = []
        for i in range(10):
            slot = self.canvas.create_rectangle(150 + i * 130, 200, 220 + i * 130, 250, dash=(4, 2))
            self.slots.append(slot)

        # Pre-generate modules on the left side
        self.modules = []
        self.create_module("Start", "lightgray", 50, 50)
        self.create_module("Wave Cap", "lightblue", 50, 150)
        self.create_module("Axis Control", "lightgreen", 50, 250)
        self.create_module("End", "lightgray", 50, 350)
        self.create_delay_module()

        # For storing placed modules
        self.placed_modules = [None] * len(self.slots)

        self.dragged_module = None

        # Buttons for saving, loading, and running scripts
        btn_frame = tk.Frame(self)
        btn_frame.grid(row=2, column=0, pady=10)  # use grid()

        tk.Button(btn_frame, text="Save Script", command=self.save_script).grid(row=0, column=0)
        tk.Button(btn_frame, text="Load Script", command=self.load_script).grid(row=0, column=1)
        tk.Button(btn_frame, text="Run Script", command=self.run_script).grid(row=1, column=0, columnspan=2)
        tk.Button(btn_frame, text="Browse Save Folder", command=self.browse_save_directory).grid(row=0, column=2)

        # Label to show the selected directory
        self.save_path_label = tk.Label(btn_frame, text="Save Path: None", fg="blue")
        self.save_path_label.grid(row=0, column=3, padx=10, pady=5)

        # Adjust window weights for proper resizing
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_rowconfigure(1, weight=1)
        self.master.grid_columnconfigure(0, weight=1)
        self.master.bind("<Configure>", self.on_resize)
        # Configure weights for resizing
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_rowconfigure(1, weight=0)  # Ensure that the Console is not squeezed by the Canvas
        self.master.grid_columnconfigure(0, weight=1)

    def on_resize(self, event):
        """Adjust the width of the canvas when the window is resized, ensuring slots remain positioned correctly."""
        self.canvas.config(width=event.width)  # Only the width of the Canvas is adjusted, not the height.
        self.update_slots_position(event.width)  # Adjusting the position of the module slot
        # Do not adjust the width of the Console

    def update_slots_position(self, canvas_width):
        """Recalculate and update the position of slots dynamically based on the canvas width."""
        slot_width = canvas_width // len(self.slots)  # Dynamically calculate the width of each slot
        for i, slot in enumerate(self.slots):
            x1 = i * slot_width + 10  # The x-coordinate of the upper left corner of each slot
            x2 = (i + 1) * slot_width - 10  # The x-coordinate of the lower right corner of each slot
            y1, y2 = 200, 250  # The y-coordinate stays the same
            self.canvas.coords(slot, x1, y1, x2, y2)  # Update the location of the slot

    def create_module(self, text, color, x, y):
        """Create a module with a specified type, color, and position, and bind interaction events."""
        module_id = f"{text}_{int(time.time() * 1000)}"  # Create a unique ID for each module
        module = self.canvas.create_rectangle(x, y, x + 100, y + 50, fill=color)
        label = self.canvas.create_text(x + 50, y + 25, text=text)
        self.modules.append({"type": text, "id": module_id, "canvas_id": module, "x": x, "y": y, "label_id": label})
        self.canvas.tag_bind(module, "<Button-1>", self.start_drag)
        self.canvas.tag_bind(module, "<B1-Motion>", self.drag_module)
        self.canvas.tag_bind(module, "<ButtonRelease-1>", self.drop_module)

        # Bind the double-click event to open the configuration window
        self.canvas.tag_bind(module, "<Double-1>", lambda event, mod_id=module_id: self.open_config_window(mod_id))

    def create_delay_module(self):
        """Create a delay module, which allows adding a time delay in the script."""
        self.create_module("Delay", "orange", 50, 450)

    def delay_config_exists(self, module_id):
        """Check if there is a delayed configuration for a given module ID"""
        config = self.load_all_configs()  # Load all configurations
        return module_id in config  # Check if the module ID is in the configuration

    def open_config_window(self, module_id):
        """Open the configuration window for a specific module type (Delay, Wave Cap, Axis Control)."""
        config_window = tk.Toplevel(self.master)
        module_type = None

        # Determine the type of module to double-click
        for module in self.modules:
            if module['id'] == module_id:
                module_type = module['type']
                break

        if module_type == "Delay":
            config_window.title(f"Configure {module_type} Module {module_id}")

            # Detecting and loading the configuration of a delay module
            delay_time = tk.DoubleVar(
                value=self.load_delay_config(module_id) if self.delay_config_exists(module_id) else 1.0)

            tk.Label(config_window, text="Enter delay in seconds:").pack(padx=10, pady=5)
            tk.Entry(config_window, textvariable=delay_time).pack(padx=10, pady=5)

            # Save button
            tk.Button(config_window, text="Save",
                      command=lambda: self.save_delay_config(module_id, delay_time, config_window)).pack(pady=10)

            # Add another Delay Module button
            tk.Button(config_window, text="Add Another Delay Module", command=self.create_delay_module).pack(pady=10)

        elif module_type == "Wave Cap":
            # Detecting and loading the WaveformConfig configuration
            if os.path.exists("waveform_config.json"):
                WaveformConfig(config_window).load_configuration()
            else:
                WaveformConfig(config_window)

        elif module_type == "Axis Control":
            config_window.title(f"Configure {module_type} Module {module_id}")

            # Detecting and loading AxisControlConfig configuration
            if os.path.exists("axis_config.json"):
                AxisControlConfig(config_window).load_configuration()
            else:
                AxisControlConfig(config_window)

        else:
            config_window.destroy()  # If no specific configuration is available, close the window

    def save_delay_config(self, module_id, delay_var, config_window):
        """Save the delay configuration for a given module and close the config window."""
        delay_time = delay_var.get()
        print(f"Delay set to {delay_time} seconds for module {module_id}.")

        # Save delay configuration to a JSON file
        config = self.load_all_configs()
        config[module_id] = delay_time
        self.save_all_configs(config)

        # Save the delay time to the module's data
        for module in self.modules:
            if module['id'] == module_id:
                module['delay'] = delay_time
                break

        config_window.destroy()
        self.update_console()

    def load_delay_config(self, module_id):
        """Load the delay configuration for a given module ID from the configuration file."""
        config = self.load_all_configs()
        return config.get(module_id, 1.0)  # Return saved delay time or default to 1.0 seconds

    def load_all_configs(self):
        """Load all module configurations from the configurations.json file."""
        try:
            with open('configurations.json', 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_all_configs(self, config):
        """Save all module configurations to the configurations.json file."""
        with open('configurations.json', 'w') as f:
            json.dump(config, f, indent=4)

    def update_console(self):
        """Refresh the console to display the current sequence of modules."""
        self.console.delete(1.0, tk.END)
        for i, module_id in enumerate(self.placed_modules):
            if module_id:
                # Find the module by ID
                module = next((mod for mod in self.modules if mod["id"] == module_id), None)
                if module:
                    display_text = module["type"]
                    # Add delay time if the module is a Delay
                    if module["type"] == "Delay" and "delay" in module:
                        display_text += f" ({module['delay']} seconds)"
                    # Optionally add other module-specific parameters here
                    self.console.insert(tk.END, f"{i + 1}. {display_text}\n")

    def start_drag(self, event):
        """Start dragging a module when clicked and prepare for repositioning."""
        self.dragged_module = self.canvas.find_withtag("current")[0]

    def browse_save_directory(self):
        """Open a dialog for selecting a save directory and update the save path label."""
        directory = filedialog.askdirectory()
        if directory:
            self.save_directory.set(directory)
            self.save_path_label.config(text=f"Save Path: {directory}")  # Update the Label of the path display

    def drag_module(self, event):
        """Move a module along with its label while dragging on the canvas."""
        if self.dragged_module:
            x, y = event.x, event.y
            coords = self.canvas.coords(self.dragged_module)
            dx, dy = x - coords[0], y - coords[1]
            self.canvas.move(self.dragged_module, dx, dy)

            # Move the associated label with the module
            for module in self.modules:
                if module['canvas_id'] == self.dragged_module:
                    self.canvas.move(module['label_id'], dx, dy)

            # Remove the module from the slot if dragged away
            self.remove_module_from_slot(self.dragged_module)

    def drop_module(self, event):
        """Drop a module into the closest available slot and update the UI accordingly."""
        if self.dragged_module:
            closest_slot = None
            min_distance = float('inf')
            for slot in self.slots:
                slot_coords = self.canvas.coords(slot)
                slot_center_x = (slot_coords[0] + slot_coords[2]) / 2
                slot_center_y = (slot_coords[1] + slot_coords[3]) / 2
                module_coords = self.canvas.coords(self.dragged_module)
                module_center_x = (module_coords[0] + module_coords[2]) / 2
                module_center_y = (module_coords[1] + module_coords[3]) / 2
                distance = ((module_center_x - slot_center_x) ** 2 + (module_center_y - slot_center_y) ** 2) ** 0.5
                if distance < min_distance:
                    min_distance = distance
                    closest_slot = slot

            if min_distance < 50:
                slot_coords = self.canvas.coords(closest_slot)
                self.canvas.coords(self.dragged_module, slot_coords[0], slot_coords[1], slot_coords[2], slot_coords[3])
                for module in self.modules:
                    if module['canvas_id'] == self.dragged_module:
                        self.canvas.coords(module['label_id'], (slot_coords[0] + slot_coords[2]) / 2,
                                           (slot_coords[1] + slot_coords[3]) / 2)

                        # Update placed_modules array
                        slot_index = self.slots.index(closest_slot)
                        self.placed_modules[slot_index] = module['id']

                        # Update the console display and redraw arrows
                        self.update_console()
                        self.draw_arrows()

            self.dragged_module = None

    def save_script(self):
        """Save the current script sequence as a JSON file in the selected directory."""
        # Check if a save directory is selected
        if not self.save_directory.get():
            messagebox.showwarning("Save Script", "Please select a save directory first.")
            return

        # Create a new folder
        timestamp = time.strftime("%Y%m%d_%H%M%S")  # Generate unique folder names using timestamps
        save_folder = os.path.join(self.save_directory.get(), f"script_{timestamp}")
        os.makedirs(save_folder, exist_ok=True)

        sequence_data = {
            "modules": []
        }
        config_data = self.load_all_configs()

        # Gather information about each module in the sequence
        for module_id in self.placed_modules:
            if module_id:
                module = next((mod for mod in self.modules if mod["id"] == module_id), None)
                if module:
                    module_type = module["type"]
                    module_info = {"type": module_type}

                    if module_type == "Delay":
                        # Add delay configuration to the sequence
                        module_info["delay"] = config_data.get(module_id, 1.0)
                    elif module_type == "Wave Cap":
                        module_info["config"] = "waveform_config.json"
                    elif module_type == "Axis Control":
                        module_info["config"] = "axis_config.json"

                    sequence_data["modules"].append(module_info)

        # Save the sequence JSON file into the newly created folder
        sequence_filepath = os.path.join(save_folder, "sequence.json")
        with open(sequence_filepath, 'w') as f:
            json.dump(sequence_data, f, indent=4)

        # Copy other configuration files into the save directory if they exist
        for config_file in ["waveform_config.json", "axis_config.json"]:
            if os.path.exists(config_file):
                destination = os.path.join(save_folder, config_file)
                with open(config_file, 'r') as src, open(destination, 'w') as dst:
                    dst.write(src.read())

        messagebox.showinfo("Save Script", f"Script saved successfully to {save_folder}")

    def load_script(self):
        """Browse and select the folder containing the script to load."""
        directory = filedialog.askdirectory()  # Ask the user to select a directory
        if directory:
            # Construct the path for the 'sequence.json' file
            script_filepath = os.path.join(directory, "sequence.json")
            if os.path.exists(script_filepath):
                with open(script_filepath, 'r') as f:
                    script_data = json.load(f)

                # Clear the canvas and reset the module list and slots
                self.canvas.delete('all')
                self.modules.clear()
                self.slots.clear()  # Clear slots list to avoid duplicates

                # Recreate slots based on the number of slots defined (e.g., 10 slots as in your initial setup)
                for i in range(10):  # Adjust if needed to match the number of slots you want
                    slot = self.canvas.create_rectangle(150 + i * 130, 200, 220 + i * 130, 250, dash=(4, 2))
                    self.slots.append(slot)

                # Iterate through the modules in the JSON file and create them
                for module_data in script_data["modules"]:
                    module_type = module_data["type"]

                    if module_type == "Start":
                        self.create_module("Start", "lightgray", 50, 50)
                    elif module_type == "Wave Cap":
                        self.create_module("Wave Cap", "lightblue", 50, 150)
                    elif module_type == "Axis Control":
                        self.create_module("Axis Control", "lightgreen", 50, 250)
                    elif module_type == "End":
                        self.create_module("End", "lightgray", 50, 350)
                    elif module_type == "Delay":
                        self.create_delay_module()
                        # Apply delay settings if they exist in the module data
                        delay_module = self.modules[-1]  # Assume it's the last added module
                        if "delay" in module_data:
                            delay_module["delay"] = module_data["delay"]

                # Update the console display to reflect the new module configuration
                self.update_console()
                self.draw_arrows()

                # Inform the user that the script has been successfully loaded
                messagebox.showinfo("Load Script", "Script loaded successfully!")
            else:
                messagebox.showerror("File Not Found", "sequence.json not found in the selected directory.")

    def run_script(self):
        """Run a selected script by opening the RunScriptPage in a new window."""
        # Check if there is a script path to load from
        script_filepath = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not script_filepath:
            messagebox.showwarning("Run Script", "No script selected. Please load a script first.")
            return

        # Create a new Toplevel window
        script_window = Toplevel(self.master)
        script_window.title("Run Script")
        script_window.geometry("800x600")  # Set the size of the new window

        # Initialize the RunScriptPage in the new window
        run_page = RunScriptPage(script_window)
        run_page.script_path.set(script_filepath)  # Set the script path to the loaded file
        run_page.load_script(script_filepath)  # Load the script in the RunScriptPage

        # Optionally, you can set the focus to the new window
        script_window.grab_set()
        script_window.transient(self.master)
        script_window.mainloop()

    def get_module_by_id(self, canvas_id):
        """Returns the module dictionary given its canvas ID."""
        for module in self.modules:
            if module["canvas_id"] == canvas_id:  # Ensure we're checking against the correct key
                return module
        return None

    def remove_module_from_slot(self, module_id):
        """Remove a module from its slot and update the UI accordingly."""
        module = self.get_module_by_id(module_id)
        if module is None:
            return  # If the module wasn't found, exit the function

        for i, placed_module in enumerate(self.placed_modules):
            if placed_module is not None and placed_module == module['id']:
                self.placed_modules[i] = None
                self.update_console()
                self.draw_arrows()
                break

    def draw_arrows(self):
        """Redraw arrows between slots that have modules placed in them."""
        # Clear existing arrows
        self.canvas.delete('arrow')

        # Draw new arrows between filled slots
        for i in range(len(self.placed_modules) - 1):
            if self.placed_modules[i] and self.placed_modules[i + 1]:
                slot1_coords = self.canvas.coords(self.slots[i])
                slot2_coords = self.canvas.coords(self.slots[i + 1])
                x1, y1 = (slot1_coords[2], (slot1_coords[1] + slot1_coords[3]) / 2)
                x2, y2 = (slot2_coords[0], (slot2_coords[1] + slot2_coords[3]) / 2)
                self.canvas.create_line(x1, y1, x2, y2, arrow=tk.LAST, tags='arrow')


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1000x750")
    app = ScriptEditor(master=root)
    root.mainloop()