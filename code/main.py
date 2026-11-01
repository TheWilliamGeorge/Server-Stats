print ('starting...')

import json
from flask import Flask, jsonify, request, abort
import hashlib
from datetime import datetime, timezone, timedelta

import stats

app = Flask(__name__)

with open('shared_secret.txt', 'r') as file:
    SHARED_SECRET = file.read()


def get_daily_token(target_date=None):
    """Generates a SHA-256 hash token for a specific date (defaults to today UTC)."""
    if target_date is None:
        target_date = datetime.now(timezone.utc).date()

    # Format date as 'YYYY-MM-DD'
    date_str = target_date.isoformat()

    # Combine secret and date
    payload = f"{SHARED_SECRET}-{date_str}"

    # Return hex digest
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()



# Define a secret token that authorized devices must send
SECRET_TOKEN = "token"



@app.route('/data', methods=['GET'])
def get_data():
    # Check for the Authorization header
    auth_header = request.headers.get('Authorization')

    # Calculate valid tokens for Today and Yesterday (grace period)
    today_utc = datetime.now(timezone.utc).date()
    yesterday_utc = today_utc - timedelta(days=1)

    valid_tokens = [
        f"Bearer {get_daily_token(today_utc)}",
        f"Bearer {get_daily_token(yesterday_utc)}"
    ]

    if not auth_header or auth_header not in valid_tokens:
        abort(401, description="Unauthorized: Invalid or expired daily token.")

    # Call psutil stats -gathering code to get data
    data = stats.get_system_stats()

    try:
        # Load and return the JSON file
        with open('data/data.json', 'r') as file:
            data = json.load(file)
        return jsonify(data)
    except FileNotFoundError:
        abort(404, description="JSON file not found on the server.")

if __name__ == '__main__':
    # host='0.0.0.0' makes it accessible from other devices on the network
    app.run(host='0.0.0.0', port=5001)