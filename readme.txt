pip install -r requirements.txt


# “Every time the page sends an HTTP request, run this function.”
        # page.on(...) : This registers an event listener on the page. Think of it like:
        # “When X happens, execute Y.”
        # "request": This event fires every time the browser makes a network request, including:
        # HTML page loads
        # CSS files
        # JS files
        # Images
        # AJAX / fetch calls
        # API calls
        # Form submissions
        # page.on("request", lambda r: print("REQ:", r.method, r.url))

        # This registers an event handler that fires every time the browser receives an HTTP response.
        # page.on("response", lambda r: print("RES:", r.status, r.url))



        # wait until captcha image is loaded
        # cap = page.locator("#imgCap")
        # await cap.wait_for(state="visible")


        # await page.wait_for_url("https://flzios.com/**")
        # await page.screenshot(path="after_login.png", full_page=True)

        # Handle Chrome SSL warning page
        # if await page.locator("#proceed-link").count() > 0:
        #     print("Bypassing SSL warning page...")
        #     await page.click("#details-button") details-button
        #     await page.click("#proceed-link") proceed-link

        # ✅ Take screenshot to verify fields are filled
        # await page.screenshot(path="login_filled.png", full_page=True)

        # mobile_val = await page.locator('input[name="mobile"]').input_value()
        # pass_val = await page.locator('input[name="password"]').input_value()
        # captcha_val = await page.locator('input[name="captcha"]').input_value()

        # print("MOBILE:", mobile_val)
        # print("CAPTCHA:", captcha_val)
        # print("PASS:", pass_val)

        # Because this site does AJAX + redirect, we manually wait for base url
        # await page.wait_for_url("https://flzios.com/**", timeout=15000)

        # <span class="PosAbs DrMenuTxt1">reza(09177245026)</span>
        # await page.locator("span.DrMenuTxt1").wait_for(state="visible")


        browser = await playwright.chromium.launch(
        executable_path=r"C:\Users\wineo\Documents\labs\filmaz\chrome-win64\chrome.exe",
        headless=True,
        args=[
            "--ignore-certificate-errors",
            "--ignore-certificate-errors-spki-list",
            "--disable-features=IsolateOrigins,site-per-process",
        ],
    )


    await page.screenshot(path="redirect_login.png", full_page=True)

     timeout=50000


curl -L \
  -H "Cookie: PHPSESSID=f785943553d06724ba4e774b2b3f5566" \
  -H "Referer: https://flzios.com/" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)" \
  -o file.zip \
  "https://flzios.com/path/to/dlink"

How to Check If It Works
    Run without -o first:    
        curl -I -L -H "Cookie: PHPSESSID=..."

    Look for:
        HTTP/1.1 200 OK
        Content-Type: application/zip
    
    If you see:
        302 Found → redirect (normal)
        403 Forbidden → missing header or invalid session
        401 Unauthorized → login required
        HTML instead of file → probably missing token

    

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




        # saving captcha image
                try:
                    captcha_path = f"tmp/captcha_{tmp_uuid}.png"
                    with open(captcha_path, "wb") as f:
                        f.write(img_bytes)
                except Exception as e:
                    self.logger.error(f"SAVING CAPTCHA Image failed: {e}")
                    return {
                        "status": False,
                        "msg": "",
                        "error": f"saving captcha image failed",
                        "detail": str(e),
                    }


Why browser.new_page() is wrong for you

browser.new_page() creates an INTERNAL temporary context automatically.

Equivalent to:

tmp_context = await browser.new_context()
page = await tmp_context.new_page()

Meaning:

isolated cookies
isolated session
isolated storage


---------
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
----------------
# load saved cookies if they exist
if Path(self.session_path).exists():
    cookies = json.loads(Path(self.session_path).read_text())
    await page.context.add_cookies(cookies)
========
# Optional: Custom 404 handler
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint not found",
            "message": f"Path {request.url.path} does not exist",
            "available_endpoints": "/api",
        },
    )

============
HEADLESS CAPTCHA WARNING

Some captcha systems block:

headless=True

If captcha/login becomes unstable later, test:

