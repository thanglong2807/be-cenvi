import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://portal.easybooks.vn/login")
    page.get_by_role("textbox", name="Tài khoản").click()
    page.get_by_role("textbox", name="Tài khoản").fill("0110211211")
    page.get_by_role("textbox", name="Mật khẩu").click()
    page.get_by_role("textbox", name="Mật khẩu").fill("udP8i7")
    page.get_by_role("button", name="Đăng nhập").click()
    page.get_by_role("button").nth(2).click()
    page.get_by_role("button", name="Đăng nhập").click()
    page.get_by_role("link", name="Quản lý nhân viên").click()
    page.get_by_role("button", name="Thêm").click()
    page.get_by_role("textbox", name="Email đăng nhập (*)").click()
    page.get_by_role("textbox", name="Email đăng nhập (*)").fill("lethanglong2807@gmail.com")
    page.get_by_role("textbox", name="Vị trí công tác").click()
    page.get_by_role("textbox", name="Vị trí công tác").fill("KT")
    page.get_by_role("textbox", name="Họ và tên (*)").click()
    page.get_by_role("textbox", name="Họ và tên (*)").fill("le thang long")
    page.get_by_role("textbox", name="Mật khẩu (*)", exact=True).click()
    page.get_by_role("textbox", name="Mật khẩu (*)", exact=True).fill("123456")
    page.get_by_role("textbox", name="Xác nhận mật khẩu (*)").click()
    page.get_by_role("textbox", name="Xác nhận mật khẩu (*)").fill("123456")
    page.get_by_role("button", name="Lưu").click()
    page.get_by_role("checkbox", name="Chế độ kế toán TT 200/").check()
    page.get_by_role("checkbox", name="Chế độ kế toán TT 133").check()
    page.get_by_role("checkbox", name="Hộ kinh doanh").check()
    page.get_by_role("button", name="Lưu").click()
    page.goto("https://portal.easybooks.vn/quan-ly-nhan-vien")
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
