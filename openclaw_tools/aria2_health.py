# aria2_health.py should only check
# BUT NOT start services.

import os
import requests
from dotenv import load_dotenv


def run():
    try:
        load_dotenv()

        aria2c_base_url = os.getenv("aria2c_base_url")
        aria2c_port = os.getenv("aria2c_port")
        aria2c_path = os.getenv("aria2c_path")
        aria2c_token = os.getenv("aria2c_token")
        final_url = f"{aria2c_base_url}:{aria2c_port}/{aria2c_path}"

        payload = {
            "jsonrpc": "2.0",
            "id": "health_check",
            "method": "aria2.getVersion",
            "params": [f"token:{aria2c_token}"],
        }

        r = requests.post(final_url, json=payload, timeout=3)

        return {
            "running": r.status_code == 200,
            "msg": "aria2.service is running",
            "error": "",
        }

    except Exception as e:
        return {
            "running": False,
            "msg": "",
            "error:": f"aria2.health check failed, {str(e)}",
        }
