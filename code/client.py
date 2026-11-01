import time
import poll
import wraptext

## SETUP ##
POLL_INTERVAL = 300 # 5 minutes
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

## HELPER FUNCTIONS ##
def parse_data(data: dict, page: int):
    """
    Parses incoming data into an array with fully formatted data for a given page.
    :param data: Dictionary of data to parse.
    :param page: Page number.
    :return: Array of data for given page.
    """

    if page == 0:
        # CPU Page 1
        page_data = []
        # Use .get() for fallback
        page_data.append (data.get("cpu_f"))
        page_data.append (data.get("cpu_temps_f"))
        page_data.append (data.get("current_freq_f"))

    elif page == 1:
        # CPU Page 2
        page_data = []
        # Get values
        page_data.append (data.get("min_freq_f"))
        page_data.append (data.get("max_freq_f"))
        page_data.append (f"Last min: {data.get("one_load_f")}")
        page_data.append (f"Last 5 mins: {data.get("five_load_f")}")
        page_data.append (f"Last 15 mins: {data.get("fifteen_load_f")}")

    elif page == 2:
        # Memory, disc usage and uptime
        page_data = []
        # Get values
        page_data.append (data.get("mem_f"))
        page_data.append (f'Free: {data.get("free_mem_f")}')
        page_data.append(f"Disc: {data.get("disc_f")}")
        page_data.append (f"Free: {data.get("free_disc_f")}")
        page_data.append (f'Uptime: {data.get("uptime_f")}')

    elif page == 3:
        # Disc
        page_data = []
        # Get values
        page_data.append (data.get("disc_ops_f"))
        page_data.append(data.get("disc_gb_f"))
        page_data.append(data.get("disc_times_f"))

    elif page == 4:
        # Network
        page_data = []
        # Get values
        page_data.append(data.get("network_gb_f"))
        page_data.append(data.get("network_packets_f"))

    elif page == 5:
        # Temps & Battery
        page_data = []
        # Get values
        page_data.append (f"CPU Usage: {data.get("one_load_f")}")
        page_data.append (data.get("cpu_temps_f"))
        page_data.append (data.get("fans_f"))
        page_data.append (f"Battery: {data.get("battery_f")}")

    elif page == 6:
        # Minecraft Server 1
        page_data = []
        # Get values
        mc_data = data.get("mc1")
        page_data.append (f"Status: {mc_data.get("running_f")}")
        page_data.append(f"RAM Usage: {mc_data.get("ram_gb_f")}")
        page_data.append (f"CPU Usage: {mc_data.get("cpu_percent_f")}")
        page_data.append (mc_data.get("status_display_f"))
        page_data.append (mc_data.get("pid_f"))

    elif page == 7:
        # Minecraft Server 2
        page_data = []
        # Get values
        mc_data = data.get("mc2")
        page_data.append (f"Status: {mc_data.get("running_f")}")
        page_data.append(f"RAM Usage: {mc_data.get("ram_gb_f")}")
        page_data.append (f"CPU Usage: {mc_data.get("cpu_percent_f")}")
        page_data.append (mc_data.get("status_display_f"))
        page_data.append(mc_data.get("pid_f"))


    return page_data

class MacDisplaySimulator:
    """Simulates an e-paper screen in Mac terminal."""

    def __init__(self, width=30):
        self.width = width

    def clear(self):
        # Clears terminal screen or prints spacing
        print("\n" * 2)

    def render_page(self, heading, lines):
        self.clear()
        self.heading = str(heading)
        print("┌" + "─" * self.width + "┐")
        # Print centred heading
        total_padding = self.width - len(self.heading)
        left_pad = total_padding // 2
        right_pad = total_padding - left_pad
        self.heading.center(20)
        centered_heading = ((" " * left_pad) + f"\033[4m{self.heading}\033[0m" + (" " * right_pad))
        print(centered_heading)
        
        
        for line in lines:
            # Pad or truncate to fit screen width
            print (wraptext.wrap(line, self.width))
        print("└" + "─" * self.width + "┘")



## MAIN LOOP ##

def render(data, index, display):
    page = parse_data(data, index)
    display.render_page(HEADINGS[index], page)

def main():
    display = MacDisplaySimulator(40)
    index = 7
    try:
        #print("\n--- Polling Server ---")
        # 1. Fetch and parse data
        data = poll.fetch_data()  # Your function that returns the JSON dict

        if data:
            display.clear()
            render (data, index, display)
            # display.show(p1) etc.
            #print("Data fetched and processed successfully.")

    except Exception as e:
        # Catch network errors, timeouts, or JSON parsing issues so the loop survives
        print(f"Polling failed: {e}")

    # Handle button presses
    if False:  # PLACEHOLDER BUTTON PRESS
        index += 1
        display.clear()
        render (data, index, display)

    # 3. Wait for 5 minutes before the next poll
    #print(f"Waiting {POLL_INTERVAL // 60} minutes until next update...")
    time.sleep(POLL_INTERVAL)



if __name__ == "__main__":
    while True:
        main()