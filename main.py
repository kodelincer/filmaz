import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv
import logging
import uuid

# Output: 2026-04-25 21:07:32 [ERROR] RubikaBot.get_updates:45 - Invalid JSON from getUpdates
logging.basicConfig(
    filename="log/filmaz.log",
    level=logging.WARNING,  # or DEBUG
    format="%(asctime)s [%(levelname)s] %(name)s.%(funcName)s:%(lineno)d - %(message)s",
)


# from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright

from rubika_bot import RubikaBot
from filmaz_client import FilmazClient

load_dotenv()

STATE_FILE = "auth.json"
RESULT_FILE = "/tmp/filmdler_last.json"
SITE_URL = os.getenv("site_url")
LOGIN_URL = os.getenv("login_url")
USERNAME = os.getenv("FILMAZ_USERNAME")
PASSWORD = os.getenv("FILMAZ_PASSWORD")
RUBIKA_TOKEN = os.getenv("rubika_token")


jobs = {}  # job_id -> result


rubikaBot = RubikaBot(RUBIKA_TOKEN)

playwright = None
browser = None
filmazClient = None
chatId = "b0BIr1v0ZDT08d2bfbaabad3c8b45edc"


@asynccontextmanager
async def lifespan(app: FastAPI):
    global playwright, browser, filmazClient, context

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        executable_path=r"./chrome-win64/chrome.exe",
        headless=True,
        args=[
            "--ignore-certificate-errors",
            "--ignore-certificate-errors-spki-list",
            "--disable-features=IsolateOrigins,site-per-process",
        ],
    )

    # ✅ bypass invalid SSL
    context = await browser.new_context(storage_state={}, ignore_https_errors=True)

    filmazClient = FilmazClient(
        rubikaBot,
        context,
        SITE_URL,
        LOGIN_URL,
        USERNAME,
        PASSWORD,
        chat_id=chatId,
        session_path=STATE_FILE,
    )

    yield  # application runs here

    # === shutdown ===
    await context.close()
    await browser.close()
    await playwright.stop()


app = FastAPI(lifespan=lifespan)


@app.get("/title")
async def get_title():
    page = await context.new_page()
    await page.goto(LOGIN_URL)
    title = await page.title()
    await page.close()
    return {"title": title}


@app.get("/login")
async def start_login():
    # asyncio.create_task(filmazClient.do_login())  # run login in background
    # return {"status": "login process started... check Rubika for captcha"}
    result = await filmazClient.login()
    return result


@app.get("/checklogin")
async def checkloing():
    result = await filmazClient.is_logged_in()
    return result


# uvicorn main:app --host 0.0.0.0 --port 5000
@app.get("/")
async def home():
    result = await rubikaBot.send_text_message(chatId, "Hello")
    return result
