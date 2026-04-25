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