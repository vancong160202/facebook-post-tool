from __future__ import annotations

import asyncio
import json
import re
import threading
from pathlib import Path
from tkinter import END, LEFT, RIGHT, Button, Entry, Frame, Label, Listbox, Message, StringVar, Text, Tk, filedialog, messagebox
from tkinter.ttk import Progressbar
from urllib.parse import quote_plus

from playwright.async_api import BrowserContext, Page, async_playwright


IMAGE_TYPES = ("*.jpg", "*.jpeg", "*.png", "*.webp")
GROUP_COUNT = 10
MAX_IMAGES = 100
POST_IMAGE_LIMIT = 80
AUTO_START_POSTING = True
PROJECT_IMAGE_FOLDER = "images"
SETTINGS_FILE = ".facebook_post_settings.json"
DEFAULT_GROUPS = (
    "TTCN FC Online - Joyce9999 - Xmen Club",
    "FC ONLINE - FO4 Cộng Đồng Giao Lưu FC Online Việt Nam",
    "FC ONLINE - Chia Sẻ Giờ Reset - Mua Bán Trao Đổi",
    "FC Online - Hội Chợ Giao Lưu Và Trao Đổi FC Online Việt Nam",
    "FC Online FO4 GARENA VIỆT NAM",
    "FC Online - Chia Sẻ Giờ RESET Giá Cầu Thủ",
    "CỘNG ĐỒNG FC ONLINE FO4 GARENA VIỆT",
    "Cộng Đồng FC Online Garena Việt Nam - FO4",
    "Mạnh Cuong Tran FC Online - Giao Lưu & Trao Đổi Về FC Online",
    "FC Online - Chia Sẻ Giờ RESET Giá Cầu Thủ (ex)",
)
GROUP_SEARCH_TERMS = {
    "FC Online FO4 GARENA VIỆT NAM": "FC ONLINE FO4",
    "Mạnh Cuong Tran FC Online - Giao Lưu & Trao Đổi Về FC Online": "Manh Cuong Tran FC Online",
}


class FacebookPostApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("Facebook Auto Posting Tool")
        self.root.geometry("760x760")
        self.root.minsize(680, 680)

        self.image_paths: list[str] = []
        self.settings_path = Path(__file__).resolve().parent / SETTINGS_FILE
        self.image_folder = self._load_saved_image_folder()
        self.group_vars = [StringVar(value=group) for group in DEFAULT_GROUPS]
        self.status_var = StringVar(value="Sẵn sàng")
        self.image_count_var = StringVar(value="Chưa chọn ảnh")

        self._build_ui()
        self.load_project_images()
        if AUTO_START_POSTING:
            self.root.after(1000, self.start_posting)

    def _build_ui(self) -> None:
        Label(self.root, text="Facebook Auto Posting Tool", font=("Segoe UI", 20, "bold")).pack(pady=(18, 4))
        Message(
            self.root,
            text="Tạo một bài duy nhất gồm tối đa 80 ảnh và chia sẻ vào 1 group chính cùng 9 group thêm.",
            width=650,
            font=("Segoe UI", 10),
        ).pack(pady=(0, 16))

        image_frame = Frame(self.root)
        image_frame.pack(fill="x", padx=24)
        Label(image_frame, text="1. Hình ảnh", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        Button(image_frame, text="Chọn hình ảnh", command=self.choose_images).pack(side=LEFT, pady=8)
        Button(image_frame, text="Chọn folder ảnh 1-80", command=self.choose_image_folder).pack(side=LEFT, padx=(8, 0), pady=8)
        Button(image_frame, text="Chọn folder Dropbox", command=self.choose_dropbox_folder).pack(side=LEFT, padx=(8, 0), pady=8)
        Button(image_frame, text="Nạp lại folder ảnh", command=self.load_project_images).pack(side=LEFT, padx=(8, 0), pady=8)
        Label(image_frame, textvariable=self.image_count_var, fg="#555").pack(side=LEFT, padx=12)

        self.image_list = Listbox(image_frame, height=5, width=88)
        self.image_list.pack(fill="x", pady=(0, 14))

        Label(self.root, text="2. Caption", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=24)
        self.caption = Text(self.root, height=5, wrap="word", font=("Segoe UI", 10))
        self.caption.pack(fill="x", padx=24, pady=(8, 14))
        self.caption.insert("1.0", "Tặng ae ít đồ cổ sưu tầm 💥💥")

        Label(self.root, text="3. Facebook Group", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=24)
        Message(
            self.root,
            text="Nhập tên group giống hoặc gần giống tên hiển thị trên Facebook. Dòng 1 là group chính; 9 dòng dưới là các group thêm.",
            width=680,
            font=("Segoe UI", 9),
        ).pack(anchor="w", padx=24, pady=(2, 6))

        group_frame = Frame(self.root)
        group_frame.pack(fill="x", padx=24)
        for index, group_var in enumerate(self.group_vars, start=1):
            Label(group_frame, text=f"{index:02d}", width=4, anchor="e").grid(row=index - 1, column=0, padx=(0, 8), pady=2)
            Entry(group_frame, textvariable=group_var, width=70).grid(row=index - 1, column=1, sticky="ew", pady=2)
        group_frame.columnconfigure(1, weight=1)

        bottom = Frame(self.root)
        bottom.pack(fill="x", padx=24, pady=18)
        self.progress = Progressbar(bottom, mode="indeterminate")
        self.progress.pack(fill="x", pady=(0, 8))
        Label(bottom, textvariable=self.status_var, anchor="w", fg="#555").pack(side=LEFT)
        Button(bottom, text="Mở Facebook và đăng bài", command=self.start_posting).pack(side=RIGHT)

    def choose_images(self) -> None:
        selected = filedialog.askopenfilenames(
            title="Chọn tối đa 80 hình ảnh",
            filetypes=[("Hình ảnh", " ".join(IMAGE_TYPES)), ("Tất cả file", "*.*")],
        )
        if not selected:
            return
        if len(selected) > MAX_IMAGES:
            messagebox.showerror("Quá nhiều ảnh", f"Bạn đã chọn {len(selected)} ảnh. Vui lòng chọn tối đa {MAX_IMAGES} ảnh.")
            return
        self.image_paths = list(selected)
        self.image_list.delete(0, END)
        for path in self.image_paths[:5]:
            self.image_list.insert(END, Path(path).name)
        if len(self.image_paths) > 5:
            self.image_list.insert(END, f"... và {len(self.image_paths) - 5} ảnh khác")
        self.image_count_var.set(f"Đã chọn {len(self.image_paths)}/{MAX_IMAGES} ảnh")

    def choose_image_folder(self) -> None:
        folder = filedialog.askdirectory(title="Chọn folder chứa ảnh số 1 đến 80")
        if not folder:
            return

        image_extensions = {".jpg", ".jpeg", ".png", ".webp"}
        numbered_images: dict[int, str] = {}
        for path in Path(folder).iterdir():
            if not path.is_file() or path.suffix.lower() not in image_extensions:
                continue
            if not path.stem.isdigit():
                continue
            number = int(path.stem)
            if 1 <= number <= MAX_IMAGES:
                numbered_images[number] = str(path)

        expected_numbers = set(range(1, MAX_IMAGES + 1))
        actual_numbers = set(numbered_images)
        if actual_numbers != expected_numbers:
            missing = sorted(expected_numbers - actual_numbers)
            messagebox.showerror(
                "Folder ảnh chưa đúng",
                "Folder phải có đủ ảnh đánh số từ 1 đến 80. "
                f"Ảnh còn thiếu: {', '.join(map(str, missing)) or 'không có'}",
            )
            return

        self.image_paths = [numbered_images[number] for number in range(1, MAX_IMAGES + 1)]
        self.image_list.delete(0, END)
        for path in self.image_paths[:5]:
            self.image_list.insert(END, Path(path).name)
        self.image_list.insert(END, "... và 75 ảnh khác")
        self.image_count_var.set("Đã tự chọn đủ 80 ảnh theo thứ tự 1-80")

    def load_project_images(self) -> None:
        folder = self.image_folder
        if not folder.exists():
            folder = Path(__file__).resolve().parent / PROJECT_IMAGE_FOLDER
        image_extensions = {".jpg", ".jpeg", ".png", ".webp"}
        available_images = {
            path.name.casefold(): path
            for path in folder.iterdir()
            if path.is_file() and path.suffix.lower() in image_extensions
        }
        order_file = folder / "order.txt"
        ordered_paths: list[Path] = []
        listed_names: set[str] = set()
        if order_file.exists():
            for line in order_file.read_text(encoding="utf-8-sig").splitlines():
                filename = line.strip()
                if not filename or filename.startswith("#"):
                    continue
                key = Path(filename).name.casefold()
                if key in available_images and key not in listed_names:
                    ordered_paths.append(available_images[key])
                    listed_names.add(key)

        remaining_paths = sorted(
            (path for key, path in available_images.items() if key not in listed_names),
            key=lambda path: path.name.casefold(),
        )
        image_paths = ordered_paths + remaining_paths
        if len(image_paths) > MAX_IMAGES:
            messagebox.showerror(
                "Quá nhiều ảnh",
                f"Folder đang có {len(image_paths)} ảnh. Facebook chỉ cho tối đa {MAX_IMAGES} ảnh mỗi bài.",
            )
            return
        self.image_paths = [str(path) for path in image_paths[:POST_IMAGE_LIMIT]]
        self.image_list.delete(0, END)
        for path in self.image_paths[:5]:
            self.image_list.insert(END, Path(path).name)
        if len(self.image_paths) > 5:
            self.image_list.insert(END, f"... và {len(self.image_paths) - 5} ảnh khác")
        self.image_count_var.set(
            f"Đã nạp {len(self.image_paths)}/{POST_IMAGE_LIMIT} ảnh từ {folder.name}"
            if self.image_paths
            else f"Folder {folder} chưa có ảnh"
        )

    def choose_dropbox_folder(self) -> None:
        folder = filedialog.askdirectory(title="Chọn folder ảnh Dropbox đã đồng bộ trên laptop")
        if not folder:
            return
        self.image_folder = Path(folder)
        self.settings_path.write_text(
            json.dumps({"image_folder": str(self.image_folder)}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.load_project_images()

    def _load_saved_image_folder(self) -> Path:
        if self.settings_path.exists():
            try:
                settings = json.loads(self.settings_path.read_text(encoding="utf-8"))
                saved_folder = Path(settings.get("image_folder", ""))
                if saved_folder.exists():
                    return saved_folder
            except (OSError, TypeError, ValueError):
                pass
        return Path(__file__).resolve().parent / PROJECT_IMAGE_FOLDER

    def start_posting(self) -> None:
        self.load_project_images()
        caption = self.caption.get("1.0", END).strip()
        groups = [group.get().strip() for group in self.group_vars]
        if not 1 <= len(self.image_paths) <= POST_IMAGE_LIMIT:
            messagebox.showwarning(
                "Số lượng ảnh không hợp lệ",
                f"Folder Dropbox cần có từ 1 đến {POST_IMAGE_LIMIT} ảnh. Hiện có {len(self.image_paths)} ảnh.",
            )
            return
        if not caption:
            messagebox.showwarning("Thiếu caption", "Vui lòng nhập caption.")
            return
        if not groups[0] or any(not group for group in groups[1:]):
            messagebox.showwarning("Thiếu group", "Vui lòng nhập đủ 1 group chính và 9 group thêm.")
            return

        self.progress.start(10)
        self.status_var.set("Đang mở Chrome...")
        threading.Thread(target=self._run_browser, args=(caption, groups), daemon=True).start()

    def _run_browser(self, caption: str, groups: list[str]) -> None:
        try:
            asyncio.run(self._post_to_facebook(caption, groups))
        except Exception as error:  # noqa: BLE001
            self.root.after(0, self._finish_with_error, str(error))

    async def _post_to_facebook(self, caption: str, groups: list[str]) -> None:
        profile_dir = Path(__file__).resolve().parent / "chrome-profile"
        async with async_playwright() as playwright:
            context = await playwright.chromium.launch_persistent_context(
                str(profile_dir),
                channel="chrome",
                headless=False,
                args=["--start-maximized"],
            )
            try:
                page = context.pages[0] if context.pages else await context.new_page()
                await page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
                await page.wait_for_timeout(3000)
                self._set_status("Chrome đã mở. Đang kiểm tra Facebook...")
                await self._wait_for_login(page)
                await self._dismiss_optional_dialogs(page)
                await self._open_group(page, groups[0])
                await self._create_post(page, caption, groups)
                self._set_status("Đã xác nhận bài đăng hoàn tất.")
                self.root.after(0, lambda: messagebox.showinfo("Hoàn tất", "Đã xác nhận bài viết đăng thành công trên group."))
            finally:
                pass

    async def _wait_for_login(self, page: Page) -> None:
        if not await self._needs_facebook_auth(page):
            return

        self._set_status("Vui lòng đăng nhập và hoàn tất xác minh 2 bước trong Chrome...")
        for _ in range(600):
            if not await self._needs_facebook_auth(page):
                return
            await page.wait_for_timeout(1000)
        raise RuntimeError("Hết thời gian chờ đăng nhập/xác minh Facebook. Hãy hoàn tất trong Chrome rồi chạy lại tool.")

    async def _needs_facebook_auth(self, page: Page) -> bool:
        url = page.url.lower()
        auth_paths = ("login", "two_step_verification", "checkpoint", "security_check", "challenge")
        return any(path in url for path in auth_paths) or await self._login_form_visible(page)

    async def _login_form_visible(self, page: Page) -> bool:
        selectors = (
            'input[name="email"]',
            'input[name="pass"]',
            'input[type="password"]',
            'button[name="login"]',
        )
        for selector in selectors:
            if await page.locator(selector).first.is_visible():
                return True
        return False

    async def _create_post(self, page: Page, caption: str, groups: list[str]) -> None:
        self._set_status("Đang mở bài viết trong group chính...")
        await self._click_create_post(page)
        await page.wait_for_timeout(1000)

        self._set_status(f"Đang tải {len(self.image_paths)} ảnh...")
        file_input = page.locator('input[type="file"]').last
        await file_input.set_input_files(self.image_paths)
        await page.wait_for_timeout(2000)

        self._set_status("Đang chọn group chính và 9 group phụ...")
        await self._click_group_selector(page)
        for group in groups[1:]:
            search = page.locator(
                'input[placeholder="Tìm kiếm nhóm"], input[placeholder="Search groups"]'
            ).last
            await search.wait_for(state="visible", timeout=30000)
            await search.fill(GROUP_SEARCH_TERMS.get(group, group))
            await page.wait_for_timeout(700)
            await self._select_group_result(page, group, GROUP_SEARCH_TERMS.get(group, group))
        await self._click_first_visible(page, ("Xong", "Done"), "nút xác nhận chọn group")
        self._set_status("Đang nhập caption lần cuối trước khi đăng...")
        composer = await self._caption_editor(page)
        if composer is None:
            raise RuntimeError("Không tìm thấy lại ô caption sau khi chọn group.")
        await composer.click()
        await composer.fill(caption)
        typed_caption = await composer.inner_text()
        if caption not in typed_caption:
            await composer.press("Control+A")
            await composer.insert_text(caption)
            typed_caption = await composer.inner_text()
        if caption not in typed_caption:
            raise RuntimeError("Caption chưa được ghi vào bài ngay trước khi đăng, nên tool đã dừng.")
        await self._click_post_button(page)
        try:
            await page.wait_for_timeout(1500)
            if await composer.is_visible() and not (await composer.inner_text()).strip():
                await self._close_empty_composer(page)
        except Exception as error:  # noqa: BLE001
            raise RuntimeError(
                "Đã bấm Đăng nhưng chưa xử lý được popup sau khi gửi. Chrome vẫn được giữ mở để kiểm tra."
            ) from error
        await self._wait_for_post_confirmation(page, caption)

    async def _wait_for_post_confirmation(self, page: Page, caption: str) -> None:
        self._set_status("Đang chờ Facebook xử lý ảnh và kiểm tra bài đã lên...")
        await self._wait_until_posting_finishes(page)
        await page.wait_for_timeout(3000)
        editor = await self._caption_editor(page)
        if editor is not None and await editor.is_visible():
            raise RuntimeError(
                "Đăng bài thành công!"
            )

        matches = page.get_by_text(caption, exact=True)
        for index in range(await matches.count()):
            if await matches.nth(index).is_visible():
                return
        raise RuntimeError(
            "Facebook đã xử lý xong nhưng không tìm thấy caption trên bài đăng. "
            "Có thể bài đã đăng trắng; tool không báo thành công và giữ Chrome mở để kiểm tra."
        )

    async def _wait_until_posting_finishes(self, page: Page) -> None:
        posting_labels = ("Đang đăng", "Posting", "Đang tải lên", "Uploading")
        while True:
            posting_visible = False
            for label in posting_labels:
                matches = page.get_by_text(label, exact=True)
                for index in range(await matches.count()):
                    if await matches.nth(index).is_visible():
                        posting_visible = True
                        break
                if posting_visible:
                    break
            if not posting_visible:
                return
            await page.wait_for_timeout(2000)

    async def _close_empty_composer(self, page: Page) -> None:
        close_candidates = (
            page.locator('[aria-label="Đóng"]').last,
            page.locator('[aria-label="Close"]').last,
            page.get_by_role("button", name=re.compile(r"Đóng|Close", re.I)).last,
        )
        for candidate in close_candidates:
            if await candidate.is_visible():
                await candidate.click(timeout=10000)
                await page.wait_for_timeout(1000)
                return

    async def _caption_editor(self, page: Page):
        caption_selectors = (
            '[contenteditable="true"][aria-label*="Bạn viết"]',
            '[contenteditable="true"][aria-label*="What\'s on your mind"]',
            '[contenteditable="true"][data-placeholder*="Bạn viết"]',
            '[contenteditable="true"][data-placeholder*="What\'s on your mind"]',
        )
        for selector in caption_selectors:
            editors = page.locator(selector)
            for index in range(await editors.count() - 1, -1, -1):
                editor = editors.nth(index)
                if await editor.is_visible():
                    return editor

        editors = page.locator('[contenteditable="true"]')
        for index in range(await editors.count()):
            editor = editors.nth(await editors.count() - index - 1)
            if await editor.is_visible():
                return editor
        return None

    async def _click_post_button(self, page: Page) -> None:
        labels = re.compile(r"^Đăng$|^Post$", re.I)
        for _ in range(60):
            candidates = (
                page.get_by_role("button", name=labels).last,
                page.locator('button').filter(has_text=labels).last,
            )
            for candidate in candidates:
                if await candidate.is_visible() and await candidate.is_enabled():
                    await candidate.click(timeout=10000)
                    return
            await page.wait_for_timeout(1000)
        raise RuntimeError(
            "Không tìm thấy nút Đăng đang hoạt động sau khi chọn group. "
            f"URL hiện tại: {page.url}"
        )

    async def _select_group_result(self, page: Page, group: str, search_term: str) -> None:
        result = await self._visible_text_match(page, group)
        if result is None:
            result = await self._visible_text_match(page, group.split(" - ")[0])
        if result is None:
            result = await self._visible_text_match(page, search_term)
        if result is None:
            raise RuntimeError(f"Không thấy kết quả group '{group}' sau khi search '{search_term}'.")
        await result.scroll_into_view_if_needed()

        row = result.locator(
            "xpath=ancestor::*[.//*[@role='checkbox'] or .//*[@aria-checked] or .//input[@type='checkbox']][1]"
        )
        if await row.count() and await row.is_visible():
            checkbox = row.locator("[role='checkbox'], [aria-checked], input[type='checkbox']").last
            if await checkbox.count() and await checkbox.is_visible():
                await checkbox.click(timeout=10000)
                return

        result_box = await result.bounding_box()
        if result_box:
            checkbox_candidates = page.locator("[role='checkbox'], [aria-checked], input[type='checkbox']")
            nearest = None
            nearest_distance = float("inf")
            for index in range(await checkbox_candidates.count()):
                candidate = checkbox_candidates.nth(index)
                if not await candidate.is_visible():
                    continue
                box = await candidate.bounding_box()
                if not box or box["x"] <= result_box["x"]:
                    continue
                distance = abs((box["y"] + box["height"] / 2) - (result_box["y"] + result_box["height"] / 2))
                if distance < nearest_distance:
                    nearest = candidate
                    nearest_distance = distance
            if nearest is not None and nearest_distance < 80:
                await nearest.click(timeout=10000)
                return

            search_box = await page.locator(
                'input[placeholder="Tìm kiếm nhóm"], input[placeholder="Search groups"]'
            ).last.bounding_box()
            if search_box:
                await page.mouse.click(
                    search_box["x"] + search_box["width"] - 35,
                    result_box["y"] + result_box["height"] / 2,
                )
                await page.wait_for_timeout(500)
                return

            row_box = await result.evaluate(
                """element => {
                    const textRect = element.getBoundingClientRect();
                    let current = element.parentElement;
                    while (current) {
                        const rect = current.getBoundingClientRect();
                        if (rect.width > textRect.width * 1.5 && rect.height >= 30 && rect.height <= 110) {
                            return {x: rect.x, y: rect.y, width: rect.width, height: rect.height};
                        }
                        current = current.parentElement;
                    }
                    return null;
                }"""
            )
            if row_box:
                await page.mouse.click(
                    row_box["x"] + row_box["width"] - 28,
                    row_box["y"] + row_box["height"] / 2,
                )
                return
        raise RuntimeError(f"Tìm thấy group '{group}' nhưng không tìm thấy ô checkbox để chọn.")

    async def _visible_text_match(self, page: Page, text: str):
        exact_candidates = page.get_by_text(text, exact=True)
        for index in range(await exact_candidates.count()):
            candidate = exact_candidates.nth(index)
            if await candidate.is_visible():
                return candidate

        candidates = page.get_by_text(re.compile(re.escape(text), re.I))
        for index in range(await candidates.count()):
            candidate = candidates.nth(index)
            if await candidate.is_visible():
                return candidate
        return None

    async def _click_group_selector(self, page: Page) -> None:
        labels = re.compile(
            r"Thêm nhóm|Add group|Đăng vào nhóm|Post to group|Chọn nhóm|Choose group|Share to groups",
            re.I,
        )
        for _ in range(60):
            candidates = (
                page.locator('button:has-text("Thêm nhóm")').last,
                page.locator('[role="button"]:has-text("Thêm nhóm")').last,
                page.get_by_text("Thêm nhóm", exact=True).last,
                page.get_by_role("button", name=labels).last,
                page.get_by_text(labels).last,
                page.locator('[role="button"]').filter(has_text=labels).last,
                page.locator('[aria-label]').filter(has_text=labels).last,
            )
            for candidate in candidates:
                if await candidate.is_visible():
                    await candidate.scroll_into_view_if_needed()
                    await candidate.click(timeout=10000)
                    return
            await page.wait_for_timeout(1000)
        raise RuntimeError(
            "Không tìm thấy bộ chọn group trong màn hình tạo bài. Facebook không cung cấp tính năng đăng nhiều group "
            f"cho giao diện/tài khoản này. URL hiện tại: {page.url}"
        )

    async def _open_group(self, page: Page, group_name: str) -> None:
        self._set_status(f"Đang mở group chính: {group_name}")
        search_url = f"https://www.facebook.com/search/groups/?q={quote_plus(group_name)}"
        await page.goto(search_url, wait_until="domcontentloaded")
        await page.wait_for_timeout(2500)

        group_link = page.get_by_role("link", name=group_name, exact=True).first
        if not await group_link.is_visible():
            group_link = page.get_by_text(group_name, exact=True).first
        if not await group_link.is_visible():
            raise RuntimeError(
                f"Không tìm thấy group chính '{group_name}' trong kết quả Facebook. "
                "Hãy kiểm tra lại tên group hoặc mở group đó trong Chrome trước."
            )
        await group_link.click(timeout=30000)
        await page.wait_for_timeout(2500)
        if "/groups/" not in page.url.lower():
            raise RuntimeError(f"Chưa vào được group chính '{group_name}'. URL hiện tại: {page.url}")

    async def _dismiss_optional_dialogs(self, page: Page) -> None:
        for label in ("Không phải bây giờ", "Not now", "Đóng", "Close"):
            candidate = page.get_by_text(label, exact=True).last
            if await candidate.is_visible():
                try:
                    await candidate.click(timeout=3000)
                    await page.wait_for_timeout(500)
                except Exception:  # noqa: BLE001
                    pass

    async def _click_create_post(self, page: Page) -> None:
        labels = re.compile(
            r"Tạo bài viết|Create post|Bạn đang nghĩ gì|Bạn viết gì đi|What's on your mind|Viết bài",
            re.I,
        )
        for _ in range(60):
            candidates = (
                page.get_by_role("button", name=labels).last,
                page.locator('[role="button"]').filter(has_text=labels).last,
                page.locator('[aria-label*="Tạo bài viết"]').last,
                page.locator('[aria-label*="Create post"]').last,
            )
            for candidate in candidates:
                if await candidate.is_visible():
                    await candidate.scroll_into_view_if_needed()
                    await candidate.click(timeout=10000)
                    return
            await page.wait_for_timeout(1000)
        raise RuntimeError(
            "Không tìm thấy nút mở khung tạo bài viết sau khi đã đóng hộp thoại phụ. "
            f"URL hiện tại: {page.url}"
        )

    async def _click_first_visible(self, page: Page, labels: tuple[str, ...], description: str) -> None:
        for label in labels:
            candidate = page.get_by_text(label, exact=True).last
            if await candidate.is_visible():
                await candidate.click(timeout=30000)
                return
        raise RuntimeError(
            f"Không tìm thấy {description}. Facebook có thể đang ở màn hình khác hoặc giao diện đã thay đổi. "
            f"URL hiện tại: {page.url}"
        )

    def _set_status(self, text: str) -> None:
        self.root.after(0, lambda: self.status_var.set(text))

    def _finish_with_error(self, error: str) -> None:
        self.progress.stop()
        self.status_var.set("Có lỗi, Chrome đã dừng.")
        messagebox.showerror("Không thể hoàn tất", error)


if __name__ == "__main__":
    app_root = Tk()
    FacebookPostApp(app_root)
    app_root.mainloop()