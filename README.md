# KeySight Oscilloscope Automation Software

## 📌 Project Overview

KeySight Oscilloscope Automation Software is a Python-based automation tool for controlling, acquiring, analyzing, and storing waveform data from KeySight oscilloscopes. It supports USB-connected oscilloscopes and is designed for **data-intensive measurements**, making it ideal for **high-precision signal analysis** and **automated waveform processing**. The software features a user-friendly GUI built with Tkinter and communicates with oscilloscopes via VISA (SCPI). Users can configure measurement processes using a drag-and-drop script editor.

## 🎯 Features

- **Automated Oscilloscope Control:** Connects to KeySight oscilloscopes via USB using VISA protocol.
- **Multi-Channel Measurement:** Supports measurements such as:
  - Peak-to-Peak Voltage (Vpp)
  - Minimum Voltage (Vmin), Maximum Voltage (Vmax)
  - Frequency & Period
  - Pulse Width & Duty Cycle
  - RMS Voltage & Average Voltage
  - Rise Time & Fall Time
  - Edge Count & Pulse Count (Positive/Negative)
  - Mean Voltage & Standard Deviation
  - Amplitude, Overshoot & Preshoot
  - Bandwidth, Bit Rate & Phase Difference
  - XMin, XMax, VTop, VBase, and VRatio
- **Waveform Visualization:** Uses Matplotlib for real-time waveform plotting.
- **Data Export & Storage:** Save measurements in JSON, CSV, Excel, and PNG formats.
- **Graphical User Interface:** Built with Tkinter for ease of use.
- **Custom Measurement Configuration:** Drag-and-drop script editor for flexible setup.
- **Support for Multiple Oscilloscope Models:** Adaptable to various KeySight oscilloscope models.

## 🌄 Home Page
![image](https://github.com/user-attachments/assets/392d5f0d-a3d0-41fe-8726-0389da0ef552)

## 🛠 Installation & Usage
### **2️⃣ Running the Software**
```bash
KeysightSoftware.exe
```

## 📚 Dependencies
This project relies on the following libraries:
- `pyvisa` - Communicates with oscilloscopes via SCPI commands
- `tkinter` - Provides the GUI interface
- `matplotlib` - For waveform visualization
- `openpyxl` - For Excel data export
- `numpy` - For numerical calculations
- `json` - For saving and loading configurations

## 🏗 Contributing
Contributions are welcome! If you find bugs or have feature suggestions, feel free to open an issue or submit a pull request.

### **Steps to Contribute:**
1. Fork the repository 🍴
2. Create a new branch 🛠
3. Make your changes and commit 📌
4. Push to your fork 🔄
5. Submit a pull request 🚀

## 📩 Contact
For any inquiries, reach out to **[cyhx2333@163.com]** or open an issue in this repository.