headless=False

because many Persian sites detect headless Chrome.

================

# await cap_loc.wait_for(state="attached")
# await cap_loc.wait_for(state="visible")
================
# saving captcha image
try:
    captcha_path = f"./tmp/captcha_{login_page_id}.png"
    with open(captcha_path, "wb") as f:
        f.write(img_bytes)
except Exception as e:
    self.logger.error(f"SAVING CAPTCHA Image failed: {e}")
    return {
        "status": False,
        "msg": "",
        "error": f"saving captcha image failed",
        "detail": str(e),
    }
    =====================SKILLS: download_movie_from_filmaz_website
    1. check /api/auth/status

2. if not logged in:
      call /api/auth/login/start
      get captcha image url
      send image to telegram
      wait for user answer
      call /api/auth/login/complete

3. search movie

4. show indexed movie list to telegram

5. wait user selection

6. get qualities

7. show qualities list

8. wait quality selection

9. extract direct link

10. call downloader tool
============
Interactive Wait State

The skill must:

send captcha to telegram
pause workflow
wait for user response
continue

Then again:

wait for movie selection
continue

Then again:

wait for quality selection

This is called:

conversational workflow
resumable agent flow
human-in-the-loop orchestration

OpenClaw is good for this.
============================= Telegram Flow Example
User:
download movie inception

Telegram Bot:
Checking login status...

Bot:
Login required.
Please solve captcha:
(image sent)

User:
7gHx2

Bot:
Login successful.
Searching movies...

Bot:
1. Inception (2010) IMDb 8.8
2. Inception: The Cobol Job
3. Inception Behind Scenes

Reply with movie number.
User:
1
Bot:
Available qualities:
1. 1080p BluRay - 2.4GB
2. 720p BluRay - 1.1GB
3. 480p - 700MB

Reply with quality number.
User:
2

Bot:
Starting download...

Then OpenClaw downloader tool starts download.
======
Final Recommended OpenClaw Skill Logic

Pseudo flow:

if not logged_in():

    login_data = start_login()

    send captcha image

    captcha_answer = wait_user_message()

    result = complete_login()

    if failed:
         stop

movies = search_movie(title)

send movie list

movie_index = wait_user_message()

qualities = get_qualities(selected_movie)

send quality list

quality_index = wait_user_message()

download_link = selected_quality["url"]

download(download_link)
===========
---
name: movie-downloader
description: download movies from filmaz
---

When user asks to download a movie:

1. Check login:

curl http://127.0.0.1:8000/api/auth/status

2. If not logged in:

curl http://127.0.0.1:8000/api/auth/login/start

3. Extract:
- login_page_id
- captcha_img

4. Send captcha image to user.

5. Ask user for captcha answer.

6. Complete login:

curl -X POST http://127.0.0.1:8000/api/auth/login/complete \
-H "Content-Type: application/json" \
-d '{
  "login_page_id":"...",
  "captcha_answer":"..."
}'

7. Search movie:

curl http://127.0.0.1:8000/api/movies/search/inception

8. Show indexed list to user.

9. Ask for movie index.

10. Get qualities:

curl "http://127.0.0.1:8000/api/movies/qualities?pageurl=..."

11. Ask quality selection.

12. Download selected URL.
============
---
name: filmaz-movie-downloader
description: Search and download movies using Filmaz FastAPI backend
---

You are a movie assistant connected to a FastAPI backend.

When the user asks to download or search a movie:

--------------------------------------------------
STEP 1: CHECK LOGIN
--------------------------------------------------
Call:
http://127.0.0.1:8000/api/auth/status

If not logged in:

--------------------------------------------------
STEP 2: START LOGIN
--------------------------------------------------
Call:
http://127.0.0.1:8000/api/auth/login/start

You will receive:
- login_page_id
- captcha image URL

Send captcha image to Telegram user and ask:
"Please enter captcha"

Wait for user reply.

--------------------------------------------------
STEP 3: COMPLETE LOGIN
--------------------------------------------------
Call:
POST http://127.0.0.1:8000/api/auth/login/complete

