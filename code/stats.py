import psutil
import datetime
import time
import json
import subprocess
import os


## SETUP ##
script_dir = os.path.dirname(os.path.abspath(__file__))
server_dir = os.path.join(script_dir, 'servers.json')

## HELPER FUNCTIONS ##
def secs2hours(secs):
    """
    Convert seconds to hours.
    :param secs: Time input in seconds
    :return: Time formatted as HH:MM:SS
    """
    mm, ss = divmod(secs, 60)
    hh, mm = divmod(mm, 60)
    return "%d:%02d:%02d" % (hh, mm, ss)


def get_top_processes(limit: int = 5, sort_by: str = 'memory'):
    """
    Returns a list of top processes sorted by memory or CPU usage.
    :param limit: Number of top processes to return (default: 5)
    :param sort_by: Metric to sort by - 'memory'/'memory_percent' or 'cpu'/'cpu_percent'
    :return: List of dictionaries containing process info
    """
    # Normalize the sort key
    sort_by = sort_by.lower()
    if sort_by in ('memory', 'mem'):
        metric = 'memory_percent'
    elif sort_by in ('cpu',):
        metric = 'cpu_percent'
    else:
        raise ValueError("Invalid sort_by metric. Use 'memory' or 'cpu'.")

    attributes = ['pid', 'name', 'username', metric]
    processes = []

    # Pre-warm CPU percent if sorting by CPU
    if metric == 'cpu_percent':
        for proc in psutil.process_iter(attrs=['pid']):
            try:
                proc.cpu_percent(interval=None)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        # Brief pause to let CPU utilization accumulate a delta
        time.sleep(0.1)

    for proc in psutil.process_iter(attributes):
        try:
            info = proc.info
            # Fallback if metric is None
            if info.get(metric) is None:
                info[metric] = 0.0
            processes.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # Sort in descending order based on the chosen metric
    sorted_processes = sorted(
        processes,
        key=lambda p: p.get(metric) or 0.0,
        reverse=True
    )

    return sorted_processes[:limit]


def gigahertz(value: float):
    """
    Converts a value in Hertz to Gigahertz.
    :param value: Value to convert
    :return: Value as GHz (float), or 0.00 in case of an error.
    """
    value_float = float(value)
    try:
        return value_float / 1000
    except:
        return 0.00


def gigabyte(value: int):
    """
    Converts a value in bytes to GB.
    :param value: Value to convert
    :return: Value as GB (float), or 0.00 in case of an error.
    """
    value_float = float(value)
    try:
        return value_float / 1024**3
    except:
        return 0.00


def get_cpu_temperatures_dict(temp_data):
    """
    Filters psutil.sensors_temperatures() for CPU sensors.
    :param temp_data: Raw data from psutil to be input
    :return: Formatted dict with display-ready keys and string values.
    """
    cpu_identifiers = {"coretemp", "cpu", "k10temp", "zenpower"}
    cpu_labels = {"core", "package", "pkg", "cpu"}

    cpu_dict = {}

    for group_name, sensors in temp_data.items():
        group_lower = group_name.lower()
        is_cpu_group = any(identifier in group_lower for identifier in cpu_identifiers)

        for sensor in sensors:
            label_lower = sensor.label.lower() if sensor.label else ""

            if is_cpu_group or any(lbl in label_lower for lbl in cpu_labels):
                label = sensor.label if sensor.label else group_name

                # Format the key and value specifically for display
                key_str = f"CPU Sensor [{label}]"
                val_str = f"{sensor.current}°C"

                cpu_dict[key_str] = val_str

    return cpu_dict


def get_cpu_fans_dict(fan_data):
    """
    Filters psutil.sensors_fans() for CPU fan sensors.
    :param fan_data: Raw data from psutil.sensors_fans() to be input
    :return: Formatted dict with display-ready keys and string values.
    """
    cpu_identifiers = {"cpu", "processor"}
    cpu_labels = {"cpu", "processor", "cpufans", "cpu_fan"}

    cpu_dict = {}

    if not fan_data:
        return cpu_dict

    for group_name, fans in fan_data.items():
        group_lower = group_name.lower()
        is_cpu_group = any(identifier in group_lower for identifier in cpu_identifiers)

        for fan in fans:
            label_lower = fan.label.lower() if fan.label else ""

            if is_cpu_group or any(lbl in label_lower for lbl in cpu_labels):
                label = fan.label if fan.label else group_name

                key_str = f"CPU Fan [{label}]"
                val_str = f"{fan.current} RPM"

                cpu_dict[key_str] = val_str

    return cpu_dict




