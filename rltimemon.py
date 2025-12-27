import psutil
import time
import os
import threading
from datetime import datetime

# List of process names to flag as suspicious
SUSPICIOUS_TOOLS = ["nmap", "hydra", "netcat", "nc", "wireshark", "tcpdump", "john"]

# Global variable to share storage stats between thread and main loop
# Format: List of tuples (filename, size_bytes, full_path)
top_large_files = []
is_scanning = True

def get_size(bytes, suffix="B"):
    """
    Scale bytes to its proper format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    """
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor

def clear_screen():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def scan_storage_thread():
    """
    Background thread to scan for large files.
    Scanning the whole disk is too slow for real-time, so we scan the Home Directory.
    """
    global top_large_files, is_scanning
    
    # Target directory: User's Home Directory (safe and relevant)
    scan_path = os.path.expanduser("~")
    
    while True:
        is_scanning = True
        temp_files = []
        
        try:
            # Walk through the directory tree
            for root, dirs, files in os.walk(scan_path):
                # optimized: skip hidden directories to speed up
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for name in files:
                    try:
                        filepath = os.path.join(root, name)
                        # Skip if it's not a link
                        if not os.path.islink(filepath):
                            size = os.path.getsize(filepath)
                            # Optimization: Only keep if > 100MB to reduce list size in memory
                            # or just keep all and sort later. 
                            # Let's just append all, python handles lists well up to millions.
                            # But for performance let's only strictly track 'large' candidates if we had a lot.
                            # Simple approach: valid file -> add.
                            temp_files.append((name, size, filepath))
                    except (PermissionError, OSError):
                        pass
        except Exception:
            pass
            
        # Find top 3
        # Sort by size (index 1) descending
        temp_files.sort(key=lambda x: x[1], reverse=True)
        top_large_files = temp_files[:3]
        
        is_scanning = False
        
        # Wait for 60 seconds before next scan to save resources
        time.sleep(60)

def monitor_system():
    # Start the storage scanner in a background thread
    t = threading.Thread(target=scan_storage_thread, daemon=True)
    t.start()
    
    print("Starting System Monitor... (Press Ctrl+C to stop)")
    time.sleep(1)
    
    # Cache process objects
    process_cache = {}

    # Initialize Network Counters
    net_io = psutil.net_io_counters()
    prev_bytes_sent = net_io.bytes_sent
    prev_bytes_recv = net_io.bytes_recv

    try:
        while True:
            # 1. Gather System Metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Network
            net_io = psutil.net_io_counters()
            curr_bytes_sent = net_io.bytes_sent
            curr_bytes_recv = net_io.bytes_recv
            sent_speed = curr_bytes_sent - prev_bytes_sent
            recv_speed = curr_bytes_recv - prev_bytes_recv
            prev_bytes_sent = curr_bytes_sent
            prev_bytes_recv = curr_bytes_recv

            mem = psutil.virtual_memory()
            mem_used = get_size(mem.used)
            mem_total = get_size(mem.total)
            
            disk = psutil.disk_usage('/')
            disk_used = get_size(disk.used)
            disk_free = get_size(disk.free)
            
            # 2. Gather Process Metrics
            current_pids = set()
            process_infos = []
            suspicious_detected = []

            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    pid = proc.info['pid']
                    name = proc.info['name']
                    current_pids.add(pid)
                    
                    if pid not in process_cache:
                        process_cache[pid] = proc
                        try: proc.cpu_percent()
                        except: pass
                    
                    p_obj = process_cache[pid]
                    try: p_cpu = p_obj.cpu_percent()
                    except: p_cpu = 0.0
                        
                    p_info = {'pid': pid, 'name': name, 'cpu_percent': p_cpu}
                    process_infos.append(p_info)
                    
                    if name in SUSPICIOUS_TOOLS:
                        suspicious_detected.append(p_info)
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            # Clean cache
            for pid in list(process_cache.keys()):
                if pid not in current_pids:
                    del process_cache[pid]
            
            top3_processes = sorted(process_infos, key=lambda p: p['cpu_percent'], reverse=True)[:3]
            
            # 3. Generate Alerts
            alerts = []
            if suspicious_detected:
                for sp in suspicious_detected:
                    alerts.append(f"SUSPICIOUS PROCESS RUNNING: {sp['name']} (PID: {sp['pid']})")
            if cpu_usage > 90: alerts.append(f"High CPU Usage: {cpu_usage}%")
            if mem.percent > 90: alerts.append(f"High Memory Usage: {mem.percent}%")
            if disk.percent > 95: alerts.append(f"Low Disk Space: {disk_free} free")

            # 4. Display Output
            clear_screen()
            print("="*60)
            print(f"      REAL-TIME SYSTEM MONITOR  |  System: {os.name}")
            print(f"      Time: {datetime.now().strftime('%H:%M:%S')}")
            print("="*60)
            
            print(f"CPU Usage    : {cpu_usage}%")
            print(f"RAM Usage    : {mem.percent}%  (Used: {mem_used} / Total: {mem_total})")
            print(f"Disk Usage   : {disk.percent}%  (Used: {disk_used} / Free: {disk_free})")
            print(f"Network      : ↓ {get_size(recv_speed)}/s  |  ↑ {get_size(sent_speed)}/s")
            
            print("-" * 60)
            print(f"{'TOP PROCESSES (High CPU)':<35} {'PID':<10} {'CPU %'}")
            print("-" * 60)
            for p in top3_processes:
                name = p['name']
                if name and len(name) > 30: name = name[:30] + "..."
                cpu_p = p['cpu_percent']
                print(f"{name:<35} {p['pid']:<10} {cpu_p:.1f}%")

            print("\n" + "-" * 60)
            print(f"{'LARGEST FILES (In User Home)':<45} {'SIZE'}")
            print("-" * 60)
            
            if is_scanning and not top_large_files:
                print(" [Scanning disk for files... please wait] ")
            elif top_large_files:
                for fname, fsize, fpath in top_large_files:
                    # Truncate potentially long filenames
                    display_name = fname
                    if len(display_name) > 40:
                        display_name = display_name[:37] + "..."
                    print(f"{display_name:<45} {get_size(fsize)}")
            else:
                print(" [No files found or error scanning] ")

            if alerts:
                print("\n" + "!" * 60)
                print("  ALERTS & WARNINGS")
                print("!" * 60)
                for alert in alerts:
                    print(f" [!] {alert}")
            
            print("\n" + "="*60)

    except KeyboardInterrupt:
        print("\nStopping Monitor...")

if __name__ == "__main__":
    monitor_system()
