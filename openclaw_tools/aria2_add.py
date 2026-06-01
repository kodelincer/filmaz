import os
import requests
from dotenv import load_dotenv


def run(url):

    try:
        load_dotenv()
        aria2c_base_url = os.getenv("aria2c_base_url")
        aria2c_port = os.getenv("aria2c_port")
        aria2c_path = os.getenv("aria2c_path")
        aria2c_token = os.getenv("aria2c_token")
        final_url = f"{aria2c_base_url}:{aria2c_port}/{aria2c_path}"

        payload = {
            "jsonrpc": "2.0",
            "id": "add",
            "method": "aria2.addUri",
            "params": [f"token:{aria2c_token}", [url]],
        }

        r = requests.post(final_url, json=payload)

        data = r.json()
        return {
            "status": True,
            "msg": "url added to aria2c rpc server for downloading the file",
            "results": {"gid": data["result"]},
            "error": "",
            "detail": "",
        }

    except Exception as e:
        return {
            "status": False,
            "msg": "",
            "detail": "fail: adding url to download failed",
            "error": str(e),
        }
