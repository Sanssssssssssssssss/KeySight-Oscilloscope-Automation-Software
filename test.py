"""
===================================================
Created on: 21-07-2024
Author: Chang Xu
File: test.py
Version: 1.6
Language: Python 3.12.3
Description:
This script tests the communication with an oscilloscope
using the VISA protocol. It queries the oscilloscope for
available SCPI commands, including device identification,
measurement catalog, and system help information.
===================================================
"""

import pyvisa
from config import VISA_ADDRESS  # Import global VISA address


def query_oscilloscope_commands(visa_address):
    """
    Query the oscilloscope for available SCPI commands.

    This function attempts to communicate with an oscilloscope using the VISA protocol.
    It retrieves device identification, measurement catalog, and system help information.
    """
    try:
        # Create a resource manager
        rm = pyvisa.ResourceManager()

        # Open the oscilloscope resource
        oscilloscope = rm.open_resource(visa_address)
        oscilloscope.timeout = 5000  # Set timeout to 5 seconds

        # Query the oscilloscope identification
        print("Querying oscilloscope identification...")
        available_commands = oscilloscope.query("*IDN?")
        print("Oscilloscope Identification:")
        print(available_commands)

        # Query the measurement catalog (list of supported measurements)
        try:
            print("\nQuerying measurement catalog...")
            measurement_catalog = oscilloscope.query(":MEASure:CATalog?")
            print("Measurement Catalog:")
            print(measurement_catalog)
        except pyvisa.errors.VisaIOError as e:
            print(f"Measurement catalog query error: {e}")

        # Query system help information (if supported)
        try:
            print("\nQuerying system help information...")
            system_help = oscilloscope.query(":SYSTem:HELP?")
            print("System Help Information:")
            print(system_help)
        except pyvisa.errors.VisaIOError as e:
            print(f"System help query error: {e}")

        # Close the connection to the oscilloscope
        oscilloscope.close()

    except pyvisa.errors.VisaIOError as e:
        print(f"A VISA communication error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    # Use the global VISA address from the config file
    query_oscilloscope_commands(VISA_ADDRESS)
