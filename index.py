
# SMART SYSTEM MONITOR (SSM)
# - Fixed Alignment
# - Real System Controls
# - Functional Junk Cleaner
# - Network Speed Display (KB/s or MB/s)


import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
import psutil
import time
import threading
from datetime import datetime
import tkinter as tk
import os
import shutil
import subprocess
from pathlib import Path
import tempfile


# MAIN APPLICATION WINDOW

class SmartSystemMonitor(ttk.Window):
    def __init__(self):
        super().__init__(themename="darkly")
        self.title("Smart System Monitor")
        self.geometry("900x560")
        self.resizable(False, False)
        self.configure(bg="#1e1e2e")

        header = ttk.Frame(self)
        header.pack(fill=X, pady=(12, 0))
        ttk.Label(
            header,
            text="Smart System Monitor",
            font=("Segoe UI Semibold", 18),
            bootstyle="inverse-dark",
        ).pack(side=LEFT, padx=20)

        content = ttk.Frame(self)
        content.pack(fill=BOTH, expand=True, padx=20, pady=12)

        # Top meters
        self.meter_frame = MeterFrame(content)
        self.meter_frame.pack(fill=X, pady=(0, 14))

        # Middle system info
        self.info_frame = SystemInfoFrame(content)
        self.info_frame.pack(fill=X, pady=(0, 14))

        # Bottom cleaner + controls
        bottom_row = ttk.Frame(content)
        bottom_row.pack(fill=X)
        bottom_row.columnconfigure(0, weight=1)
        bottom_row.columnconfigure(1, weight=1)

        self.cleaner_frame = SystemCleanerFrame(bottom_row)
        self.cleaner_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.controls_frame = SystemControlsFrame(bottom_row)
        self.controls_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        # Start background updates
        self.monitor = SystemMonitor(self)
        self.monitor.start()


# METER FRAME (Top Row)

class MeterFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bootstyle="dark")
        self.configure(padding=(10, 8))

        container = ttk.Frame(self)
        container.pack(fill=X)
        for col in range(4):
            container.columnconfigure(col, weight=1, uniform="m")

        # CPU Meter
        self.cpu_meter = ttk.Meter(
            container,
            metersize=150,
            amountused=0,
            amounttotal=100,
            subtext="CPU Usage",
            bootstyle="success",
        )
        self.cpu_meter.grid(row=0, column=0, padx=10, sticky="n")

        # RAM Meter
        self.ram_meter = ttk.Meter(
            container,
            metersize=150,
            amountused=0,
            amounttotal=100,
            subtext="RAM Usage",
            bootstyle="warning",
        )
        self.ram_meter.grid(row=0, column=1, padx=10, sticky="n")

        # Network Sent
        self.net_sent_meter = ttk.Meter(
            container,
            metersize=150,
            amountused=0,
            amounttotal=100,
            subtext="Upload Speed",
            bootstyle="info",
        )
        self.net_sent_meter.grid(row=0, column=2, padx=10, sticky="n")

        # Network Received
        self.net_recv_meter = ttk.Meter(
            container,
            metersize=150,
            amountused=0,
            amounttotal=100,
            subtext="Download Speed",
            bootstyle="primary",
        )
        self.net_recv_meter.grid(row=0, column=3, padx=10, sticky="n")

        # Speed Labels (below meters)
        self.net_sent_label = ttk.Label(container, text="Sent: 0 KB/s", font=("Segoe UI", 10))
        self.net_recv_label = ttk.Label(container, text="Recv: 0 KB/s", font=("Segoe UI", 10))
        self.net_sent_label.grid(row=1, column=2, pady=(8, 0))
        self.net_recv_label.grid(row=1, column=3, pady=(8, 0))



# SYSTEM INFO FRAME (Middle)

class SystemInfoFrame(ttk.Labelframe):
    def __init__(self, parent):
        super().__init__(parent, text="System Info", bootstyle="dark")
        self.configure(padding=12)

        container = ttk.Frame(self)
        container.pack(fill=X)
        for c in range(3):
            container.columnconfigure(c, weight=1, uniform="info")

        self.battery_label = ttk.Label(container, text="Battery: --", font=("Segoe UI", 11))
        self.battery_label.grid(row=0, column=0, sticky="w", padx=10)

        self.charger_label = ttk.Label(container, text="Charger: --", font=("Segoe UI", 11))
        self.charger_label.grid(row=0, column=1, sticky="w", padx=10)

        self.uptime_label = ttk.Label(container, text="Uptime: --", font=("Segoe UI", 11))
        self.uptime_label.grid(row=0, column=2, sticky="w", padx=10)



# SYSTEM CLEANER FRAME

