"""
===================================================
Created on: 21-7-2024
Author: Chang Xu
File: config.py
Version: 1.0
Language: Python 3.12.3
Description:
This script defines global configuration variables
for the Keysight oscilloscope automation system,
including VISA address, timeout, file paths, and
utility functions to update these configurations.
===================================================
"""


# Global variable for VISA address used for instrument communication
VISA_ADDRESS = "USB0::0x0957::0x1780::MY55310270::0::INSTR"

# Default timeout for VISA operations (in milliseconds)
GLOBAL_TIMEOUT = 10000

# Base directory for saving files
BASE_DIRECTORY = "C:\\Users\\Public\\"

# Default filename for data storage
BASE_FILENAME = "my_data"


def update_visa_address(new_address):
    """ Update the VISA address for instrument communication """
    global VISA_ADDRESS
    VISA_ADDRESS = new_address


def update_global_timeout(new_timeout):
    """ Update the global timeout setting """
    global GLOBAL_TIMEOUT
    GLOBAL_TIMEOUT = new_timeout


def update_base_directory(new_directory):
    """ Update the base directory for saving files """
    global BASE_DIRECTORY
    BASE_DIRECTORY = new_directory


def update_base_filename(new_filename):
    """ Update the default filename for data storage """
    global BASE_FILENAME
    BASE_FILENAME = new_filename

