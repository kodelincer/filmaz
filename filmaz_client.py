import os
import re
import json
import uuid
from pathlib import Path
from dotenv import load_dotenv
import base64

# from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright

# from rubika_bot import RubikaBot
import logging


class FilmazClient:
    def __init__(self):

        load_dotenv()
        self.site_url = os.getenv("site_url")
        self.login_url = os.getenv("login_url")
        self.username = os.getenv("flzios_user")
        self.password = os.getenv("flzios_pass")
        self.state_file_path = os.getenv("state_file")
        self.pending_logins = {}

        self.playwright = None
        self.browser = None
        self.context = None

        self.login_page = None
        self.login_session_id = None

        self.last_search_query = None
        self.last_search_results = []
        self.last_quality_results = []

        self.logger = logging.getLogger("filmazClient")

    async def initialize(self):

        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch(
            executable_path=r"./chrome-win64/chrome.exe",
            headless=True,
            args=[
                "--ignore-certificate-errors",
                "--ignore-certificate-errors-spki-list",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
        )

        # bypass invalid SSL
        self.context = await self.browser.new_context(
            storage_state={}, ignore_https_errors=True
        )

    async def start_login(self):
        try:
            page = None
            # ---------- OPEN PAGE ----------
            try:
                page = await self.context.new_page()
                await page.goto(self.login_url)
            except Exception as e:
                self.logger.error(f"couldnt goto {self.login_url}: {e}")
                return {
                    "status": False,
                    "msg": "",
                    "error": f"navigation to {self.login_url} failed.",
                    "detail": str(e),
                }

            # ---------- GET CAPTCHA ----------
            try:
                cap_loc = page.locator("#imgCap")
                await cap_loc.wait_for(state="attached")
                await cap_loc.wait_for(state="visible")
                img_bytes = await cap_loc.screenshot()
                captcha_base64 = base64.b64encode(img_bytes).decode("utf-8")
                tmp_uuid = uuid.uuid4()
                session_id = str(tmp_uuid)
                self.pending_logins[session_id] = {
                    "page": page,
                }

                return {
                    "status": True,
                    "msg": "captcha image captured as base64 successfully and login page saved by session_id",
                    "captcha_base64": captcha_base64,
                    "session_id": session_id,
                    "error": "",
                    "detail": "",
                }
            except Exception as e:
                self.logger.error(f"GET CAPTCHA section: {e}")
                return {
                    "status": False,
                    "msg": "",
                    "error": f"captcha image of LOGIN FORM not found",
                    "detail": str(e),
                }
        except Exception as e:
            # CATCH ANY UNEXPECTED ERROR
            self.logger.error(f"UNEXPECTED ERROR: {e}")
            return {
                "status": False,
                "msg": "",
                "error": "unexpected_exception",
                "detail": str(e),
            }

    async def complete_login(self, session_id: str, captcha: str):
        try:
            session = self.pending_logins.get(session_id)
            if not session:
                return {
                    "status": False,
                    "msg": "",
                    "error": "invalid_session_id",
                    "detail": str(session_id),
                }
            page = session["page"]

            # ---------- FILL LOGIN FORM ----------
            try:
                await page.locator('input[name="mobile"]').wait_for(state="visible")
                await page.locator('input[name="mobile"]').fill(self.username)
                await page.locator('input[name="password"]').fill(self.password)
                await page.locator('input[name="captcha"]').fill(captcha)
                await page.locator('button[name="submit"]').click()
            except Exception as e:
                self.logger.error(f"FILLING LOGIN FORM: {e}")
                return {
                    "status": False,
                    "msg": "",
                    "error": "filling of form fields in login page failed",
                    "detail": str(e),
                }

            # ---------- WAIT FOR USERNAME ON PAGE ----------
            try:
                # await page.wait_for_url(re.compile(f"{self.site_url}.*"))
                await page.wait_for_url(f"{self.site_url}/*")
                username_locator = page.locator("span.DrMenuTxt1")
                await username_locator.wait_for(state="attached")  # state="visible"
                text = await username_locator.inner_text()
            except Exception as e:
                self.logger.error(f"WAITING FOR USERNAME Value ON PAGE: {e}")
                return {
                    "status": False,
                    "msg": "",
                    "error": "Login failed, Username value not found after login.",
                    "detail": str(e),
                }

            # ---------- CHECK LOGIN SUCCESS ----------
            if self.username in text:
                # SUCCESS
                cookies = await page.context.cookies()
                Path(self.state_file_path).write_text(json.dumps(cookies, indent=2))

                return {
                    "status": True,
                    "msg": "login success and auth_cookies saved for future use",
                    "error": "",
                    "detail": "",
                }
            else:
                return {
                    "status": False,
                    "msg": "",
                    "error": "wrong_username_after_login",
                    "detail": text,
                }
        except Exception as e:
            # CATCH ANY UNEXPECTED ERROR
            self.logger.error(f"UNEXPECTED ERROR: {e}")
            return {
                "status": False,
                "msg": "",
                "error": "unexpected_exception",
                "detail": str(e),
            }

        finally:
            if page:
                try:
                    await page.close()
                except:
                    pass

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

    async def search(self, query: str):
        page = None
        try:
            page = await self.browser.new_page()

            # Load session if exists
            if Path(self.session_path).exists():
                cookies = json.loads(Path(self.session_path).read_text())
                await page.context.add_cookies(cookies)

            url = f"https://flzios.com/search?q={query}"
            await page.goto(url)

            # If redirected to login → session expired
            if "login" in page.url:
                return {
                    "status": False,
                    "logged_in": False,
                    "error": "not_logged_in",
                    "message": "you must login first",
                }

            # Wait for movie list to load
            await page.locator(".movie_list").wait_for()

            movie_items = page.locator(".movie_item")
            count = await movie_items.count()

            if count == 0:
                return {
                    "status": True,
                    "logged_in": True,
                    "results": [],
                    "message": "no results found",
                }

            results = []
            for i in range(count):
                item = movie_items.nth(i)

                link = await item.locator("a").get_attribute("href")
                title = await item.locator(".movie_item_title").inner_text()
                year = await item.locator(".movie_item_year").inner_text()
                imdb = await item.locator(".movie_item_imdb").inner_text()

                full_url = f"{self.site_url}/{link}"  # https://flzios.com/{link}

                results.append(
                    {
                        "index": i + 1,
                        "title": title,
                        "year": year,
                        "imdb": imdb,
                        "page": full_url,
                    }
                )

            # store for next step
            self.last_search_results = results
            self.last_search_query = query
            self.state = "waiting_movie_index"

            # Send formatted list to rubika
            msg = f"نتایج جستجو برای '{query}':\n\n"
            for r in results:
                msg += f"{r['index']}. {r['title']} ({r['year']})\n"
            msg += "\nیک عدد ارسال کنید."

            await self.rubika.send_text_message(self.chat_id, msg)

            return {"status": True, "results": results}

        except Exception as e:
            return {
                "status": False,
                "logged_in": False,
                "error": "search_failed",
                "detail": str(e),
            }

        finally:
            if page:
                try:
                    await page.close()
                except:
                    pass

    async def open_movie_by_index(self, index: int):

        if self.state != "waiting_movie_index":
            return {"status": False, "error": "not_waiting_for_movie_index"}

        if index < 1 or index > len(self.last_search_results):
            return {"status": False, "error": "invalid_index"}

        movie = self.last_search_results[index - 1]
        url = movie["page"]

        page = None
        try:
            page = await self.browser.new_page()
            await page.goto(url)

            # TODO: after you send details of movie page, I will parse download links
            # Extract qualities from download section
            quality_items = page.locator("#result2 a")
            count = await quality_items.count()

            qualities = []
            for i in range(count):
                a = quality_items.nth(i)
                link = await a.get_attribute("href")

                size = await a.locator(".w30").inner_text()
                quality_name = await a.locator(".w70").inner_text()

                qualities.append(
                    {"i": i + 1, "quality": quality_name, "size": size, "url": link}
                )

            self.last_quality_results = qualities
            self.state = "waiting_quality_index"

            # Send to Rubika
            msg = f"کیفیت‌های فیلم '{movie['title']}':\n\n"
            for q in qualities:
                msg += f"{q['i']}. {q['quality']} — {q['size']}\n"
            msg += "\nیک شماره کیفیت بفرست."

            await self.rubika.send_text_message(self.chat_id, msg)

            await page.close()

            return {"status": True, "qualities": qualities}

        except Exception as e:
            return {"status": False, "error": "open_movie_failed", "detail": str(e)}

        finally:
            if page:
                try:
                    await page.close()
                except:
                    pass

    async def shutdown(self):
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()
