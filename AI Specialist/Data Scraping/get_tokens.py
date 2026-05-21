import asyncio
from playwright.async_api import async_playwright
import json
import os

async def get_tokens():
    print("Opening browser to automatically fetch tokens...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto("https://batdongsan.com.vn/")
        print("Waiting for Cloudflare validation (if any)...")
        
        # Chờ phần tử xuất hiện để chắc chắn đã vào được trang web
        try:
            await page.wait_for_selector(".js__searchbar", timeout=15000)
            print("Page loaded successfully!")
        except Exception as e:
            print("Timeout waiting for selector, might be blocked by Cloudflare. Trying to fetch anyway...")
            
        # Lấy cookies
        cookies = await context.cookies()
        bds_cookie = next((c['value'] for c in cookies if c['name'] == 'BDS.UMS.Cookie'), None)
        
        # Lấy local storage
        access_token = await page.evaluate("() => localStorage.getItem('userToken')")
        
        # Nếu chưa có trong local storage, thử tìm trong session storage hoặc script variables
        if not access_token:
            access_token = await page.evaluate("() => sessionStorage.getItem('userToken')")
            
        print("---")
        if access_token:
            print(f"[OK] Found AccessToken: {access_token[:50]}...")
        else:
            print("[FAIL] AccessToken not found in storage.")
            
        if bds_cookie:
            print(f"[OK] Found BDS Cookie: {bds_cookie[:50]}...")
        else:
            print("[FAIL] BDS Cookie not found.")
            
        await browser.close()
        
        return access_token, bds_cookie

if __name__ == "__main__":
    asyncio.run(get_tokens())
