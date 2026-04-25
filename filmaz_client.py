import json
from pathlib import Path
import asyncio
from rubika_bot import RubikaBot
import logging


class FilmazClient:
    def __init__(
        self,
        rubika: RubikaBot,
        browser,
        site_url,
        login_url,
        username,
        password,
        chat_id: str = "b0BIr1v0ZDT08d2bfbaabad3c8b45edc",
        session_path: str = "auth.json",
    ):
        self.rubika = rubika
        self.browser = browser
        self.site_url = site_url
        self.login_url = login_url
        self.username = username
        self.password = password
        self.chat_id = chat_id
        self.session_path = session_path

        self.logger = logging.getLogger("filmazClient")

    async def login(self):
        page = None
        try:
            # ---------- OPEN PAGE ----------
            try:
                page = await self.browser.new_page()
                await page.goto(self.login_url)
            except Exception as e:
                self.logger.error(f"couldnt goto {self.login_url}: {e}")
                await self.rubika.send_text_message(
                    self.chat_id, f"navigation to {self.login_url} failed. detail: {e}"
                )
                return {
                    "status": False,
                    "error": f"navigation to {self.login_url} failed.",
                    "detail": str(e),
                }

            # ---------- GET CAPTCHA ----------
            try:
                cap_loc = page.locator("#imgCap")
                await cap_loc.wait_for(state="attached")
                await cap_loc.wait_for(state="visible")
                img_bytes = await cap_loc.screenshot()
            except Exception as e:
                await self.rubika.send_text_message(
                    self.chat_id, f"captcha image not found: {e}"
                )
                return {
                    "status": False,
                    "error": f"captcha image of login form from '{self.login_url}' not found",
                    "detail": str(e),
                }

            # ---------- SEND CAPTCHA ----------
            res = await self.rubika.send_image(self.chat_id, img_bytes, "captcha.png")
            if not res["status"]:
                await self.rubika.send_text_message(
                    self.chat_id, f"Error sending captcha: {res}"
                )
                return {
                    "status": False,
                    "error": "CaptchaImage sending to Bot failed!!!",
                    "detail": res,
                }

            # ---------- GET CAPTCHA ANSWER ----------
            captcha_text = await self.wait_for_captcha_answer()
            if not captcha_text:
                await self.rubika.send_text_message(
                    self.chat_id, "No captcha reply received."
                )
                return {
                    "status": False,
                    "error": "captcha_timeout",
                    "detail": "User did not reply in time",
                }

            await self.rubika.send_text_message(
                self.chat_id, f"Captcha Received: {captcha_text}"
            )

            # ---------- FILL LOGIN FORM ----------
            try:
                await page.locator('input[name="mobile"]').wait_for(state="visible")
                await page.locator('input[name="mobile"]').fill(self.username)
                await page.locator('input[name="password"]').fill(self.password)
                await page.locator('input[name="captcha"]').fill(captcha_text)
                await page.locator('button[name="submit"]').click()
            except Exception as e:
                await self.rubika.send_text_message(
                    self.chat_id, f"form_fill_failed: {e}"
                )
                return {
                    "status": False,
                    "error": "filling of form fields in login page failed",
                    "detail": str(e),
                }

            # ---------- WAIT FOR USERNAME ON PAGE ----------
            try:

                await page.wait_for_url(f"{self.site_url}/*")
                username_locator = page.locator("span.DrMenuTxt1")
                await username_locator.wait_for(state="attached")  # state="visible"
                text = await username_locator.inner_text()
            except Exception as e:
                await self.rubika.send_text_message(
                    self.chat_id, f"login_result_missing [username not found]: {e}"
                )
                return {
                    "status": False,
                    "error": "Login failed, Username not found after login.",
                    "detail": str(e),
                }

            # ---------- CHECK LOGIN SUCCESS ----------
            if self.username in text:
                # SUCCESS
                cookies = await page.context.cookies()
                Path(self.session_path).write_text(json.dumps(cookies, indent=2))
                await self.rubika.send_text_message(
                    self.chat_id, "Login successful 👍 Session saved."
                )
                return {"status": True, "message": "login_success", "cookies": cookies}
            else:
                await self.rubika.send_text_message(
                    self.chat_id, "Login failed ❌ Username not found after login."
                )
                return {
                    "status": False,
                    "error": "wrong_username_after_login",
                    "detail": text,
                }
        except Exception as e:
            # CATCH ANY UNEXPECTED ERROR
            await self.rubika.send_text_message(self.chat_id, f"Unexpected error: {e}")
            return {"status": False, "error": "unexpected_exception", "detail": str(e)}

        finally:
            if page:
                try:
                    await page.close()
                except:
                    pass

    async def wait_for_captcha_answer(self):
        await self.rubika.get_updates()  # flush old messages
        await asyncio.sleep(3)  # allow backend to deliver sent message
        for _ in range(10):  # ~10x 2seconds
            res = await self.rubika.get_updates()
            if res["status"] == True and res["count"] > 0:
                update = res["updates"][-1]
                if update.get("type") == "NewMessage":
                    msg = update["new_message"]
                    text = msg.get("text")
                    if text:
                        return text.strip()
            await asyncio.sleep(2)

        return None

    async def is_logged_in(self):
        page = None
        try:
            page = await self.browser.new_page()

            # load saved cookies if they exist
            if Path(self.session_path).exists():
                cookies = json.loads(Path(self.session_path).read_text())
                await page.context.add_cookies(cookies)

            await page.goto(self.site_url)
            await page.wait_for_url(f"{self.site_url}/*")

            try:
                username_locator = page.locator("span.DrMenuTxt1")
                await username_locator.wait_for(state="attached")  # state="visible"
                text = await username_locator.inner_text()

                if self.username in text:
                    return {
                        "status": True,
                        "logged_in": True,
                        "message": text,
                        "error": "",
                        "error_detail": "",
                    }
            except:
                pass

            return {
                "status": True,
                "logged_in": False,
                "message": "user not logged in, you should login first",
                "error": "",
                "error_detail": "",
            }
        except Exception as e:
            return {
                "status": False,
                "logged_in": False,
                "message": "",
                "error": "check_login_failed",
                "error_detail": str(e),
            }

        finally:
            if page:
                try:
                    await page.close()
                except:
                    pass