def get_minecraft_stats(session_name: str, data: dict):
    """
    Checks if a tmux session is active and collects resource usage of associated Java processes.
    :param session_name: Name of the tmux session (e.g., 'mc1')
    :return: Dictionary containing running status, RAM in GB, CPU usage, and status display as formatted strings.
    """
    is_running = False
    try:
        result = subprocess.run(["tmux", "has-session", "-t", session_name], capture_output=True)
        is_running = (result.returncode == 0)
    except Exception:
        is_running = False

    ram_usage_gb = 0.0
    cpu_percent = 0.0

    # Map session names to their exact jar file signatures from process list
    target_keyword = "server.jar" if session_name == data.get("mc1") else "fabric-server-launch.jar"

    if is_running:
        for proc in psutil.process_iter(['name', 'cmdline', 'memory_info']):
            try:
                if proc.info['name'] and 'java' in proc.info['name'].lower():
                    cmdline = " ".join(proc.info['cmdline'] or [])
                    if target_keyword in cmdline:
                        if proc.info['memory_info']:
                            # Convert bytes to GB
                            ram_usage_gb += proc.info['memory_info'].rss / (1024 * 1024 * 1024)
                        cpu_percent += proc.cpu_percent(interval=None)
                        pid = proc.pid
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

    # Format all four data points as strings
    running_f = "ONLINE" if is_running else "OFFLINE"
    ram_gb_f = f"{round(ram_usage_gb, 2)} GB"
    cpu_f = f"{round(cpu_percent, 1)}%"
    status_display_f = f"{running_f} ({ram_gb_f})"
    pid_f = f"PID: {pid}"

    return {
        "running_f": running_f,
        "ram_gb_f": ram_gb_f,
        "cpu_percent_f": cpu_f,
        "status_display_f": status_display_f,
        "pid_f": pid_f
    }


## MAIN LOOP ##

