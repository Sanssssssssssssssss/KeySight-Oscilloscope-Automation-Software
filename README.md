# Keysight Automation Studio

Keysight Automation Studio is a Windows desktop application for controlling Keysight oscilloscopes, capturing waveforms, applying bench presets, building scriptable automation flows, and exporting measurement data. The current default client is a Qt-based interface optimized for bench use on Windows.

## What It Does

- Connects to Keysight oscilloscopes over VISA / SCPI
- Captures multi-channel waveform data
- Calculates scalar measurements such as Vpp, frequency, period, rise time, duty cycle, phase, and more
- Exports screenshots, waveform plots, CSV data, and Excel measurement reports
- Saves and reuses axis, waveform, and script presets
- Runs repeatable automation sequences with capture, axis control, and delay steps
- Merges repeated run outputs with the batch processing page

## Current App Structure

- `main.py`: default Qt entrypoint
- `main_tk.py`: legacy Tk compatibility entrypoint
- `keysight_software/qt_app/`: current desktop client
- `keysight_software/ui/`: legacy Tk client
- `configs/`: local configuration and preset files

## Windows Release

The repository includes a packaged Windows build:

- `KeysightSoftware.exe`
- `_internal/`

To run the packaged app on Windows:

```powershell
.\KeysightSoftware.exe
```

## Local Development

Create and activate the virtual environment, then install dependencies:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Run the default Qt client:

```powershell
python .\main.py
```

Run the legacy Tk client:

```powershell
python .\main_tk.py
```

## Packaging

This project is currently packaged for Windows with PyInstaller:

```powershell
python -m PyInstaller build.spec --noconfirm --clean
```

The generated Windows release bundle is intended for Windows only.

## Dependencies

- `PySide6`
- `PyVISA`
- `numpy`
- `matplotlib`
- `openpyxl`
- `pandas`
- `Pillow`

Notes:

- `tkinter` is only needed for the legacy client and is provided by the Python installation.
- Live instrument communication also requires a system VISA runtime such as NI-VISA or Keysight IO Libraries.

## Project Description

This project is aimed at oscilloscope automation workflows where engineers need a single desktop tool for instrument connection, waveform acquisition, preset management, automated script execution, and export of measurement results. It is designed for Windows bench environments and prioritizes repeatability, offline-safe editing, and practical operator workflows over generic demo UI patterns.
