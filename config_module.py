import argparse
import json
import logging
import platform
import httpx
import socket
import asyncio
import uuid
import psutil

logging.basicConfig(level=logging.INFO)

REQUIRED_KEYS = [
    'azure_iot_hub_host',
    'device_id',
    'shared_access_key',
    'rewst_engine_host',
    'rewst_org_id'
]

async def fetch_configuration(config_url, secret=None):
    # Collect host information
    host_info = {
        "hostname": socket.gethostname(),
        "mac_address": get_mac_address(),
        "is_domain_controller": is_domain_controller(),  # We'll need to implement this
        "operating_system": platform.platform(),
        "cpu_model": platform.processor(),
        "ram_gb": psutil.virtual_memory().total / (1024 ** 3)
    }

    headers = {}
    if secret:
        headers['x-rewst-secret'] = secret
    
    retry_intervals = [(5, 12), (60, 60), (300, float('inf'))]  # (interval, max_retries) for each phase
    for interval, max_retries in retry_intervals:
        retries = 0
        while retries < max_retries:
            retries += 1
            async with httpx.AsyncClient(timeout=None) as client:  # Set timeout to None to wait indefinitely
                try:
                    response = await client.post(
                        config_url,
                        json=host_info,
                        headers=headers,
                        follow_redirects=True
                    )
                except httpx.TimeoutException:
                    logging.warning(f"Attempt {retries}: Request timed out. Retrying...")
                    continue  # Skip the rest of the loop and retry

                except httpx.RequestError as e:
                    logging.warning(f"Attempt {retries}: Network error: {e}. Retrying...")
                    continue

                if response.status_code == 200:
                    data = response.json()
                    config_data = data.get('configuration')
                    if config_data and all(key in config_data for key in REQUIRED_KEYS):
                        return config_data
                    else:
                        logging.warning(f"Attempt {retries}: Missing required keys in configuration data. Retrying...")
                elif response.status_code == 400 or response.status_code == 401:
                    logging.error(f"Attempt {retries}: Not authorized. Check your config secret.")
                else:
                    logging.warning(f"Attempt {retries}: Received status code {response.status_code}. Retrying...")
            await asyncio.sleep(interval)
        logging.info(f"Moving to next retry phase: {interval}s interval for {max_retries} retries.")


def save_configuration(config_data, file_path='config.json'):
    # Save configuration to a file
    with open(file_path, 'w') as f:
        json.dump(config_data, f, indent=4)

def load_configuration(file_path='config.json'):
    # Load configuration from a file
    try:
        with open(file_path) as f:
            return json.load(f)
    except FileNotFoundError:
        return None
 
def get_mac_address():
    # Returns the MAC address of the host without colons
    mac_num = hex(uuid.UUID(int=uuid.getnode()).int)[2:]
    mac_address = ':'.join(mac_num[i: i + 2] for i in range(0, 11, 2))
    return mac_address.replace(':', '')


def is_domain_controller():
    # We'll need to implement logic to determine if the host is a domain controller
    pass

async def main():
    parser = argparse.ArgumentParser(description='Fetch and save configuration.')
    parser.add_argument('--config-secret', type=str, help='Secret to use when fetching the configuration.')
    args = parser.parse_args()

    config = load_configuration()
    if config is None:
        print("Configuration file not found. Fetching configuration from Rewst...")
        config_url = args.config_url
        config_secret = args.config_secret
        config = await fetch_configuration(config_url, secret=config_secret)  # Pass the secret to fetch_configuration
        save_configuration(config)
        print(f"Configuration saved to config.json")
    return config  # Return the configuration

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
