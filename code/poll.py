import json
import requests
import hashlib
from datetime import datetime, timezone
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
url_path = os.path.join(script_dir, 'server_url.txt')
secret_path = os.path.join(script_dir, 'shared_secret.txt')

# Use 'localhost' or '127.0.0.1' if running the Flask server on the same machine
with open(url_path, 'r') as file:
    SERVER_URL = file.read()

with open(secret_path, 'r') as file:
    SHARED_SECRET = file.read()


def get_todays_token():
    """Generates today's SHA-256 token using standard Python datetime and hashlib."""
    # Get current UTC date in YYYY-MM-DD format
    today_utc = datetime.now(timezone.utc).date()
    date_str = today_utc.isoformat()

    # Combine secret and date
    payload = f"{SHARED_SECRET}-{date_str}"

    # Generate SHA-256 hex digest
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def fetch_data():
    token = get_todays_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        #print(f"Requesting data from {SERVER_URL}...")
        response = requests.get(SERVER_URL, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            #print("Successfully received data:")
            #print(data)

            '''
            # Debug: write to json file
            dump = json.dumps(data)
            with open('client/data/data.json', 'w') as file:
                file.write(dump)
            '''

            return data

        else:
            print(f"Failed with status code {response.status_code}:")
            print(response.text)
            return {}
            
    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    fetch_data()