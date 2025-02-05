# KeySight Oscilloscope Automation Software

## 📌 Project Overview
KeySight Oscilloscope Automation Software is a Python-based automation tool for controlling, acquiring, analyzing, and storing waveform data from KeySight oscilloscopes. It features a user-friendly GUI built with Tkinter and communicates with oscilloscopes via VISA (SCPI). The software supports multi-channel measurements and allows users to configure measurement processes using a drag-and-drop script editor.

## 🎯 Features
- **Automated Oscilloscope Control:** Connects to KeySight oscilloscopes via VISA protocol.
- **Multi-Channel Measurement:** Supports measurements like Vpp, Frequency, Duty Cycle, RMS Voltage, and more.
- **Waveform Visualization:** Uses Matplotlib for real-time waveform plotting.
- **Data Export & Storage:** Save measurements in JSON, CSV, Excel, and PNG formats.
- **Graphical User Interface:** Built with Tkinter for ease of use.
- **Custom Measurement Configuration:** Drag-and-drop script editor for flexible setup.
- **Support for Multiple Oscilloscope Models:** Adaptable to various KeySight oscilloscope models.

## 🛠 Installation & Usage
### **1️⃣ Prerequisites**
Make sure you have Python installed (Python 3.7+ recommended). Also, install the required dependencies:
```bash
pip install -r requirements.txt
```

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

## 📜 License
This project is licensed under the MIT License.

## 📩 Contact
For any inquiries, reach out to **[Your Email]** or open an issue in this repository.



