import os
import re
import time
import uuid
import base64
import logging
from dotenv import load_dotenv
from playwright.async_api import async_playwright


class FilmazClient:

    def __init__(self):

        load_dotenv()

        self.base_url = os.getenv("webapi_base_url")
        self.site_url = os.getenv("site_url")
        self.login_url = os.getenv("login_url")
        self.username = os.getenv("flzios_user")
        self.password = os.getenv("flzios_pass")

        self.playwright = None
        self.context = None
        self.pending_logins = {}

        self.logger = logging.getLogger("filmazClient")

    async def initialize(self):

        self.playwright = await async_playwright().start()

        self.context = await self.playwright.chromium.launch_persistent_context(
            executable_path=r"./chrome-win64/chrome.exe",
            user_data_dir=r"./chrome-profile",
            viewport={"width": 1366, "height": 768},
            # user_agent="Mozilla/5.0 ..."
            headless=True,
            ignore_https_errors=True,
            args=[
                "--ignore-certificate-errors",
                "--ignore-certificate-errors-spki-list",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
        )

    async def start_login(self):
        try:
            # open login page
            try:
                page = await self.context.new_page()
                # await page.goto(self.login_url)
                await page.goto(
                    self.login_url, wait_until="domcontentloaded", timeout=30000
                )
            except Exception as e:
                self.logger.error(f"couldnt goto {self.login_url}: {e}")
                return {
                    "status": False,
                    "msg": "",
                    "error": f"navigation to {self.login_url} failed.",
                    "detail": str(e),
                }

            # capture captcha image from login page
            try:
                cap_loc = page.locator("#imgCap")
                await cap_loc.wait_for(state="visible", timeout=15000)
                img_bytes = await cap_loc.screenshot()

                login_page_id = str(uuid.uuid4())
                self.pending_logins[login_page_id] = {
                    "page": page,
                    "captcha_bytes": img_bytes,
                    "created_at": time.time(),
                }

                return {
                    "status": True,
                    "msg": "CaptchaImage captured successfully",
                    "data": {
                        "login_page_id": login_page_id,
                        "captcha_url": f"{self.base_url}/api/auth/captcha/{login_page_id}",
                    },
                    "error": "",
                    "detail": "",
                }
            except Exception as e:
                self.logger.error(f"failed in getting captcha image: {e}")
                return {
                    "status": False,
                    "msg": "",
                    "error": f"failed: captcha image of LOGIN FORM not found",
                    "detail": str(e),
                }
        except Exception as e:
            # CATCH ANY UNEXPECTED ERROR
            self.logger.error(f"UNEXPECTED ERROR in login page/form: {e}")
            return {
                "status": False,
                "msg": "",
                "error": "unexpected_exception: in login page/form",
                "detail": str(e),
            }

    async def complete_login(self, login_page_id: str, captcha_answer: str):

        page = None
        try:

            pending_page = self.pending_logins.get(login_page_id)
            if not pending_page:
                return {
                    "status": False,
                    "msg": "",
                    "error": "invalid_login_page_id",
                    "detail": str(login_page_id),
                }
            page = pending_page["page"]

            # ---------- FILL LOGIN FORM ----------
            try:

                await page.locator('input[name="mobile"]').wait_for(state="visible")

                await page.locator('input[name="mobile"]').fill(self.username)
                await page.locator('input[name="password"]').fill(self.password)
                await page.locator('input[name="captcha"]').fill(captcha_answer)

            except Exception as e:
                self.logger.error(f"FILLING LOGIN FORM: {e}")
                return {
                    "status": False,
                    "msg": "",
                    "error": "failed: filling of form fields in login page failed",
                    "detail": str(e),
                }

            # ---------- WAIT FOR LOGIN RESULT ----------
            try:
                # Start listening for a page navigation BEFORE doing an action that may cause navigation like (click)
                # This solves race conditions on fast internet.
                async with page.expect_navigation(
                    wait_until="domcontentloaded", timeout=10000
                ):
                    await page.locator('button[name="submit"]').click()

                # small delay for page reaction
                await page.wait_for_timeout(2000)
                self.logger.info(f"Current URL after login: {page.url}")

                # still on login page => probably wrong captcha
                if "login" in page.url.lower():

                    return {
                        "status": False,
                        "msg": "",
                        "error": "wrong_captcha_or_login_failed",
                        "detail": f"still on login page after submit: {page.url}",
                    }

                # # wait for redirect after successful login
                # await page.wait_for_url(
                #     re.compile(f"{re.escape(self.site_url)}.*"),
                #     timeout=10000,
                # )

            except Exception as e:
                self.logger.error(f"LOGIN REDIRECT FAILED: {e}")
                return {
                    "status": False,
                    "msg": "",
                    "error": "login_redirect_failed",
                    "detail": str(e),
                }

            # ---------- CHECK USERNAME PANEL ----------
            try:

                username_locator = page.locator("span.DrMenuTxt1")
                await username_locator.wait_for(
                    state="attached",
                    timeout=10000,
                )
                text = await username_locator.inner_text()

            except Exception as e:
                self.logger.error(f"WAITING FOR USERNAME PANEL FAILED: {e}")
                return {
                    "status": False,
                    "msg": "",
                    "error": "username_info_panel_not_found_after_login",
                    "detail": str(e),
                }

            # ---------- FINAL LOGIN CHECK ----------
            if self.username in text:
                return {
                    "status": True,
                    "msg": f"Login successful! Welcome back, {self.username}!",
                    "error": "",
                    "detail": "",
                }

            return {
                "status": False,
                "msg": "",
                "error": f"username '{self.username}' not found after login",
                "detail": text,
            }

        except Exception as e:
            self.logger.error(f"UNEXPECTED ERROR: {e}")
            return {
                "status": False,
                "msg": "",
                "error": "unexpected_exception",
                "detail": str(e),
            }

        finally:

            # remove pending login session
            if login_page_id in self.pending_logins:
                del self.pending_logins[login_page_id]

            # close login page
            try:
                if page:
                    await page.close()
            except:
                pass

    async def is_logged_in(self):

        page = None
        try:
            page = await self.context.new_page()
            await page.goto(self.site_url, wait_until="domcontentloaded")

            try:
                username_locator = page.locator("span.DrMenuTxt1")
                await username_locator.wait_for(state="attached")  # state="visible"
                text = await username_locator.inner_text()

                if self.username in text:
                    return {
                        "status": True,
                        "message": f"your logged in with the username: {text}",
                        "error": "",
                        "error_detail": "",
                    }
            except:
                pass

            return {
                "status": False,
                "message": "",
                "error": "user not logged in, you should login first",
                "error_detail": "",
            }
        except Exception as e:
            return {
                "status": False,
                "message": "",
                "error": "checking_loggedIn_status_failed",
                "error_detail": str(e),
            }
        finally:
            if page:
                await page.close()

    async def search(self, query: str, page_index: int = 1):

        page = None
        try:
            page = await self.context.new_page()
            url = f"https://flzios.com/search?q={query}"
            # await page.goto(url)
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # If redirected to login → session expired
            if "login" in page.url:
                return {
                    "status": False,
                    "message": "you should first login to the website.",
                    "error": "not_logged_in",
                    "detail": "",
                }

            # Wait for movie list to load
            await page.locator(".movie_list").wait_for()
            movie_items = page.locator(".movie_item")
            count = await movie_items.count()

            if count == 0:
                return {
                    "status": True,
                    "msg": "no results found",
                    "data": [],
                    "error": "",
                    "detail": "",
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

            return {
                "status": True,
                "msg": f"{count} item(s) found",
                "data": results,
                "error": "",
                "detail": "",
            }

        except Exception as e:
            return {
                "status": False,
                "msg": "",
                "error": "search_failed",
                "detail": str(e),
            }
        finally:
            if page:
                await page.close()

    async def get_qualities(self, movie_pageurl: str):

        page = None
        try:
            page = await self.context.new_page()
            # await page.goto(movie_pageurl)
            await page.goto(movie_pageurl, wait_until="domcontentloaded", timeout=30000)

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

            return {
                "status": True,
                "msg": f"{count} quality item(s) found",
                "data": qualities,
                "error": "",
                "detail": "",
            }

        except Exception as e:
            return {
                "status": False,
                "msg": "",
                "error": "failed in getting quality links of movie",
                "detail": str(e),
            }
        finally:
            if page:
                await page.close()

    async def shutdown(self):
        await self.context.close()
