import asyncio
import httpx
import logging
from .host_info import (
    build_host_tags
)

# Put Timestamps on logging entries
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

REQUIRED_KEYS = [
    'azure_iot_hub_host',
    'device_id',
    'shared_access_key',
    'rewst_engine_host',
    'rewst_org_id'
]


async def fetch_configuration(config_url, secret=None, org_id=None):

    host_info = build_host_tags(org_id)

    headers = {}
    if secret:
        headers['x-rewst-secret'] = secret

    logging.debug(f"Sending host information to {config_url}: {str(host_info)}")

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

                if response.status_code == 303:
                    logging.info("Waiting while Rewst processes Agent Registration...")  # Custom message for 303
                elif response.status_code == 200:
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

            logging.info(f"Attempt {retries}: Waiting {interval}s before retrying...")
            await asyncio.sleep(interval)

    logging.info("This process will end when the service is installed.")