Body:
{
  "login_page_id": "...",
  "captcha_answer": "USER_INPUT"
}

If success → continue

--------------------------------------------------
STEP 4: SEARCH MOVIE
--------------------------------------------------
Call:
http://127.0.0.1:8000/api/movies/search/{movie_title}

Show results as indexed list.

Ask user:
"Select movie number"

--------------------------------------------------
STEP 5: GET QUALITIES
--------------------------------------------------
Call:
http://127.0.0.1:8000/api/movies/qualities?pageurl=SELECTED_PAGE

Show available qualities.

Ask user:
"Select quality number"

--------------------------------------------------
STEP 6: DOWNLOAD LINK
--------------------------------------------------
Return selected download URL to downloader tool.
save the movie in dir: 
/home/wineo/dlmovies
==============
goto() already waits for navigation.
Calling wait_for_url() AFTER goto() is usually redundant.
wait_for_url() is mainly useful when:
clicking buttons
form submits
SPA route changes
redirects after actions

NOT after successful goto().
=================================
General Playwright rule

Usually:

goto()
↓
wait_for_url()

is redundant.

Because:

await page.goto(...)

already waits for navigation internally.
When should you use wait_for_url()?

Mostly after user-triggered actions:

click()
submit()
keyboard press
SPA route change
redirect after login

Example:

async with page.expect_navigation():
    await button.click()

or:

await button.click()
await page.wait_for_url("**/dashboard")
Better philosophy for modern websites

DOM-based waits are usually more reliable than URL waits.

GOOD:

await page.locator(".user-panel").wait_for()

LESS reliable:

await page.wait_for_url(...)

because many sites:

use AJAX
don't navigate
use React/Vue/Angular
use history.pushState()
partially render content
====================================

python -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
=============
Install and Configure FastAPI Server Tools
bash
# Install production server (Gunicorn)
pip install gunicorn

# Create a startup script
cat > start_server.sh << 'EOF'
#!/bin/bash
cd ~/filmaz-project
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
EOF

chmod +x start_server.sh

# Create systemd service (for production)
sudo cat > /etc/systemd/system/filmaz-api.service << 'EOF'
[Unit]
Description=Filmaz FastAPI Application
After=network.target

[Service]
User=$USER
WorkingDirectory=/home/$USER/filmaz-project
Environment="PATH=/home/$USER/filmaz-project/venv/bin"
ExecStart=/home/$USER/filmaz-project/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF
============
aria2c \
  --enable-rpc \
  --rpc-listen-all=true \
  --rpc-listen-port=6800 \
  --rpc-secret=AAEaVHsGRadpzvD8v98ERlt5SvETIWZp83c \
  --continue=true \
  --max-connection-per-server=16 \
  --daemon=true

  aria2c --enable-rpc --rpc-listen-all=true --rpc-allow-origin-all=true --rpc-listen-port=6800 --rpc-secret=mytoken

  aria2c \
  --enable-rpc \
  --rpc-listen-all=true \
  --rpc-allow-origin-all=true \
  --max-connection-per-server=16 \
  --continue=true \
  --rpc-listen-port=6800 \
  --rpc-secret=mytoken
  --dir /path/to/output
  --daemon=true

  curl http://localhost:6800/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0",
    "id":"qwer",
    "method":"aria2.addUri",
    "params":["token:mytoken", ["https://example.com/file.iso"]]
  }'

aria2 returns a GID.

Poll progress

Example:

curl http://localhost:6800/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0",
    "id":"qwer",
    "method":"aria2.tellStatus",
    "params":["token:mytoken","GID_HERE"]
  }'

  You get:

completedLength
totalLength
speed
status
eta

{
  "tools": {
    "allow": [
      "exec",
      "process"
    ]
  }
}

You should use process tool too.

Because:

exec starts command
process monitors running background tasks

OpenClaw was specifically designed for this workflow.
=================
The common modern architecture for AI agents is:

User
  ↓
Agent / Orchestrator
  ↓
LLM
  ↓
Tool calling system
  ↓
Tools / APIs / MCP servers / Processes
  ↓
Real world actions