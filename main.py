import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv
import logging


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

STATE_FILE = "config/auth.json"
DOWNLOAD_DIR = "dl_movies"

SITE_URL = os.getenv("site_url")
LOGIN_URL = os.getenv("login_url")
USERNAME = os.getenv("FILMAZ_USERNAME")
PASSWORD = os.getenv("FILMAZ_PASSWORD")

RUBIKA_TOKEN = os.getenv("rubika_token")


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

    rubikaBot.filmaz = filmazClient

    yield  # application runs here

    # === shutdown ===
    await context.close()
    await browser.close()
    await playwright.stop()


app = FastAPI(lifespan=lifespan)


@app.get("/login")
async def start_login():
    # asyncio.create_task(filmazClient.do_login())  # run login in background
    result = await filmazClient.login()
    return result


@app.get("/loggedin")
async def checkloing():
    result = await filmazClient.is_logged_in()
    return result


# here must get a direct link with the session
@app.get("/search")
async def search_movie(q: str):
    # printout list of movie items with [index_name_year]
    result = await filmazClient.search(q)
    return result


# from search items(name,year,pageurl) ,
# select one of them then list the qualities(dlinks) to download
@app.get("/movie_index")
async def movie_index(m_index: int):
    # printout quality items with [index_quality]
    # result = await filmazClient.search(q)
    return ""  # result


@app.get("/quality_index")
async def quality_index(q_index: int):
    # based on quality index get dlink to downlaod the movie
    # dlink = await filmazClient.search(q)
    return ""  # dlink


# if we can attach session to curl of agent so just can
# agent get dlink and session info then download it by itself
@app.get("/dl_without_agent")
async def download_movie(dlink: str):
    result = await filmazClient.download_movie(dlink)
    return result


@app.get("/")
async def home():
    # here explain these tools and functions and input to the agent
    result = await rubikaBot.send_text_message(chatId, "Hello")
    return result
