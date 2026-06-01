import os
import requests
from dotenv import load_dotenv


def run(gid):

    try:
        load_dotenv()
        aria2c_base_url = os.getenv("aria2c_base_url")
        aria2c_port = os.getenv("aria2c_port")
        aria2c_path = os.getenv("aria2c_path")
        aria2c_token = os.getenv("aria2c_token")
        final_url = f"{aria2c_base_url}:{aria2c_port}/{aria2c_path}"

        payload = {
            "jsonrpc": "2.0",
            "id": "resume",
            "method": "aria2.unpause",
            "params": [f"token:{aria2c_token}", gid],
        }

        result = requests.post(final_url, json=payload)
        return result.json()

    except Exception as e:
        return {
            "status": False,
            "msg": "",
            "detail": "aria2.unpause[resume] failed",
            "error": str(e),
        }