class SystemCleanerFrame(ttk.Labelframe):
    def __init__(self, parent):
        super().__init__(parent, text="System Cleaner", bootstyle="dark")
        self.configure(padding=12)

        self.info_label = ttk.Label(
            self, text="Ready to clean junk files", font=("Segoe UI", 10)
        )
        self.info_label.pack(anchor="w", pady=(4, 6))

        row = ttk.Frame(self)
        row.pack(fill=X, pady=(8, 4))

        self.progress = ttk.Progressbar(row, orient=HORIZONTAL, length=260, mode="determinate")
        self.progress.pack(side=LEFT, padx=(0, 10))

        self.clean_btn = ttk.Button(
            row, text="Clean Junk", bootstyle="success-outline", command=self.clean
        )
        self.clean_btn.pack(side=LEFT)

    def clean(self):
        self.clean_btn.state(["disabled"])
        self.progress["value"] = 0

        def worker():
            temp_dir = Path(tempfile.gettempdir())
            files = list(temp_dir.glob("*"))
            total = len(files)
            deleted = 0
            for i, f in enumerate(files, 1):
                try:
                    if f.is_file():
                        f.unlink()
                        deleted += 1
                    elif f.is_dir():
                        shutil.rmtree(f, ignore_errors=True)
                        deleted += 1
                except Exception:
                    continue
                self.progress["value"] = (i / total) * 100
                time.sleep(0.005)
            self.after(0, lambda: self.finish_clean(deleted))

        threading.Thread(target=worker, daemon=True).start()

    def finish_clean(self, deleted):
        self.clean_btn.state(["!disabled"])
        self.progress["value"] = 100
        Messagebox.show_info("System Cleaner", f"Cleaned {deleted} junk items successfully!")



# SYSTEM CONTROLS FRAME

class SystemControlsFrame(ttk.Labelframe):
    def __init__(self, parent):
        super().__init__(parent, text="System Controls", bootstyle="dark")
        self.configure(padding=12)

        btn_row = ttk.Frame(self)
        btn_row.pack(pady=6)

        ttk.Button(
            btn_row, text="Shutdown", bootstyle="danger-outline", command=self.shutdown
        ).pack(side=LEFT, padx=10)

        ttk.Button(
            btn_row, text="Restart", bootstyle="warning-outline", command=self.restart
        ).pack(side=LEFT, padx=10)

        ttk.Button(
            btn_row, text="Sleep", bootstyle="info-outline", command=self.sleep
        ).pack(side=LEFT, padx=10)

    def shutdown(self):
        subprocess.run("shutdown /s /t 1", shell=True)

    def restart(self):
        subprocess.run("shutdown /r /t 1", shell=True)

    def sleep(self):
        subprocess.run("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)



# SYSTEM MONITOR THREAD

class SystemMonitor(threading.Thread):
    def __init__(self, app):
        super().__init__(daemon=True)
        self.app = app
        self.boot_time = datetime.fromtimestamp(psutil.boot_time())
        self.prev_net = psutil.net_io_counters()
        self.prev_time = time.time()

    def run(self):
        while True:
            try:
                cpu = psutil.cpu_percent(interval=None)
                ram = psutil.virtual_memory().percent

                now = time.time()
                net_io = psutil.net_io_counters()
                delta_t = now - self.prev_time if now - self.prev_time > 0 else 1
                sent_kb_s = (net_io.bytes_sent - self.prev_net.bytes_sent) / 1024.0 / delta_t
                recv_kb_s = (net_io.bytes_recv - self.prev_net.bytes_recv) / 1024.0 / delta_t
                self.prev_net = net_io
                self.prev_time = now

                # Convert to MB/s if large
                def format_speed(speed):
                    return f"{speed/1024:.2f} MB/s" if speed > 1024 else f"{speed:.1f} KB/s"

                # Battery
                battery = psutil.sensors_battery()
                if battery:
                    batt_text = f"Battery: {battery.percent}%"
                    charge_status = "Charging" if battery.power_plugged else "Not Charging"
                else:
                    batt_text = "Battery: N/A"
                    charge_status = "N/A"

                # Uptime
                uptime = datetime.now() - self.boot_time
                uptime_text = f"Uptime: {uptime.seconds // 3600}h {(uptime.seconds // 60) % 60}m"

                # Update meters
                self.app.meter_frame.cpu_meter.configure(amountused=cpu)
                self.app.meter_frame.ram_meter.configure(amountused=ram)

                sent_display = min(int(sent_kb_s / 10), 100)
                recv_display = min(int(recv_kb_s / 10), 100)
                self.app.meter_frame.net_sent_meter.configure(amountused=sent_display)
                self.app.meter_frame.net_recv_meter.configure(amountused=recv_display)

                # Update speed labels
                self.app.meter_frame.net_sent_label.configure(text=f"Sent: {format_speed(sent_kb_s)}")
                self.app.meter_frame.net_recv_label.configure(text=f"Recv: {format_speed(recv_kb_s)}")

                # System Info
                self.app.info_frame.battery_label.configure(text=batt_text)
                self.app.info_frame.charger_label.configure(text=f"Charger: {charge_status}")
                self.app.info_frame.uptime_label.configure(text=uptime_text)

                time.sleep(1)

            except Exception:
                time.sleep(1)
                continue



# RUN APPLICATION

if __name__ == "__main__":
    app = SmartSystemMonitor()
    app.mainloop()
