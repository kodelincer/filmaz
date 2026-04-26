import httpx
import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, Optional


class RubikaBot:

    def __init__(
        self,
        token: str,
        offset_file_url: str = "last_offset.txt",
        timeout: int = 10,
        retries: int = 3,
    ):
        self.token = token
        self.offset_file = Path(offset_file_url)
        self.retries = max(1, retries)

        self.base = f"https://botapi.rubika.ir/v3/{token}"
        self.update_url = f"{self.base}/getUpdates"
        self.send_msg_url = f"{self.base}/sendMessage"
        self.request_file_url = f"{self.base}/requestSendFile"
        self.send_file_url = f"{self.base}/sendFile"

        self.filmaz = None  # will be set later

        self.client = httpx.AsyncClient(timeout=timeout)
        self.logger = logging.getLogger("RubikaBot")

    def load_offset(self) -> str:
        try:
            if self.offset_file.exists():
                return self.offset_file.read_text().strip()
        except Exception as e:
            self.logger.error(f"Failed to load offset: {e}")
        return "0"

    def save_offset(self, offset):
        try:
            self.offset_file.write_text(str(offset), encoding="utf-8")
        except Exception as e:
            # important: log, but don't crash the whole bot if filesystem is read-only etc.
            self.logger.error(f"Failed to save offset: {e}")

    async def get_updates(self, limit: int = 100) -> Dict[str, Any]:

        payload = {"limit": limit, "offset_id": self.load_offset()}

        for attempt in range(self.retries):
            try:
                response = await self.client.post(self.update_url, json=payload)
                response.raise_for_status()

                try:
                    result = response.json()
                except Exception as e:
                    self.logger.error(f"Invalid JSON from getUpdates: {e}")
                    return {
                        "status": False,
                        "error": "invalid_json",
                        "error_detail": str(e),
                        "updates": [],
                        "count": 0,
                    }

                if result.get("status") != "OK":
                    return {
                        "status": False,
                        "error": "api_status_not_ok",
                        "error_detail": result.get("status"),
                        "updates": [],
                        "count": 0,
                    }

                # 3) validate top-level structure
                inside_result = result.get("data")
                if not isinstance(inside_result, dict):
                    return {
                        "status": False,
                        "error": "invalid_response",
                        "error_detail": "Missing or non-dict 'data' from Rubika",
                        "updates": [],
                        "count": 0,
                    }

                updates = inside_result.get("updates")
                if not isinstance(updates, list):
                    return {
                        "status": False,
                        "error": "invalid_updates",
                        "detail": "'updates' is missing or not a list",
                        "updates": [],
                        "count": 0,
                    }

                # ----- save new offset if present -----
                next_offset = inside_result.get("next_offset_id")
                if isinstance(next_offset, str) and next_offset:
                    self.save_offset(next_offset)

                # ----- SUCCESS (even if updates list is empty) -----
                return {
                    "status": True,
                    "error": None,
                    "detail": None,
                    "updates": updates,
                    "count": len(updates),
                }

            except httpx.TimeoutException:
                self.logger.warning("Timeout contacting Rubika")

            except httpx.RequestError as e:
                self.logger.warning(f"Network error: {e}")

            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                return {
                    "status": False,
                    "error": "unexpected_error",
                    "error_detail": str(e),
                    "updates": [],
                    "count": 0,
                }

            await asyncio.sleep(1)

        return {
            "status": False,
            "error": "max_retries_exceeded",
            "error_detail": "",
            "updates": [],
            "count": 0,
        }

    async def update_loop(self):
        while True:
            res = await self.get_updates()
            if res["status"] == True and res["count"] > 0:
                # read last message
                update = res["updates"][-1]

                if update.get("type") == "NewMessage":
                    msg = update["new_message"]
                    text = msg.get("text")
                    if text:
                        future = self.waiting_users.get(self.chat_id)
                        if future and not future.done():
                            future.set_result(text)

            await asyncio.sleep(3)

    async def send_text_message(self, chat_id: str, text: str) -> Dict[str, Any]:

        payload = {
            "chat_id": chat_id,
            "text": text,
        }

        for attempt in range(self.retries):
            try:
                response = await self.client.post(self.send_msg_url, json=payload)
                response.raise_for_status()

                try:
                    result = response.json()
                except Exception as e:
                    self.logger.error(f"Invalid JSON from sendMessage: {e}")
                    return {
                        "status": False,
                        "error": "invalid_json",
                        "error_detail": str(e),
                    }

                if result.get("status") != "OK":
                    return {
                        "status": False,
                        "error": "api_error",
                        "error_detail": result,
                    }

                message_id = result.get("data", {}).get("message_id")
                if not message_id:
                    return {
                        "status": False,
                        "error": "missing_message_id",
                        "error_detail": result,
                    }

                return {"status": True, "error": None, "message_id": message_id}

            except httpx.TimeoutException:
                self.logger.warning("Timeout contacting Rubika")

            except httpx.RequestError as e:
                self.logger.warning(f"Network error: {e}")

            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                return {
                    "status": False,
                    "error": "unexpected_error",
                    "error_detail": str(e),
                }

            await asyncio.sleep(1)

        return {"status": False, "error": "max_retries_exceeded", "error_detail": ""}

    async def request_upload_url(self, file_type: str = "Image") -> Dict[str, Any]:

        payload = {"type": file_type}

        for attempt in range(self.retries):
            try:
                response = await self.client.post(self.request_file_url, json=payload)
                response.raise_for_status()

                try:
                    result = response.json()
                except Exception as e:
                    self.logger.error(f"Invalid JSON from requestSendFile: {e}")
                    return {
                        "status": False,
                        "error": "invalid_json",
                        "error_detail": str(e),
                    }

                if result.get("status") != "OK":
                    return {
                        "status": False,
                        "error": "api_error",
                        "error_detail": result,
                    }

                upload_url = result.get("data", {}).get("upload_url")
                if not upload_url:
                    return {
                        "status": False,
                        "error": "upload_url_missing",
                        "error_detail": result,
                    }

                return {
                    "status": True,
                    "error": None,
                    "upload_url": upload_url,
                }

            except httpx.TimeoutException:
                self.logger.warning("Timeout request_upload_url Rubika")
            except httpx.RequestError as e:
                self.logger.warning(f"Network error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                return {
                    "status": False,
                    "error": "unexpected_error",
                    "error_detail": str(e),
                }

            await asyncio.sleep(1)

        return {"status": False, "error": "max_retries_exceeded", "error_detail": ""}

    async def upload_file(
        self, upload_url: str, file_bytes: bytes, filename: str = "captcha.png"
    ) -> Dict[str, Any]:

        files = {"file": (filename, file_bytes)}
        max_upload_retries = 2

        for attempt in range(max_upload_retries):
            try:
                response = await self.client.post(upload_url, files=files)
                response.raise_for_status()

                try:
                    result = response.json()
                except Exception as e:
                    self.logger.error(f"Invalid JSON from upload_file: {e}")
                    return {
                        "status": False,
                        "error": "invalid_json",
                        "error_detail": str(e),
                    }

                if result.get("status") != "OK":
                    return {
                        "status": False,
                        "error": "upload_failed",
                        "error_detail": result,
                    }

                file_id = result.get("data", {}).get("file_id")
                if not file_id:
                    return {
                        "status": False,
                        "error": "file_id_missing",
                        "error_detail": result,
                    }

                return {"status": True, "error": None, "file_id": file_id}

            except httpx.TimeoutException:
                self.logger.warning("Timeout upload_file Rubika")
            except httpx.RequestError as e:
                self.logger.warning(f"Network error: {e}")
            except Exception as e:
                self.logger.exception("Unexpected error in send_file")
                return {
                    "status": False,
                    "error": "unexpected_error",
                    "error_detail": str(e),
                }

            await asyncio.sleep(1)

        return {"status": False, "error": "max_retries_exceeded", "error_detail": ""}

    async def send_file(self, chat_id: str, file_id: str) -> Dict[str, Any]:

        payload = {
            "chat_id": chat_id,
            "file_id": file_id,
        }

        for attempt in range(self.retries):
            try:
                response = await self.client.post(self.send_file_url, json=payload)
                response.raise_for_status()

                try:
                    result = response.json()
                except Exception as e:
                    self.logger.error(f"Invalid JSON from sendFile: {e}")
                    return {
                        "status": False,
                        "error": "invalid_json",
                        "error_detail": str(e),
                    }

                if result.get("status") == "OK":
                    message_id = result.get("data", {}).get("message_id")
                    if not message_id:
                        return {
                            "status": False,
                            "error": "missing_message_id",
                            "error_detail": result,
                        }

                    return {
                        "status": True,
                        "error": None,
                        "message_id": message_id,
                    }

                return {
                    "status": False,
                    "error": "api_error",
                    "error_detail": result,
                }

            except httpx.TimeoutException:
                self.logger.warning("Timeout send_file Rubika")
            except httpx.RequestError as e:
                self.logger.warning(f"Network error: {e}")
            except Exception as e:
                self.logger.exception("Unexpected error in send_file")
                return {
                    "status": False,
                    "error": "unexpected_error",
                    "error_detail": str(e),
                }

            await asyncio.sleep(1)

        return {"status": False, "error": "max_retries_exceeded", "error_detail": ""}

    async def send_image(
        self, chat_id: str, image_bytes: bytes, filename: str = "captcha.png"
    ) -> Dict[str, Any]:

        # Step 1: request upload url
        up = await self.request_upload_url()
        if not up.get("status"):
            return {
                "status": False,
                "error": "request_upload_url_failed",
                "error_detail": up,
            }

        # Step 2: upload file
        upload = await self.upload_file(up["upload_url"], image_bytes, filename)
        if not upload.get("status"):
            return {
                "status": False,
                "error": "upload_failed",
                "error_detail": upload,
            }

        # Step 3: send file
        send_res = await self.send_file(chat_id, upload["file_id"])
        if not send_res.get("status"):
            return {
                "status": False,
                "error": "send_file_failed",
                "error_detail": send_res,
            }

        return {
            "status": True,
            "error": None,
            "message_id": send_res["message_id"],
        }

    async def close(self) -> None:
        try:
            await self.client.aclose()
        except Exception as e:
            self.logger.error(f"Error closing httpx client: {e}")
