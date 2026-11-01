import urequests
import ujson
import ubinascii
import ntptime
import utime
import hashlib

# Server URL and Token configuration
with open('client/server_url.txt', 'r') as file:
    SERVER_URL = file.read()

with open('shared_secret.txt', 'r') as file:
    SHARED_SECRET = file.read()

def sync_time():
    """Syncs Pico W clock via NTP over Wi-Fi."""
    try:
        ntptime.settime()  # Sets internal RTC to current UTC time
        print("Time synchronized via NTP.")
    except Exception as e:
        print(f"NTP sync failed: {e}")


def get_todays_token():
    """Generates the exact same daily token as the server."""
    # Get current UTC date tuple: (year, month, mday, hour, minute, second, ...)
    t = utime.gmtime()

    # Format manually as YYYY-MM-DD in MicroPython
    date_str = "{:04d}-{:02d}-{:02d}".format(t[0], t[1], t[2])

    payload = f"{SHARED_SECRET}-{date_str}"

    # MicroPython-safe SHA-256 hex conversion
    h = hashlib.sha256(payload.encode('utf-8'))
    return ubinascii.hexlify(h.digest()).decode('utf-8')




def fetch_data():
    sync_time()

    token = get_todays_token()
    headers = {"Authorization": f"Bearer {token}"}

    try:
        # print(f"Requesting data from {SERVER_URL}...")
        response = urequests.get(SERVER_URL, headers=headers)

        if response.status_code == 200:
            # Parse JSON response
            data = response.json()

            # CRITICAL for MicroPython: Always close the response socket
            response.close()

            # print("Successfully received data:")
            # print(data)
            return data

        else:
            print(f"Failed with status code {response.status_code}:")
            print(response.text)
            response.close()
            return {}

    except Exception as e:
        print("An error occurred:", e)
        return {}


if __name__ == "__main__":
    # Note: Ensure your Pico W is connected to Wi-Fi before calling this function!
    fetch_data()