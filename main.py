from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging
from filmaz_client import FilmazClient
from pydantic import BaseModel


class CompleteLoginRequest(BaseModel):
    session_id: str
    captcha: str


# Output: 2026-04-25 21:07:32 [ERROR] RubikaBot.get_updates:45 - Invalid JSON from getUpdates
logging.basicConfig(
    filename="log/filmaz.log",
    level=logging.WARNING,  # or DEBUG
    format="%(asctime)s [%(levelname)s] %(name)s.%(funcName)s:%(lineno)d - %(message)s",
)

filmazClient = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global filmazClient
    filmazClient = FilmazClient()
    await filmazClient.initialize()

    yield  # application runs here

    # === shutdown ===
    await filmazClient.shutdown()


app = FastAPI(lifespan=lifespan)


# asyncio.create_task(filmazClient.do_login())  # run login in background
@app.get("/api/auth/login/start")
async def login():
    result = await filmazClient.start_login()
    return result


@app.post("/api/auth/login/complete")
async def complete_login(req: CompleteLoginRequest):
    result = await filmazClient.complete_login(req.session_id, req.captcha)
    return result


# return True or False
@app.get("/api/auth/status")
async def is_loggedin():
    result = await filmazClient.is_logged_in()
    return result


@app.get("/api/movies/search/{movie_title}")
async def search_movie(movie_title: str):
    # [index:name:year:imdb:pageurl]
    result = await filmazClient.search(movie_title)
    return result


@app.get("api/movies/qualities/{pageurl:path}")
async def get_qualities(pageurl: str):
    # [index:quality_name:size:dlink]
    results = await filmazClient.get_qualities(pageurl)
    return results


@app.get("/")
async def api_docs():
    return {
        "status": "success",
        "message": "Filmaz API Documentation",
        "endpoints": {
            "auth": {
                "login_start": "/api/auth/login/start",
                "login_complete": "/api/auth/login/complete",
                "status": "/api/auth/status",
            },
            "movies": {
                "search": "/api/movies/search/{title}",
                "qualities": "/api/movies/qualities/{page_url}",
            },
        },
    }


