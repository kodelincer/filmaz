from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
import logging
from filmaz_client import FilmazClient
from pydantic import BaseModel


class CompleteLoginRequest(BaseModel):
    login_page_id: str
    captcha_answer: str


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
    result = await filmazClient.complete_login(req.login_page_id, req.captcha_answer)
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


@app.get("/api/movies/qualities")
async def get_qualities(pageurl: str = Query(..., description="The movie URL")):
    # [index:quality_name:size:dlink]
    results = await filmazClient.get_qualities(pageurl)
    return results


@app.get("/")
async def api_docs():
    return {"message": "Api docs", "version": "1.0.0"}
