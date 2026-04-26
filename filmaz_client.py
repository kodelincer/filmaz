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
        session_path: str = "config/auth.json",
    ):
        self.rubika = rubika
        self.browser = browser
        self.site_url = site_url
        self.login_url = login_url
        self.username = username
        self.password = password
        self.chat_id = chat_id
        self.session_path = session_path

        # Later when you want multiple users simultaneously, you replace this with:
        # self.waiting_futures = {
        #     chat_id: future
        # }
        self.waiting_users = {
            self.chat_id: None
        }  # key = chat_id, value = Future object

        # self.waiting_users = {
        #     1111: <Future pending>,   # User A waiting
        #     2222: <Future pending>,   # User B waiting
        #     3333: <Future pending>,   # User C waiting
        # }

        self.last_search_query = None
        # store both results with index
        self.last_search_results = []
        self.last_quality_results = []

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

    async def wait_for_user(self, chat_id):
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        # store the future for this chat
        self.waiting_users[chat_id] = future
        # wait until resolved
        result = await future
        # cleanup
        self.waiting_users.pop(chat_id, None)
        return result

    def handle_incoming_message(self, chat_id, text):
        # check if this chat is currently waiting for user input
        future = self.waiting_users.get(chat_id)

        if future and not future.done():
            future.set_result(text)
            return

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

    async def download_movie(self, dlink: str):
        # download file here by fastapi,  without agent and its tools like curl
        return {"status": True, "url": ""}
