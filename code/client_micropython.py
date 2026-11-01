import time
import network
import poll

# --- READ WIFI CREDENTIALS FROM FILES ---
try:
    with open('wifi_ssid.txt', 'r') as file:
        WIFI_SSID = file.read().strip()
    with open('wifi_password.txt', 'r') as file:
        WIFI_PASSWORD = file.read().strip()
except OSError:
    print("WARNING: wifi_ssid.txt or wifi_password.txt not found! Wi-Fi will fail to connect.")
    WIFI_SSID = ""
    WIFI_PASSWORD = ""


def connect_wifi():
    """Connects the Pico W to Wi-Fi using credentials from files."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print(f"Connecting to Wi-Fi '{WIFI_SSID}'...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)

        # Wait up to 15 seconds for connection
        timeout = 15
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            print(".", end="")
            timeout -= 1

    if wlan.isconnected():
        print("\nWi-Fi Connected successfully!")
        print("Network config:", wlan.ifconfig())
        return True
    else:
        print("\nFailed to connect to Wi-Fi.")
        return False


## SETUP ##
POLL_INTERVAL = 300  # 5 minutes
HEADINGS = [
    "CPU (1)",
    "CPU (2)",
    "Memory, Disc & Uptime",
    "Disc",
    "Network",
    "Temps & Battery",
    "Minecraft Server 1",
    "Minecraft Server 2"
]

# Simple text wrapper fallback if wraptext module is missing
try:
    import wraptext
except ImportError:
    class wraptext:
        @staticmethod
        def wrap(text, width):
            if text is None:
                return "".ljust(width)
            text_str = str(text)
            if len(text_str) > width:
                return text_str[:width]
            return text_str.ljust(width)


## HELPER FUNCTIONS ##
def parse_data(data: dict, page: int):
    """
    Parses incoming data into an array with fully formatted data for a given page.
    :param data: Dictionary of data to parse.
    :param page: Page number.
    :return: Array of data for given page.
    """
    if not data:
        return ["No data available"]

    if page == 0:
        # CPU Page 1
        page_data = []
        page_data.append(data.get("cpu_f"))
        page_data.append(data.get("cpu_temps_f"))
        page_data.append(data.get("current_freq_f"))

    elif page == 1:
        # CPU Page 2
        page_data = []
        page_data.append(data.get("min_freq_f"))
        page_data.append(data.get("max_freq_f"))
        page_data.append(f"Last min: {data.get('one_load_f')}")
        page_data.append(f"Last 5 mins: {data.get('five_load_f')}")
        page_data.append(f"Last 15 mins: {data.get('fifteen_load_f')}")

    elif page == 2:
        # Memory, disc usage and uptime
        page_data = []
        page_data.append(data.get("mem_f"))
        page_data.append(f"Free: {data.get('free_mem_f')}")
        page_data.append(f"Disc: {data.get('disc_f')}")
        page_data.append(f"Free: {data.get('free_disc_f')}")
        page_data.append(f"Uptime: {data.get('uptime_f')}")

    elif page == 3:
        # Disc
        page_data = []
        page_data.append(data.get("disc_ops_f"))
        page_data.append(data.get("disc_gb_f"))
        page_data.append(data.get("disc_times_f"))

    elif page == 4:
        # Network
        page_data = []
        page_data.append(data.get("network_gb_f"))
        page_data.append(data.get("network_packets_f"))

    elif page == 5:
        # Temps & Battery
        page_data = []
        page_data.append(f"CPU Usage: {data.get('one_load_f')}")
        page_data.append(data.get("cpu_temps_f"))
        page_data.append(data.get("fans_f"))
        page_data.append(f"Battery: {data.get('battery_f')}")

    elif page == 6:
        # Minecraft Server 1
        page_data = []
        mc_data = data.get("mc1") or {}
        page_data.append(f"Status: {mc_data.get('running_f')}")
        page_data.append(f"RAM Usage: {mc_data.get('ram_gb_f')}")
        page_data.append(f"CPU Usage: {mc_data.get('cpu_percent_f')}")
        page_data.append(mc_data.get("status_display_f"))
        page_data.append(mc_data.get("pid_f"))

    elif page == 7:
        # Minecraft Server 2
        page_data = []
        mc_data = data.get("mc2") or {}
        page_data.append(f"Status: {mc_data.get('running_f')}")
        page_data.append(f"RAM Usage: {mc_data.get('ram_gb_f')}")
        page_data.append(f"CPU Usage: {mc_data.get('cpu_percent_f')}")
        page_data.append(mc_data.get("status_display_f"))
        page_data.append(mc_data.get("pid_f"))

    else:
        page_data = ["Invalid page"]

    return page_data


class MacDisplaySimulator:
    """Simulates an e-paper screen in Mac terminal."""

    def __init__(self, width=30):
        self.width = width

    def clear(self):
        print("\n" * 2)

    def render_page(self, heading, lines):
        self.clear()
        self.heading = str(heading)
        print("┌" + "─" * self.width + "┐")
        total_padding = self.width - len(self.heading)
        left_pad = total_padding // 2
        right_pad = total_padding - left_pad
        centered_heading = ((" " * left_pad) + f"\033[4m{self.heading}\033[0m" + (" " * right_pad))
        print(centered_heading)

        for line in lines:
            wrapped = wraptext.wrap(str(line) if line is not None else "", self.width)
            print(wrapped)
        print("└" + "─" * self.width + "┘")


def render(data, index, display):
    page = parse_data(data, index)
    display.render_page(HEADINGS[index], page)


## MAIN LOOP ##
def main():
    # Connect to Wi-Fi first
    if not connect_wifi():
        print("Retrying Wi-Fi in 10 seconds...")
        time.sleep(10)
        return

    display = MacDisplaySimulator(40)
    index = 0

    while True:
        try:
            print("\n--- Polling Server ---")
            data = poll.fetch_data()  # Fetches JSON dict from server

            if data:
                display.clear()
                render(data, index, display)
                print("Data fetched and processed successfully.")
            else:
                print("Received empty data dictionary.")

        except Exception as e:
            print(f"Polling failed: {e}")

        if False:  # PLACEHOLDER BUTTON PRESS
            index = (index + 1) % len(HEADINGS)
            display.clear()
            render(data, index, display)

        # Wait for 5 minutes before the next poll
        print(f"Waiting {POLL_INTERVAL // 60} minutes until next update...")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()