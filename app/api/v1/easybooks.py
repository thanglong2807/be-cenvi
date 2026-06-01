import os
import asyncio
import traceback
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

router = APIRouter(prefix="/easybooks", tags=["EasyBooks"])

BASE     = os.getenv("EASYBOOKS_URL",      "https://portal.easybooks.vn")
EB_USER  = os.getenv("EASYBOOKS_USERNAME", "")
EB_PASS  = os.getenv("EASYBOOKS_PASSWORD", "")
HEADLESS = os.getenv("DOCKER", "false").lower() == "true"


class CreateAccountPayload(BaseModel):
    email: str
    full_name: str
    job: str
    password: str


def _angular_fill(locator, value: str) -> None:
    """Fill input trong Angular app: click → clear → gõ từng ký tự để trigger đúng events."""
    locator.click()
    locator.select_text()
    locator.press_sequentially(value, delay=60)
    locator.press("Tab")  # blur để trigger validation


def _run_automation(email: str, full_name: str, job: str, password: str) -> str:
    import os, time
    step = "khởi động"
    os.makedirs("static/videos", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS, slow_mo=200)
        context = browser.new_context(
            record_video_dir="static/videos/",
            record_video_size={"width": 1280, "height": 800},
        )
        page = context.new_page()
        try:
            # ── Bước 1: Đăng nhập ────────────────────────────────────────────
            step = "mở trang đăng nhập"
            page.goto(f"{BASE}/login")
            page.wait_for_load_state("load", timeout=15000)

            step = "nhập tài khoản"
            user_input = page.get_by_role("textbox", name="Tài khoản")
            user_input.wait_for(state="visible", timeout=10000)
            user_input.fill(EB_USER)

            step = "nhập mật khẩu"
            pass_input = page.get_by_role("textbox", name="Mật khẩu")
            pass_input.wait_for(state="visible", timeout=5000)
            pass_input.fill(EB_PASS)

            step = "bấm Đăng nhập (bước 1)"
            login_btn = page.get_by_role("button", name="Đăng nhập")
            login_btn.wait_for(state="visible", timeout=5000)
            login_btn.click()

            # ── Bước 2: Chờ sau login — tự phát hiện có cần chọn công ty không
            step = "chờ sau đăng nhập"
            page.wait_for_load_state("load", timeout=15000)
            page.wait_for_timeout(3000)
            page.screenshot(path="static/eb_step2_after_login.png")

            # Nếu có trang chọn công ty (có button/element chứa text KTDV) thì chọn
            ktdv_el = page.locator("*", has_text="KTDV").first
            if ktdv_el.is_visible():
                step = "chọn công ty KTDV"
                ktdv_el.click()
                # Xác nhận đăng nhập công ty nếu có popup
                try:
                    confirm_btn = page.get_by_role("button", name="Đăng nhập")
                    confirm_btn.wait_for(state="visible", timeout=5000)
                    confirm_btn.click()
                    page.wait_for_load_state("load", timeout=15000)
                    page.wait_for_timeout(2000)
                except PWTimeout:
                    pass
            else:
                print("[INFO] Không có trang chọn công ty, đã vào dashboard trực tiếp")

            # ── Bước 4: Vào Quản lý nhân viên ────────────────────────────────
            step = "click link Quản lý nhân viên"
            qln_link = page.get_by_role("link", name="Quản lý nhân viên")
            # Nếu link chưa visible, thử mở menu cha (Hệ thống / Cài đặt)
            try:
                qln_link.wait_for(state="visible", timeout=10000)
            except PWTimeout:
                for parent_name in ["Hệ thống", "Cài đặt", "Quản lý"]:
                    try:
                        parent = page.get_by_role("link", name=parent_name).first
                        if parent.is_visible():
                            parent.click()
                            qln_link.wait_for(state="visible", timeout=8000)
                            break
                    except PWTimeout:
                        continue
            qln_link.scroll_into_view_if_needed()
            qln_link.click(timeout=10000)
            # Chờ trang Quản lý nhân viên render — đợi nút Thêm thay vì networkidle
            page.wait_for_load_state("load", timeout=15000)

            # ── Bước 5: Bấm Thêm — chờ trang list render xong ────────────────
            step = "click nút Thêm"
            them = page.get_by_role("button", name="Thêm")
            them.wait_for(state="visible", timeout=15000)
            them.click()

            # Chờ form mở hoàn toàn (email input xuất hiện là dấu hiệu form ready)
            step = "chờ form mở"
            email_input = page.get_by_role("textbox", name="Email đăng nhập (*)")
            email_input.wait_for(state="visible", timeout=10000)
            page.screenshot(path="static/eb_step5_them.png")

            # ── Bước 6: Tick 3 checkbox ───────────────────────────────────────
            step = "tick checkbox TT 200"
            cb1 = page.get_by_role("checkbox", name="Chế độ kế toán TT 200/")
            cb1.wait_for(state="visible", timeout=5000)
            cb1.check()

            step = "tick checkbox TT 133"
            page.get_by_role("checkbox", name="Chế độ kế toán TT 133").check()

            step = "tick checkbox Hộ kinh doanh"
            page.get_by_role("checkbox", name="Hộ kinh doanh").check()
            page.screenshot(path="static/eb_step6_checkbox.png")

            # ── Bước 7: Điền form ─────────────────────────────────────────────
            step = "điền email đăng nhập"
            _angular_fill(email_input, email)

            step = "điền vị trí công tác"
            _angular_fill(page.get_by_role("textbox", name="Vị trí công tác"), job)

            step = "điền họ và tên"
            _angular_fill(page.get_by_role("textbox", name="Họ và tên (*)"), full_name)

            step = "điền mật khẩu"
            _angular_fill(page.get_by_role("textbox", name="Mật khẩu (*)", exact=True), password)

            step = "điền xác nhận mật khẩu"
            _angular_fill(page.get_by_role("textbox", name="Xác nhận mật khẩu (*)"), password)

            page.wait_for_timeout(500)
            page.screenshot(path="static/eb_step7_form.png")

            # ── Bước 8: Lưu ──────────────────────────────────────────────────
            step = "click Lưu"
            luu = page.get_by_role("button", name="Lưu")
            luu.wait_for(state="visible", timeout=5000)
            luu.click(timeout=10000)

            # ── Bước 9: Chờ phản hồi sau Lưu ────────────────────────────────
            step = "kiểm tra kết quả"
            # Chờ 3s rồi kiểm tra form đã đóng chưa (form đóng = thành công)
            page.wait_for_timeout(3000)
            email_field = page.get_by_role("textbox", name="Email đăng nhập (*)")
            if not email_field.is_visible():
                return "Tạo tài khoản thành công"

            # Form chưa đóng sau 3s — chờ thêm tối đa 7s nữa
            try:
                email_field.wait_for(state="hidden", timeout=7000)
                return "Tạo tài khoản thành công"
            except PWTimeout:
                pass

            page.screenshot(path="static/eb_step9_result.png")

            # Form vẫn mở sau 10s — kiểm tra toast lỗi
            result_info = page.evaluate("""() => {
                const results = []
                const notifiers = document.querySelectorAll(
                    '.toast-message, .toast-title, .alert:not(button), ' +
                    '[role="alert"], [role="status"], ' +
                    '.swal2-title, .swal2-html-container, ' +
                    '.notification-message, .msg-text'
                )
                notifiers.forEach(el => {
                    if (['BUTTON','A','INPUT'].includes(el.tagName)) return
                    const t = el.innerText?.trim()
                    if (t && t.length > 2) results.push({ tag: el.tagName, cls: el.className, text: t })
                })
                if (results.length === 0) {
                    document.querySelectorAll('[class*="error"]:not(button), [class*="invalid"]:not(button), .text-danger').forEach(el => {
                        const t = el.innerText?.trim()
                        if (t && t.length > 2) results.push({ tag: el.tagName, cls: el.className, text: t })
                    })
                }
                return results
            }""")
            print("[DEBUG] Thông báo sau Lưu:", result_info)

            all_texts = " ".join([r.get("text", "").lower() for r in result_info]) if result_info else ""
            error_keywords   = ["thất bại", "lỗi", "không hợp lệ", "đã tồn tại", "error", "invalid", "failed", "exist"]
            success_keywords = ["thành công", "success", "đã tạo", "hoàn thành"]

            if any(k in all_texts for k in error_keywords):
                detail = " | ".join([r.get("text", "") for r in result_info])
                raise RuntimeError(f"EasyBooks báo lỗi: {detail}")

            if any(k in all_texts for k in success_keywords):
                return " | ".join([r.get("text", "") for r in result_info if r.get("text")])

            # Vẫn không có tín hiệu rõ ràng — kiểm tra form còn mở không
            form_still_open = email_field.is_visible()
            if form_still_open:
                # Form vẫn còn => có thể lỗi validation chưa hiển thị toast
                # Lấy toàn bộ text trong form để debug
                form_text = page.evaluate("() => document.querySelector('form, .modal, .panel')?.innerText?.trim() || ''")
                print("[DEBUG] Form text:", form_text[:500])
                raise RuntimeError(f"Form vẫn còn mở sau Lưu — có thể lỗi validation. Form text: {form_text[:200]}")

            return "Tạo tài khoản thành công"

        except PWTimeout as e:
            page.screenshot(path="static/eb_error.png")
            raise RuntimeError(f"[Timeout] Bước '{step}': {e}") from e
        except Exception as e:
            try:
                page.screenshot(path="static/eb_error.png")
            except Exception:
                pass
            raise RuntimeError(f"[Lỗi] Bước '{step}': {e}") from e
        finally:
            video_path = page.video.path() if page.video else None
            context.close()  # video được lưu khi context đóng
            browser.close()
            if video_path:
                # Đổi tên video thành tên cố định để dễ xem
                import shutil
                dest = "static/videos/last_session.webm"
                try:
                    shutil.move(video_path, dest)
                    print(f"[VIDEO] Xem tại /static/videos/last_session.webm")
                except Exception:
                    pass


@router.post("/create-account")
async def create_easybooks_account(payload: CreateAccountPayload):
    try:
        msg = await asyncio.to_thread(
            _run_automation,
            payload.email,
            payload.full_name,
            payload.job,
            payload.password,
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    return {"success": True, "message": msg or "Tạo tài khoản EasyBooks thành công"}
