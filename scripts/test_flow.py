import os, sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ['DOCKER'] = 'false'
os.environ['EASYBOOKS_URL'] = 'https://portal.easybooks.vn'
os.environ['EASYBOOKS_USERNAME'] = '0110211211'
os.environ['EASYBOOKS_PASSWORD'] = 'udP8i7'
os.makedirs('static/videos', exist_ok=True)

from playwright.sync_api import sync_playwright

BASE    = 'https://portal.easybooks.vn'
EB_USER = '0110211211'
EB_PASS = 'udP8i7'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=500)
    context = browser.new_context()
    page = context.new_page()

    # Bước 1: Login
    page.goto(f"{BASE}/login")
    page.get_by_role("textbox", name="Tài khoản").fill(EB_USER)
    page.get_by_role("textbox", name="Mật khẩu").fill(EB_PASS)
    page.get_by_role("button", name="Đăng nhập").click()

    print(">>> Đã click Đăng nhập. Browser đang mở.")
    print(">>> Hãy quan sát trang và tương tác thủ công.")
    print(">>> Khi xong nhấn Enter để đóng browser.")

    # Dừng tại đây — user tự thao tác trên browser
    page.wait_for_load_state("load", timeout=15000)
    print(f">>> URL sau login: {page.url}")

    # Giữ browser mở để user quan sát
    input("\nNhấn Enter để đóng browser...")

    context.close()
    browser.close()
