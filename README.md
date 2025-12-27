# Automation with Python

This repository contains Python scripts designed to automate daily tasks and monitor system performance.

## 1. File Management (`filemng.py`)

This script automates the organization of your **Downloads** folder by moving files into appropriate directories (Music, Pictures, Videos, Documents) based on their file extensions.

### How it Works:
- **Scans** the `/home/nissan/Downloads` directory.
- **Categorizes** files based on extensions:
    - `.mp3` -> **Music**
    - `.png`, `.jpg`, `.jpeg` -> **Pictures**
    - `.mp4`, `.mov` -> **Videos**
    - `.pdf` -> **Documents**
- **Sorts by Age**:
    - Files created **less than 3 days ago** are moved to a specific `recent/` subfolder within their category (e.g., `Music/recent/`).
    - Older files are moved directly to the main category folder.
- **Handles Duplicates**: If a file with the same name exists, it renames the new file with a timestamp to prevent overwriting.

### Output:
```text
Scanning /home/nissan/Download...
Moved [song.mp3] to [/home/nissan/Music/recent]
Moved [photo.jpg] to [/home/nissan/Pictures]
File exists. Renaming to report_20241227.pdf
Moved [report.pdf] to [/home/nissan/Documents/recent]
```

---

## 2. Real-Time System Monitoring (`rltimemon.py`)

This script provides a real-time dashboard in your terminal to monitor system resources and detect suspicious activity.

### Features:
- **Resource Monitoring**: Real-time tracking of:
    - **CPU** Usage (%)
    - **RAM** Usage (Used/Total)
    - **Disk** Usage (Used/Free)
    - **Network** Speed (Upload/Download)
- **Process Analysis**:
    - Displays the **Top 3 Processes** consuming the most CPU.
    - Scans for **Suspicious Processes** (e.g., `nmap`, `hydra`, `netcat`, `wireshark`) and alerts you if they are running.
- **Storage Analysis**:
    - Background scanner that finds and displays the **Top 3 Largest Files** in your Home directory.
- **Alerts**:
    - Visual warnings for High CPU (>90%), High Memory (>90%), Low Disk Space, or Suspicious Activity.

### Usage:
Run the script in your terminal:
```bash
python3 rltimemon.py
```

### Output Screenshot:
![Real Time Monitor Output](path_to_screenshot.png)
*(Replace this with your actual screenshot)*