def get_system_stats():
    ## FETCH DATA ##
    cpu = psutil.cpu_percent(interval=1, percpu=True)
    freq = psutil.cpu_freq(percpu=True)
    load = [x / psutil.cpu_count() * 100 for x in psutil.getloadavg()]
    memory = psutil.virtual_memory()
    disc = psutil.disk_usage('/')
    disc_usage = psutil.disk_io_counters()
    network = psutil.net_io_counters()

    if hasattr(psutil, "sensors_temperatures"):
        temps = psutil.sensors_temperatures()
    else:
        temps = None

    if hasattr(psutil, "sensors_fans"):
        fans = psutil.sensors_fans()
    else:
        fans = None

    battery = psutil.sensors_battery()

    boot_time = psutil.boot_time()
    uptime_secs = time.time() - boot_time
    hours = int(uptime_secs // 3600)
    mins = int((uptime_secs % 3600) // 60)
    uptime_f = f"{hours} hours, {mins} minutes"

    ## FORMAT DATA ##
    cpu_f = ""
    for n in range(len(cpu) - 1):
        cpu_f += f"{n}: {cpu[n]}% | "

    if freq and len(freq) > 0:
        current_freq_f = f"Current: {gigahertz(freq[0].current)} GHz"
        min_freq_f = f"Min: {gigahertz(freq[0].min)} GHz"
        max_freq_f = f"Max: {gigahertz(freq[0].max)} GHz"
    else:
        current_freq_f = "Current: N/A"
        min_freq_f = "Min: N/A"
        max_freq_f = "Max: N/A"

    if load and len(load) > 0:
        one_load_f = f"{round(load[0], 2)}%"
        five_load_f = f"{round(load[1], 2)}%"
        fifteen_load_f = f"{round(load[2], 2)}%"
    else:
        one_load_f = "N/A"
        five_load_f = "N/A"
        fifteen_load_f = "N/A"

    if memory and len(memory) > 0:
        mem_f = f"{round(gigabyte(memory.used), 2)} GB / {round(gigabyte(memory.total), 2)} GB ({memory.percent}%)"
        free_mem_f = f"{round(gigabyte(memory.available), 2)} GB"
    else:
        mem_f = "N/A"
        free_mem_f = "N/A"

    if disc and len(disc) > 0:
        disc_f = f"{round(gigabyte(disc.used), 2)} GB / {round(gigabyte(disc.total), 2)} GB ({disc.percent}%)"
        free_disc_f = f"{round(gigabyte(disc.free), 2)} GB"
    else:
        disc_f = "N/A"
        free_disc_f = "N/A"

    if disc_usage and len(disc_usage) > 0:
        disc_ops_f = f"Read: {disc_usage.read_count} ops | Write: {disc_usage.write_count} ops"
        disc_bytes_f = f"Read: {disc_usage.read_bytes} bytes | Write: {disc_usage.write_bytes} bytes"
        disc_gb_f = f"Read: {round(gigabyte(disc_usage.read_bytes), 2)} GB | Write: {round(gigabyte(disc_usage.write_bytes), 2)} GB"
        disc_times_f = f"Read: {round(disc_usage.read_time / 1000, 2)} secs | Write: {round(disc_usage.write_time / 1000, 2)} secs"
    else:
        disc_ops_f = "N/A"
        disc_bytes_f = "N/A"
        disc_gb_f = "N/A"
        disc_times_f = "N/A"

    if network and len(network) > 0:
        network_gb_f = f"Sent: {round(gigabyte(network.bytes_sent), 2)} GB | Received: {round(gigabyte(network.bytes_recv), 2)} GB"
        network_packets_f = f"Sent: {network.packets_sent} packets | Received: {network.packets_recv} packets"
    else:
        network_gb_f = "N/A"
        network_packets_f = "N/A"

    if hasattr(psutil, "sensors_temperatures") and temps:
        cpu_temps_f = get_cpu_temperatures_dict(temps)
    else:
        cpu_temps_f = 'No Temperatures Detected'

    if hasattr(psutil, "sensors_fans") and fans:
        fans_f = get_cpu_fans_dict(fans)
    else:
        fans_f = 'No Fans Detected'

    try:
        battery_secs = battery.secsleft
        b_hours = int(battery_secs // 3600)
        b_mins = int((battery_secs % 3600) // 60)
        battery_f = f"{round(battery.percent, 2)}% ({b_hours}h {b_mins}m left)"
    except:
        battery_f = 'No Battery Detected'

    with open(server_dir, 'r') as json_file:
        server_names = json.load(json_file)
    # Minecraft Server Objects
    mc1 = get_minecraft_stats(server_names.get("mc1"), server_names)
    mc2 = get_minecraft_stats(server_names.get("mc2"), server_names)

    ## WRITE TO JSON ##
    json_dump = {
        "cpu_f": cpu_f,
        "current_freq_f": current_freq_f,
        "min_freq_f": min_freq_f,
        "max_freq_f": max_freq_f,
        "one_load_f": one_load_f,
        "five_load_f": five_load_f,
        "fifteen_load_f": fifteen_load_f,
        "mem_f": mem_f,
        "free_mem_f": free_mem_f,
        "disc_f": disc_f,
        "free_disc_f": free_disc_f,
        "disc_ops_f": disc_ops_f,
        "disc_bytes_f": disc_bytes_f,
        "disc_gb_f": disc_gb_f,
        "disc_times_f": disc_times_f,
        "network_gb_f": network_gb_f,
        "network_packets_f": network_packets_f,
        "cpu_temps_f": cpu_temps_f,
        "battery_f": battery_f,
        "fans_f": fans_f,
        "uptime_f": uptime_f,
        "mc1": mc1,
        "mc2": mc2
    }

    print(json_dump)
    dump = json.dumps(json_dump)
    os.makedirs("data", exist_ok=True)
    with open("data/data.json", 'w') as file:
        file.write(dump)

    return True


if __name__ == '__main__':
    get_system_stats()