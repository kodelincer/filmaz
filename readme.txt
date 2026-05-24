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