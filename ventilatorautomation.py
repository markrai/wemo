import pywemo
import requests
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define constants at the top of the script
DEVICE_NAME = "Fresh Air Ventilator"
JSON_URL = "http://192.168.1.180/json"
RETRY_LIMIT = 3
RETRY_DELAY = 5  # seconds
REQUEST_TIMEOUT = 10  # seconds
LOG_FILE = "ventilatorautomation.log"
THRESHOLD = 1000  # Threshold value for average

# Function to fetch and process JSON data
def fetch_json_data(url):
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching data from URL: {e}")
        return None

# Function to find the Wemo device by name
def find_wemo_device_by_name(device_name):
    try:
        devices = pywemo.discover_devices()
        for device in devices:
            if device.name == device_name:
                return device
        logging.warning(f"Device named '{device_name}' not found")
        return None
    except Exception as e:
        logging.error(f"Error discovering Wemo devices: {e}")
        return None

# Function to log ventilator state changes
def log_ventilator_state(action):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a') as log_file:
        log_file.write(f"{timestamp} - {action}\n")

# Main function to control the Wemo switch based on JSON data
def control_wemo_switch():
    # Fetch JSON data
    data = fetch_json_data(JSON_URL)
    if not data:
        logging.error("No data received from JSON URL")
        return

    # Extract values from the JSON data
    p_0_3_um = data.get("p_0_3_um")
    p_0_3_um_b = data.get("p_0_3_um_b")

    if p_0_3_um is not None and p_0_3_um_b is not None:
        # Calculate the average
        average = (p_0_3_um + p_0_3_um_b) / 2
        logging.info(f"The average of p_0_3_um and p_0_3_um_b is {average}")

        # Find the Wemo device by name
        wemo_device = find_wemo_device_by_name(DEVICE_NAME)
        if not wemo_device:
            logging.error(f"Device named '{DEVICE_NAME}' not found")
            return

        # Control the Wemo switch based on the average value
        try:
            if average < THRESHOLD:
                if wemo_device.get_state() == 0:
                    logging.info(f"Turning on the Wemo switch '{DEVICE_NAME}'")
                    wemo_device.on()
                    log_ventilator_state("Turned on")
                else:
                    logging.info(f"Wemo switch '{DEVICE_NAME}' is already on")
            else:
                if wemo_device.get_state() == 1:
                    logging.info(f"Turning off the Wemo switch '{DEVICE_NAME}'")
                    wemo_device.off()
                    log_ventilator_state("Turned off")
                else:
                    logging.info(f"Wemo switch '{DEVICE_NAME}' is already off")
        except Exception as e:
            logging.error(f"Error controlling Wemo switch '{DEVICE_NAME}': {e}")
    else:
        logging.error("Could not find the required values in the JSON response.")

# Run the main function
if __name__ == "__main__":
    control_wemo_switch()
