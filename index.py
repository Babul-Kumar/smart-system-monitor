import tkinter as tk
from tkinter import messagebox
import psutil
import win32com.client
import os
import shutil
import threading
import time
from datetime import datetime
import pystray
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
import numpy as np

class SmartSystemMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart System Monitor (SSM)")
        self.root.geometry("600x900")  # Increased height for four graphs
        self.root.resizable(False, False)

        # Labels for displaying system stats
        self.label_charger = tk.Label(root, text="Charger Status: Checking...", font=("Arial", 12))
        self.label_charger.pack(pady=10)

        self.label_cpu = tk.Label(root, text="CPU Usage: 0%", font=("Arial", 12))
        self.label_cpu.pack(pady=5)

        self.label_ram = tk.Label(root, text="RAM Usage: 0%", font=("Arial", 12))
        self.label_ram.pack(pady=5)

        self.label_network_sent = tk.Label(root, text="Network Sent: 0 KB/s", font=("Arial", 12))
        self.label_network_sent.pack(pady=5)

        self.label_network_recv = tk.Label(root, text="Network Received: 0 KB/s", font=("Arial", 12))
        self.label_network_recv.pack(pady=5)

        self.label_cleaner = tk.Label(root, text="Junk Cleaner Ready", font=("Arial", 12))
        self.label_cleaner.pack(pady=10)

        # Clean Junk Button
        self.clean_button = tk.Button(root, text="Clean Junk Files", command=self.clean_junk_files, font=("Arial", 12))
        self.clean_button.pack(pady=10)

        # Setup four separate graphs
        self.fig, (self.ax1, self.ax2, self.ax3, self.ax4) = plt.subplots(4, 1, figsize=(5, 6), sharex=True)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(pady=10)
        self.times = []
        self.cpu_data = []
        self.ram_data = []
        self.net_sent_data = []
        self.net_recv_data = []
        self.max_points = 60  # Show last 60 seconds

        # System Tray Setup
        self.icon = self.create_system_tray_icon()
        self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

        # Start monitoring and logging threads
        self.running = True
        self.monitor_thread = threading.Thread(target=self.update_stats)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

        self.logging_thread = threading.Thread(target=self.log_stats)
        self.logging_thread.daemon = True
        self.logging_thread.start()

        # Start graph animation
        self.ani = animation.FuncAnimation(self.fig, self.update_graph, interval=1000)

    def create_system_tray_icon(self):
        image = Image.new('RGB', (64, 64), color='white')
        icon = pystray.Icon("SSM")
        icon.icon = image
        icon.title = "Smart System Monitor"
        icon.menu = pystray.Menu(
            pystray.MenuItem("Show", self.restore_from_tray),
            pystray.MenuItem("Exit", self.stop)
        )
        threading.Thread(target=icon.run, daemon=True).start()
        return icon

    def minimize_to_tray(self):
        self.root.withdraw()
        self.icon.notify("Smart System Monitor minimized to tray", "SSM")

    def restore_from_tray(self):
        self.root.deiconify()
        self.icon.remove_notification()

    def get_charger_status(self):
        try:
            wmi = win32com.client.GetObject("winmgmts:")
            batteries = wmi.InstancesOf("Win32_Battery")
            for battery in batteries:
                status = battery.BatteryStatus
                if status == 2:
                    return "Charging"
                elif status == 1:
                    return "On Battery"
                else:
                    return "Unknown"
        except Exception as e:
            return f"Error: {str(e)}"

    def get_cpu_usage(self):
        return psutil.cpu_percent(interval=1)

    def get_ram_usage(self):
        memory = psutil.virtual_memory()
        return memory.percent

    def get_network_usage(self):
        net_io = psutil.net_io_counters()
        return net_io.bytes_sent, net_io.bytes_recv

    def update_stats(self):
        prev_sent, prev_recv = self.get_network_usage()
        prev_time = time.time()

        while self.running:
            # Charger Status
            charger_status = self.get_charger_status()
            self.label_charger.config(text=f"Charger Status: {charger_status}")

            # CPU Usage
            cpu_usage = self.get_cpu_usage()
            self.label_cpu.config(text=f"CPU Usage: {cpu_usage:.1f}%")

            # RAM Usage
            ram_usage = self.get_ram_usage()
            self.label_ram.config(text=f"RAM Usage: {ram_usage:.1f}%")

            # Network Usage
            curr_sent, curr_recv = self.get_network_usage()
            curr_time = time.time()
            delta_time = curr_time - prev_time
            sent_speed = (curr_sent - prev_sent) / delta_time / 1024  # KB/s
            recv_speed = (curr_recv - prev_recv) / delta_time / 1024  # KB/s
            self.label_network_sent.config(text=f"Network Sent: {sent_speed:.2f} KB/s")
            self.label_network_recv.config(text=f"Network Received: {recv_speed:.2f} KB/s")

            # Update graph data
            self.times.append(time.time())
            self.cpu_data.append(cpu_usage)
            self.ram_data.append(ram_usage)
            self.net_sent_data.append(sent_speed)
            self.net_recv_data.append(recv_speed)

            # Trim data to last 60 points
            if len(self.times) > self.max_points:
                self.times.pop(0)
                self.cpu_data.pop(0)
                self.ram_data.pop(0)
                self.net_sent_data.pop(0)
                self.net_recv_data.pop(0)

            prev_sent, prev_recv = curr_sent, curr_recv
            prev_time = curr_time

            time.sleep(1)

    def update_graph(self, frame):
        # Clear all subplots
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self.ax4.clear()

        times = np.array(self.times) - self.times[0] if self.times else np.array([])

        # Plot CPU Usage
        self.ax1.plot(times, self.cpu_data, label="CPU (%)", color="#1f77b4", linewidth=2, alpha=0.8)
        self.ax1.set_ylim(0, 100)
        self.ax1.set_ylabel("CPU (%)", color="#1f77b4")
        self.ax1.tick_params(axis='y', labelcolor="#1f77b4")
        self.ax1.grid(True, linestyle="--", alpha=0.7)

        # Plot RAM Usage
        self.ax2.plot(times, self.ram_data, label="RAM (%)", color="#ff7f0e", linewidth=2, alpha=0.8)
        self.ax2.set_ylim(0, 100)
        self.ax2.set_ylabel("RAM (%)", color="#ff7f0e")
        self.ax2.tick_params(axis='y', labelcolor="#ff7f0e")
        self.ax2.grid(True, linestyle="--", alpha=0.7)

        # Plot Network Sent
        self.ax3.plot(times, self.net_sent_data, label="Net Sent (KB/s)", color="#2ca02c", linewidth=2, alpha=0.8)
        if self.net_sent_data:
            max_sent = max(self.net_sent_data)
            self.ax3.set_ylim(0, max(max_sent * 1.1, 1))  # Dynamic range with padding
        else:
            self.ax3.set_ylim(0, 1)
        self.ax3.set_ylabel("Net Sent (KB/s)", color="#2ca02c")
        self.ax3.tick_params(axis='y', labelcolor="#2ca02c")
        self.ax3.grid(True, linestyle="--", alpha=0.7)

        # Plot Network Received
        self.ax4.plot(times, self.net_recv_data, label="Net Recv (KB/s)", color="#d62728", linewidth=2, alpha=0.8)
        if self.net_recv_data:
            max_recv = max(self.net_recv_data)
            self.ax4.set_ylim(0, max(max_recv * 1.1, 1))  # Dynamic range with padding
        else:
            self.ax4.set_ylim(0, 1)
        self.ax4.set_ylabel("Net Recv (KB/s)", color="#d62728")
        self.ax4.tick_params(axis='y', labelcolor="#d62728")
        self.ax4.grid(True, linestyle="--", alpha=0.7)
        self.ax4.set_xlabel("Time (s)")

        # Set title and adjust layout
        self.fig.suptitle("System Usage Over Time", fontsize=12)
        self.fig.tight_layout(rect=[0, 0, 1, 0.95])  # Adjust for suptitle
        self.canvas.draw()

    def log_stats(self):
        log_file = "system_monitor_log.txt"
        while self.running:
            try:
                cpu_usage = self.get_cpu_usage()
                ram_usage = self.get_ram_usage()
                sent, recv = self.get_network_usage()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_entry = f"{timestamp}, CPU: {cpu_usage:.1f}%, RAM: {ram_usage:.1f}%, Sent: {sent / 1024:.2f} KB, Recv: {recv / 1024:.2f} KB\n"
                with open(log_file, "a") as f:
                    f.write(log_entry)
            except Exception as e:
                print(f"Logging error: {str(e)}")
            time.sleep(60)

    def clean_junk_files(self):
        self.clean_button.config(state="disabled")
        self.label_cleaner.config(text="Scanning for junk files...")
        self.root.update()

        junk_paths = [
            os.path.expandvars(r"%temp%"),
            os.path.expandvars(r"C:\Windows\Temp"),
            os.path.expandvars(r"C:\$Recycle.Bin")
        ]

        total_size = 0
        files_to_delete = []

        for path in junk_paths:
            try:
                for root, dirs, files in os.walk(path, topdown=True):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            file_size = os.path.getsize(file_path)
                            total_size += file_size
                            files_to_delete.append(file_path)
                        except (OSError, PermissionError):
                            continue
            except (OSError, PermissionError):
                continue

        total_size_mb = total_size / (1024 * 1024)
        if total_size_mb > 0:
            confirm = messagebox.askyesno(
                "Confirm Deletion",
                f"Found {len(files_to_delete)} junk files ({total_size_mb:.2f} MB). Delete them?"
            )
            if confirm:
                deleted_size = 0
                for file_path in files_to_delete:
                    try:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        deleted_size += file_size
                    except (OSError, PermissionError):
                        continue
                deleted_size_mb = deleted_size / (1024 * 1024)
                self.label_cleaner.config(text=f"Deleted {deleted_size_mb:.2f} MB of junk files")
                messagebox.showinfo("Success", f"Cleaned {deleted_size_mb:.2f} MB of junk files")
            else:
                self.label_cleaner.config(text="Junk cleaning cancelled")
        else:
            self.label_cleaner.config(text="No junk files found")
            messagebox.showinfo("Info", "No junk files found")

        self.clean_button.config(state="normal")

    def stop(self):
        self.running = False
        self.icon.stop()
        plt.close(self.fig)
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SmartSystemMonitor(root)
    root.mainloop()