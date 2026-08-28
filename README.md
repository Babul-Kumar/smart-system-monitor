# Smart System Monitor

A lightweight desktop system monitor built with Python, Tkinter, ttkbootstrap, and psutil.

## Features

- Live CPU and RAM usage meters
- Upload and download speed display in KB/s or MB/s
- Battery percentage and charger status
- System uptime display
- Temporary-file cleanup with progress feedback
- Shutdown, restart, and sleep controls
- Dark-themed fixed-size desktop interface

## Requirements

- Python 3.9 or newer
- Tkinter
- `psutil`
- `ttkbootstrap`

On Debian or Ubuntu, install Tkinter with:

```bash
sudo apt install python3-tk
```

Install the Python packages with:

```bash
python -m pip install psutil ttkbootstrap
```

## Run

From the project directory, start the application with:

```bash
python index.py
```

## Notes

- The power-control buttons currently use Windows commands (`shutdown` and `rundll32.exe`). They will not work as written on Linux or macOS.
- The cleaner removes files and directories from the operating system's temporary directory. Review this behavior before using it on important systems.
- Battery information may show `N/A` on desktops or systems where battery sensors are unavailable.

## Project Files

- `index.py` - application source code
- `system_monitor_log.txt` - reserved log file
- `CNAME` - custom domain configuration for GitHub Pages
