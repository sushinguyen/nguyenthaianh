"""
=============================================================================
COMMENT SCRAPER - Bốc tách bình luận tự động từ các trang TMĐT & Mạng xã hội
=============================================================================
Sử dụng Playwright để mở trình duyệt Chrome ảo, tự động cuộn trang,
bấm nút "Xem thêm bình luận" như người thật, sau đó trích xuất toàn bộ text.

Hỗ trợ: Shopee, Tiki, Facebook, TikTok

Cài đặt:
    pip install playwright pandas
    playwright install chromium

Sử dụng:
    python comment_scraper.py --url "https://shopee.vn/..." --platform shopee
    python comment_scraper.py --url "https://tiki.vn/..." --platform tiki
    python comment_scraper.py --url "https://www.facebook.com/..." --platform facebook
    python comment_scraper.py --url "https://www.tiktok.com/..." --platform tiktok
    python comment_scraper.py --url "https://shopee.vn/..." --platform shopee --output results.csv
    python comment_scraper.py --url "https://shopee.vn/..." --platform shopee --max-scrolls 50

Đầu ra mặc định: data.csv
Các cột: stt, ten_tai_khoan, noi_dung, thoi_gian
"""

import argparse
import csv
import json
import random
import time
import re
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional

from playwright.sync_api import sync_playwright, Page, ElementHandle


# =============================================================================
# CẤU HÌNH CHO TỪNG NỀN TẢNG
# =============================================================================

PLATFORM_CONFIG = {
    "shopee": {
        "name": "Shopee",
        # Selector cho khu vực bình luận
        "comment_section": ".product-ratings",
        # Selector cho từng bình luận
        "comment_items": ".shopee-product-rating",
        # Selector cho nội dung bình luận
        "comment_text": ".shopee-product-rating__main-comment, .r4A3wf",
        # Selector cho tên người dùng
        "username": ".shopee-product-rating__author-name, .r4A3wf + div",
        # Selector cho rating (số sao)
        "rating": ".shopee-product-rating__rating",
        # Selector cho thời gian
        "timestamp": ".shopee-product-rating__time, .r4A3wf",
        # Nút "Xem thêm bình luận" hoặc phân trang
        "load_more_buttons": [
            "button.product-ratings__page-next",
            ".shopee-icon-button--right",
            "button:has-text('Trang sau')",
            "button:has-text('Next')",
        ],
        # Nút "Xem thêm" trong từng bình luận (mở rộng text dài)
        "expand_buttons": [
            "button:has-text('Xem thêm')",
            "button:has-text('See more')",
            "a:has-text('Xem thêm')",
        ],
        "wait_selector": ".product-ratings, .product-rating-overview",
        "scroll_target": ".product-ratings",
    },
    "tiki": {
        "name": "Tiki",
        "comment_section": ".review-comment",
        "comment_items": ".review-comment__list .review-comment__item, .style__ReviewCommentItemStyle-sc",
        "comment_text": ".review-comment__content, .review-comment__text",
        "username": ".review-comment__user-name, .review-comment__user-info__name",
        "rating": ".review-comment__rating",
        "timestamp": ".review-comment__created-date",
        "load_more_buttons": [
            "button:has-text('Xem thêm')",
            "button:has-text('Xem thêm đánh giá')",
            ".review-comment__load-more button",
            "a:has-text('Xem thêm nhận xét')",
            "p:has-text('Xem thêm')",
        ],
        "expand_buttons": [
            "span:has-text('Xem thêm')",
            "a:has-text('Xem thêm')",
        ],
        "wait_selector": ".review-comment, .customer-reviews",
        "scroll_target": ".review-comment, .customer-reviews",
    },
    "facebook": {
        "name": "Facebook",
        "comment_section": "[role='complementary'], .x1n2onr6",
        "comment_items": "[aria-label*='Comment'], [aria-label*='Bình luận'], div[data-testid='UFI2Comment/root_depth_0']",
        "comment_text": "[data-ad-comet-preview='message'], [dir='auto'] span, .x1lliihq",
        "username": "a[role='link'] span, .x1heor9g strong span",
        "rating": None,
        "timestamp": "a[role='link'] span.x4k7w5x, abbr[data-utime]",
        "load_more_buttons": [
            "span:has-text('Xem thêm bình luận')",
            "span:has-text('View more comments')",
            "span:has-text('Xem thêm')",
            "div[role='button']:has-text('Xem thêm bình luận')",
            "div[role='button']:has-text('View more comments')",
            "span:has-text('View previous comments')",
            "span:has-text('Xem các bình luận trước')",
        ],
        "expand_buttons": [
            "div[role='button']:has-text('Xem thêm')",
            "div[role='button']:has-text('See more')",
            "span:has-text('Xem thêm')",
        ],
        "wait_selector": "[role='main'], [role='feed']",
        "scroll_target": None,  # Cuộn toàn trang
    },
    # TikTok sử dụng API interception, không dùng CSS selector
    "tiktok": {
        "name": "TikTok",
        "comment_section": None,
        "comment_items": None,
        "comment_text": None,
        "username": None,
        "rating": None,
        "timestamp": None,
        "load_more_buttons": [],
        "expand_buttons": [],
        "wait_selector": None,
        "scroll_target": None,
    },
}


# =============================================================================
# DATA MODEL
# =============================================================================

@dataclass
class Comment:
    """Đại diện cho một bình luận đã trích xuất."""
    platform: str = ""
    username: str = ""
    text: str = ""
    rating: Optional[str] = None
    timestamp: str = ""
    scraped_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def is_valid(self) -> bool:
        """Kiểm tra bình luận có hợp lệ không (phải có nội dung text)."""
        return bool(self.text and self.text.strip())


# =============================================================================
# HUMAN-LIKE BEHAVIOR - Giả lập hành vi người thật
# =============================================================================

class HumanBehavior:
    """Giả lập hành vi cuộn trang, di chuột, chờ đợi như người thật."""

    @staticmethod
    def random_delay(min_sec: float = 0.5, max_sec: float = 2.0):
        """Chờ ngẫu nhiên giữa các hành động."""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)

    @staticmethod
    def smooth_scroll(page: Page, distance: int = 300, target_selector: str = None):
        """
        Cuộn trang mượt mà, giống hành vi cuộn chuột của người thật.
        Cuộn từng bước nhỏ thay vì nhảy cả đoạn lớn.
        """
        steps = random.randint(3, 6)
        step_distance = distance // steps

        if target_selector:
            # Cuộn trong một container cụ thể
            page.evaluate("""
                (args) => {
                    const el = document.querySelector(args.selector);
                    if (el) {
                        let scrolled = 0;
                        const interval = setInterval(() => {
                            el.scrollTop += args.step;
                            scrolled += args.step;
                            if (scrolled >= args.distance) clearInterval(interval);
                        }, args.interval);
                    }
                }
            """, {
                "selector": target_selector,
                "step": step_distance,
                "distance": distance,
                "interval": random.randint(50, 150),
            })
        else:
            # Cuộn toàn trang
            page.evaluate("""
                (args) => {
                    let scrolled = 0;
                    const interval = setInterval(() => {
                        window.scrollBy(0, args.step);
                        scrolled += args.step;
                        if (scrolled >= args.distance) clearInterval(interval);
                    }, args.interval);
                }
            """, {
                "step": step_distance,
                "distance": distance,
                "interval": random.randint(50, 150),
            })

        # Chờ cuộn xong + chờ nội dung load
        time.sleep(distance / 1000 + random.uniform(0.3, 0.8))

    @staticmethod
    def scroll_to_bottom(page: Page, max_scrolls: int = 30, target_selector: str = None):
        """
        Cuộn xuống cuối trang, dừng khi không còn nội dung mới.
        Giống như người dùng cuộn liên tục để xem hết nội dung.
        """
        print("  🖱️  Đang cuộn trang xuống cuối...")
        last_height = page.evaluate("document.body.scrollHeight")
        no_change_count = 0

        for i in range(max_scrolls):
            scroll_distance = random.randint(400, 900)
            HumanBehavior.smooth_scroll(page, scroll_distance, target_selector)
            HumanBehavior.random_delay(0.8, 2.5)

            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                no_change_count += 1
                if no_change_count >= 3:
                    print(f"  ✅ Đã cuộn đến cuối trang (sau {i + 1} lần cuộn)")
                    break
            else:
                no_change_count = 0
                last_height = new_height

            if (i + 1) % 5 == 0:
                print(f"  📜 Đã cuộn {i + 1}/{max_scrolls} lần...")

        return i + 1


# =============================================================================
# TIKTOK SCRAPER - Sử dụng API Interception (ổn định hơn CSS selector)
# =============================================================================

class TikTokScraper:
    """
    Bốc tách bình luận TikTok bằng cách bắt API response.

    Thay vì dùng CSS selector (dễ hỏng khi TikTok cập nhật giao diện),
    phương pháp này bắt trực tiếp dữ liệu JSON từ API nội bộ của TikTok
    khi trình duyệt tải bình luận → dữ liệu chính xác 100%.
    """

    def __init__(self, headless: bool = False, max_scrolls: int = 30):
        self.headless = headless
        self.max_scrolls = max_scrolls
        self.comments: list[Comment] = []
        self.human = HumanBehavior()
        self._api_comments: list[dict] = []

    def _on_response(self, response):
        """
        Callback bắt API response từ TikTok.
        TikTok gọi API nội bộ để lấy bình luận, ta bắt response đó.
        """
        url = response.url
        # Các endpoint API bình luận của TikTok
        comment_api_patterns = [
            "/api/comment/list",
            "/comment/list",
            "comment/list/",
            "/api/comment/list/reply",
        ]

        if any(pattern in url for pattern in comment_api_patterns):
            try:
                data = response.json()
                comments_data = data.get("comments", [])
                if not comments_data:
                    # Một số phiên bản API trả về trong "comment"
                    comments_data = data.get("comment", [])

                for c in comments_data:
                    self._api_comments.append(c)
                    username = c.get("user", {}).get("nickname", "")
                    if not username:
                        username = c.get("user", {}).get("unique_id", "")
                    text = c.get("text", "")
                    create_time = c.get("create_time", "")

                    # Chuyển timestamp sang dạng đọc được
                    time_str = ""
                    if create_time:
                        try:
                            time_str = datetime.fromtimestamp(int(create_time)).strftime("%Y-%m-%d %H:%M:%S")
                        except (ValueError, TypeError, OSError):
                            time_str = str(create_time)

                    if text:
                        comment = Comment(
                            platform="TikTok",
                            username=username,
                            text=text,
                            timestamp=time_str,
                        )
                        self.comments.append(comment)

                if comments_data:
                    print(f"  📡 Bắt được {len(comments_data)} bình luận từ API (tổng: {len(self.comments)})")

            except Exception:
                pass

    def _extract_from_sigi_state(self, page: Page):
        """
        Phương pháp dự phòng: Trích xuất từ SIGI_STATE (hydration data).
        TikTok nhúng dữ liệu JSON vào thẻ script trong HTML.
        """
        print("  🔄 Thử trích xuất từ SIGI_STATE / __UNIVERSAL_DATA_FOR_REHYDRATION__...")
        try:
            sigi_data = page.evaluate("""
                () => {
                    // Thử SIGI_STATE
                    const sigi = document.querySelector('#SIGI_STATE');
                    if (sigi) return JSON.parse(sigi.textContent);

                    // Thử __UNIVERSAL_DATA_FOR_REHYDRATION__
                    const universal = document.querySelector('#__UNIVERSAL_DATA_FOR_REHYDRATION__');
                    if (universal) return JSON.parse(universal.textContent);

                    // Thử tìm trong script tags
                    const scripts = document.querySelectorAll('script[type="application/json"]');
                    for (const s of scripts) {
                        try {
                            const data = JSON.parse(s.textContent);
                            if (data && (data.CommentItem || data.comments || data.ItemModule)) {
                                return data;
                            }
                        } catch(e) {}
                    }
                    return null;
                }
            """)

            if not sigi_data:
                return

            # Tìm comments trong cấu trúc SIGI_STATE
            comment_items = {}
            if "CommentItem" in sigi_data:
                comment_items = sigi_data["CommentItem"]
            elif "comments" in sigi_data:
                comment_items = sigi_data["comments"]

            # Tìm user data
            user_items = {}
            if "UserModule" in sigi_data:
                user_items = sigi_data["UserModule"].get("users", {})

            if isinstance(comment_items, dict):
                for cid, cdata in comment_items.items():
                    text = cdata.get("text", "")
                    uid = cdata.get("user", "")
                    username = ""

                    if isinstance(uid, dict):
                        username = uid.get("nickname", uid.get("unique_id", ""))
                    elif isinstance(uid, str) and uid in user_items:
                        username = user_items[uid].get("nickname", uid)
                    else:
                        username = str(uid) if uid else ""

                    create_time = cdata.get("create_time", "")
                    time_str = ""
                    if create_time:
                        try:
                            time_str = datetime.fromtimestamp(int(create_time)).strftime("%Y-%m-%d %H:%M:%S")
                        except (ValueError, TypeError, OSError):
                            time_str = str(create_time)

                    if text:
                        comment = Comment(
                            platform="TikTok",
                            username=username,
                            text=text,
                            timestamp=time_str,
                        )
                        self.comments.append(comment)

            elif isinstance(comment_items, list):
                for cdata in comment_items:
                    text = cdata.get("text", "")
                    user_data = cdata.get("user", {})
                    username = ""
                    if isinstance(user_data, dict):
                        username = user_data.get("nickname", user_data.get("unique_id", ""))

                    create_time = cdata.get("create_time", "")
                    time_str = ""
                    if create_time:
                        try:
                            time_str = datetime.fromtimestamp(int(create_time)).strftime("%Y-%m-%d %H:%M:%S")
                        except (ValueError, TypeError, OSError):
                            time_str = str(create_time)

                    if text:
                        comment = Comment(
                            platform="TikTok",
                            username=username,
                            text=text,
                            timestamp=time_str,
                        )
                        self.comments.append(comment)

            if self.comments:
                print(f"  ✅ Trích xuất được {len(self.comments)} bình luận từ hydration data")

        except Exception as e:
            print(f"  ⚠️  Không lấy được dữ liệu từ SIGI_STATE: {e}")

    def _extract_from_dom(self, page: Page):
        """
        Phương pháp dự phòng cuối: Dùng JavaScript thông minh để quét DOM.
        Tìm các cụm text có cấu trúc giống bình luận (username + nội dung).
        """
        print("  🔄 Thử trích xuất trực tiếp từ DOM...")
        try:
            dom_comments = page.evaluate("""
                () => {
                    const results = [];

                    // Tìm comment container bằng nhiều cách
                    const selectors = [
                        '[data-e2e="comment-list-item"]',
                        '[class*="CommentItem"]',
                        '[class*="comment-item"]',
                        '[class*="DivCommentItem"]',
                        '[class*="CommentContent"]',
                    ];

                    let items = [];
                    for (const sel of selectors) {
                        items = document.querySelectorAll(sel);
                        if (items.length > 0) break;
                    }

                    // Nếu tìm thấy comment items
                    if (items.length > 0) {
                        for (const item of items) {
                            // Tìm username (thường là link hoặc thẻ có class chứa "user")
                            let username = '';
                            const userEls = item.querySelectorAll(
                                'a[href*="/@"], [class*="user"] a, [data-e2e*="username"], ' +
                                'span[class*="User"], a[class*="StyledLink"]'
                            );
                            for (const uel of userEls) {
                                const t = uel.textContent?.trim();
                                if (t && t.length > 0 && t.length < 50) {
                                    username = t;
                                    break;
                                }
                            }

                            // Tìm nội dung bình luận (thường là p hoặc span)
                            let text = '';
                            const textEls = item.querySelectorAll(
                                'p[class*="Comment"], span[class*="Comment"], ' +
                                '[data-e2e*="comment-level"] p, ' +
                                'p[class*="text"], span[class*="text"]'
                            );
                            for (const tel of textEls) {
                                const t = tel.textContent?.trim();
                                if (t && t.length > 0) {
                                    text = t;
                                    break;
                                }
                            }

                            // Nếu vẫn không tìm thấy text, lấy text trực tiếp
                            if (!text) {
                                const allText = item.innerText?.trim();
                                if (allText) {
                                    // Tách username ra khỏi nội dung
                                    const lines = allText.split('\\n').filter(l => l.trim());
                                    if (lines.length >= 2) {
                                        if (!username) username = lines[0];
                                        // Bỏ username, thời gian ngắn, lấy phần nội dung
                                        text = lines.filter((l, i) => {
                                            if (i === 0) return false; // skip username
                                            if (l.match(/^\\d+[smhdw]|ago|trước|giờ|phút|ngày/)) return false;
                                            if (l.match(/^Reply|Trả lời|Like|\\d+$/)) return false;
                                            return l.length > 1;
                                        }).join(' ').trim();
                                    }
                                }
                            }

                            // Tìm thời gian
                            let timeStr = '';
                            const timeEls = item.querySelectorAll(
                                '[data-e2e*="time"], [class*="Time"], [class*="time"], ' +
                                'span[class*="Created"]'
                            );
                            for (const tel of timeEls) {
                                const t = tel.textContent?.trim();
                                if (t && t.length < 30) {
                                    timeStr = t;
                                    break;
                                }
                            }

                            if (text && text.length > 0) {
                                results.push({username, text, time: timeStr});
                            }
                        }
                    }

                    return results;
                }
            """)

            for item in dom_comments:
                comment = Comment(
                    platform="TikTok",
                    username=item.get("username", ""),
                    text=item.get("text", ""),
                    timestamp=item.get("time", ""),
                )
                if comment.is_valid():
                    self.comments.append(comment)

            if dom_comments:
                print(f"  ✅ Trích xuất được {len(dom_comments)} bình luận từ DOM")

        except Exception as e:
            print(f"  ⚠️  Lỗi khi quét DOM: {e}")

    def scrape(self, url: str) -> list[Comment]:
        """Quy trình bốc tách bình luận TikTok."""
        print("=" * 65)
        print("  🚀 TIKTOK COMMENT SCRAPER (API Interception)")
        print("=" * 65)
        print(f"  🔗 URL: {url}")
        print()

        with sync_playwright() as p:
            # Mở trình duyệt
            print("  [1/4] 🌐 Đang mở trình duyệt Chrome...")
            browser = p.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--window-size=1366,768",
                ]
            )

            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                locale="vi-VN",
                timezone_id="Asia/Ho_Chi_Minh",
            )

            # Ẩn dấu hiệu automation
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => false });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                Object.defineProperty(navigator, 'languages', { get: () => ['vi-VN', 'vi', 'en-US', 'en'] });
            """)

            page = context.new_page()

            # Đăng ký bắt API response TRƯỚC khi load trang
            print("  [2/4] 📡 Đăng ký bắt API bình luận...")
            page.on("response", self._on_response)

            # Truy cập URL
            print("  [3/4] 📄 Đang tải trang TikTok...")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                self.human.random_delay(3.0, 5.0)
                print("  ✅ Trang đã tải xong")
            except Exception as e:
                print(f"  ❌ Lỗi khi tải trang: {e}")
                browser.close()
                return []

            # Cuộn trang để trigger load thêm bình luận
            print("  [4/4] 📜 Đang cuộn trang để tải thêm bình luận...")

            # Tìm và cuộn vào vùng comment
            try:
                comment_area = page.query_selector(
                    '[data-e2e="comment-list"], '
                    '[class*="CommentList"], '
                    '[class*="comment-list"]'
                )
                if comment_area:
                    comment_area.scroll_into_view_if_needed()
                    self.human.random_delay(1.0, 2.0)
            except Exception:
                pass

            # Cuộn nhiều lần để load thêm bình luận
            for i in range(self.max_scrolls):
                self.human.smooth_scroll(page, random.randint(300, 600))
                self.human.random_delay(1.0, 2.5)

                # Thử bấm nút "Xem thêm bình luận"
                try:
                    for btn_text in ["View more comments", "Xem thêm bình luận",
                                     "View more", "Xem thêm"]:
                        btn = page.query_selector(f"text='{btn_text}'")
                        if btn and btn.is_visible():
                            btn.click()
                            self.human.random_delay(1.5, 3.0)
                            print(f"  👆 Đã bấm '{btn_text}'")
                            break
                except Exception:
                    pass

                if (i + 1) % 5 == 0:
                    print(f"  📜 Đã cuộn {i + 1}/{self.max_scrolls} lần | Bình luận: {len(self.comments)}")

            # Nếu API không bắt được gì, thử các phương pháp dự phòng
            if not self.comments:
                self._extract_from_sigi_state(page)

            if not self.comments:
                self._extract_from_dom(page)

            # Loại bỏ trùng lặp
            seen = set()
            unique = []
            for c in self.comments:
                key = (c.username, c.text)
                if key not in seen:
                    seen.add(key)
                    unique.append(c)
            self.comments = unique

            print()
            print("=" * 65)
            print(f"  🎉 HOÀN TẤT! Đã trích xuất {len(self.comments)} bình luận TikTok")
            print("=" * 65)

            browser.close()

        return self.comments


# =============================================================================
# COMMENT SCRAPER CHÍNH (cho Shopee, Tiki, Facebook)
# =============================================================================

class CommentScraper:
    """
    Bốc tách bình luận tự động từ các trang web.
    Sử dụng Playwright để điều khiển trình duyệt Chrome.
    """

    def __init__(self, platform: str, headless: bool = False, max_scrolls: int = 30):
        """
        Args:
            platform: Tên nền tảng (shopee, tiki, facebook, tiktok)
            headless: True = chạy ngầm, False = hiện trình duyệt để xem
            max_scrolls: Số lần cuộn tối đa
        """
        if platform not in PLATFORM_CONFIG:
            raise ValueError(
                f"Nền tảng '{platform}' chưa được hỗ trợ. "
                f"Chọn một trong: {', '.join(PLATFORM_CONFIG.keys())}"
            )

        self.platform = platform
        self.config = PLATFORM_CONFIG[platform]
        self.headless = headless
        self.max_scrolls = max_scrolls
        self.comments: list[Comment] = []
        self.human = HumanBehavior()

    def _click_load_more(self, page: Page) -> int:
        """
        Tìm và bấm tất cả nút "Xem thêm bình luận".
        Trả về số lần bấm thành công.
        """
        total_clicks = 0

        for selector in self.config["load_more_buttons"]:
            click_count = 0
            max_clicks_per_button = 50  # Giới hạn để tránh lặp vô hạn

            while click_count < max_clicks_per_button:
                try:
                    button = page.query_selector(selector)
                    if button and button.is_visible():
                        # Di chuột đến nút trước khi bấm (giống người thật)
                        button.scroll_into_view_if_needed()
                        self.human.random_delay(0.3, 1.0)
                        button.click()
                        click_count += 1
                        total_clicks += 1
                        print(f"  👆 Đã bấm 'Xem thêm' ({total_clicks} lần)")

                        # Chờ nội dung mới load
                        self.human.random_delay(1.0, 3.0)
                        page.wait_for_load_state("networkidle", timeout=10000)
                    else:
                        break
                except Exception:
                    break

        return total_clicks

    def _expand_comments(self, page: Page):
        """Bấm nút 'Xem thêm' trong từng bình luận để mở rộng text bị ẩn."""
        for selector in self.config.get("expand_buttons", []):
            try:
                buttons = page.query_selector_all(selector)
                for btn in buttons:
                    try:
                        if btn.is_visible():
                            btn.click()
                            self.human.random_delay(0.2, 0.5)
                    except Exception:
                        continue
            except Exception:
                continue

    def _extract_text_safe(self, element: ElementHandle, selector: str) -> str:
        """Trích xuất text an toàn từ một element con."""
        try:
            child = element.query_selector(selector)
            if child:
                text = child.inner_text()
                return text.strip() if text else ""
        except Exception:
            pass
        return ""

    def _extract_comments(self, page: Page) -> list[Comment]:
        """Trích xuất tất cả bình luận từ trang hiện tại."""
        comments = []

        try:
            items = page.query_selector_all(self.config["comment_items"])
            print(f"  🔍 Tìm thấy {len(items)} phần tử bình luận")

            for item in items:
                try:
                    comment = Comment(platform=self.config["name"])

                    # Trích xuất nội dung bình luận
                    for text_sel in self.config["comment_text"].split(", "):
                        text = self._extract_text_safe(item, text_sel)
                        if text:
                            comment.text = text
                            break

                    # Trích xuất tên người dùng
                    for user_sel in self.config["username"].split(", "):
                        username = self._extract_text_safe(item, user_sel)
                        if username:
                            comment.username = username
                            break

                    # Trích xuất rating (nếu có)
                    if self.config["rating"]:
                        rating_el = item.query_selector(self.config["rating"])
                        if rating_el:
                            # Đếm số sao (thường dựa trên class hoặc thuộc tính)
                            stars = item.query_selector_all(
                                ".shopee-product-rating__icon--active, "
                                ".icon-rating-solid, "
                                "[data-rating]"
                            )
                            comment.rating = str(len(stars)) if stars else None

                    # Trích xuất thời gian
                    if self.config["timestamp"]:
                        for time_sel in self.config["timestamp"].split(", "):
                            timestamp = self._extract_text_safe(item, time_sel)
                            if timestamp:
                                comment.timestamp = timestamp
                                break

                    if comment.is_valid():
                        comments.append(comment)

                except Exception as e:
                    continue

        except Exception as e:
            print(f"  ⚠️  Lỗi khi trích xuất bình luận: {e}")

        return comments

    def _fallback_extract(self, page: Page) -> list[Comment]:
        """
        Phương pháp dự phòng: Nếu selector cụ thể không hoạt động,
        dùng cách tổng quát hơn để lấy text.
        """
        print("  🔄 Thử phương pháp trích xuất dự phòng...")
        comments = []

        try:
            # Lấy tất cả text có vẻ là bình luận (đoạn text vừa phải)
            all_texts = page.evaluate("""
                () => {
                    const results = [];
                    // Tìm tất cả element chứa text có độ dài phù hợp với bình luận
                    const elements = document.querySelectorAll(
                        'p, span, div[class*="comment"], div[class*="review"], ' +
                        'div[class*="rating"], div[class*="feedback"]'
                    );
                    const seen = new Set();
                    for (const el of elements) {
                        const text = el.innerText?.trim();
                        if (text && text.length > 10 && text.length < 2000 && !seen.has(text)) {
                            // Lọc bỏ text trùng lặp và quá ngắn/dài
                            seen.add(text);
                            results.push(text);
                        }
                    }
                    return results;
                }
            """)

            for text in all_texts:
                comment = Comment(
                    platform=self.config["name"],
                    text=text,
                    username="(không xác định)",
                )
                comments.append(comment)

        except Exception as e:
            print(f"  ⚠️  Phương pháp dự phòng cũng lỗi: {e}")

        return comments

    def scrape(self, url: str) -> list[Comment]:
        """
        Quy trình chính: Mở trình duyệt → Cuộn trang → Bấm xem thêm → Trích xuất.

        Args:
            url: URL trang cần bốc tách bình luận

        Returns:
            Danh sách các Comment đã trích xuất
        """
        # --- Nếu là TikTok, dùng TikTokScraper riêng ---
        if self.platform == "tiktok":
            tiktok_scraper = TikTokScraper(
                headless=self.headless,
                max_scrolls=self.max_scrolls,
            )
            self.comments = tiktok_scraper.scrape(url)
            return self.comments

        # --- Quy trình cho Shopee, Tiki, Facebook ---
        print("=" * 65)
        print(f"  🚀 COMMENT SCRAPER - Nền tảng: {self.config['name']}")
        print("=" * 65)
        print(f"  🔗 URL: {url}")
        print(f"  🖥️  Chế độ: {'Chạy ngầm' if self.headless else 'Hiện trình duyệt'}")
        print(f"  📜 Cuộn tối đa: {self.max_scrolls} lần")
        print()

        with sync_playwright() as p:
            # ---- BƯỚC 1: Mở trình duyệt ----
            print("  [1/5] 🌐 Đang mở trình duyệt Chrome...")
            browser = p.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--window-size=1366,768",
                ]
            )

            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                locale="vi-VN",
                timezone_id="Asia/Ho_Chi_Minh",
            )

            # Ẩn dấu hiệu automation (anti-detection)
            context.add_init_script("""
                // Ẩn webdriver flag
                Object.defineProperty(navigator, 'webdriver', { get: () => false });
                // Giả lập plugin
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                // Giả lập ngôn ngữ
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['vi-VN', 'vi', 'en-US', 'en']
                });
            """)

            page = context.new_page()

            # ---- BƯỚC 2: Truy cập URL ----
            print(f"  [2/5] 📄 Đang tải trang...")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                self.human.random_delay(2.0, 4.0)

                # Chờ khu vực bình luận xuất hiện
                if self.config["wait_selector"]:
                    try:
                        page.wait_for_selector(
                            self.config["wait_selector"],
                            timeout=15000
                        )
                        print("  ✅ Khu vực bình luận đã tải xong")
                    except Exception:
                        print("  ⚠️  Không tìm thấy khu vực bình luận mặc định, tiếp tục...")

            except Exception as e:
                print(f"  ❌ Lỗi khi tải trang: {e}")
                browser.close()
                return []

            # ---- BƯỚC 3: Cuộn xuống khu vực bình luận ----
            print(f"  [3/5] 📜 Đang cuộn trang để tải bình luận...")
            scroll_target = self.config.get("scroll_target")
            num_scrolls = self.human.scroll_to_bottom(
                page,
                max_scrolls=self.max_scrolls,
                target_selector=scroll_target,
            )

            # ---- BƯỚC 4: Bấm nút "Xem thêm" ----
            print(f"  [4/5] 👆 Đang bấm nút 'Xem thêm bình luận'...")
            total_clicks = 0

            # Lặp: cuộn thêm → bấm xem thêm → cuộn thêm
            for round_num in range(3):
                clicks = self._click_load_more(page)
                total_clicks += clicks

                if clicks > 0:
                    # Cuộn thêm sau khi load bình luận mới
                    self.human.scroll_to_bottom(
                        page, max_scrolls=5, target_selector=scroll_target
                    )
                else:
                    break

            if total_clicks == 0:
                print("  ℹ️  Không tìm thấy nút 'Xem thêm' hoặc đã tải hết")
            else:
                print(f"  ✅ Đã bấm 'Xem thêm' tổng cộng {total_clicks} lần")

            # Mở rộng các bình luận bị cắt ngắn
            self._expand_comments(page)

            # ---- BƯỚC 5: Trích xuất bình luận ----
            print(f"  [5/5] 📝 Đang trích xuất bình luận...")
            self.comments = self._extract_comments(page)

            # Nếu không tìm thấy gì, thử phương pháp dự phòng
            if not self.comments:
                self.comments = self._fallback_extract(page)

            # Loại bỏ bình luận trùng lặp
            seen_texts = set()
            unique_comments = []
            for c in self.comments:
                normalized = re.sub(r'\s+', ' ', c.text.strip().lower())
                if normalized not in seen_texts:
                    seen_texts.add(normalized)
                    unique_comments.append(c)
            self.comments = unique_comments

            print()
            print("=" * 65)
            print(f"  🎉 HOÀN TẤT! Đã trích xuất {len(self.comments)} bình luận")
            print("=" * 65)

            browser.close()

        return self.comments

    def save_to_csv(self, filepath: str = "data.csv"):
        """Lưu bình luận ra file CSV với các cột: stt, ten_tai_khoan, noi_dung, thoi_gian."""
        if not self.comments:
            print("  ⚠️  Không có bình luận để lưu!")
            return

        with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "stt", "ten_tai_khoan", "noi_dung", "thoi_gian"
            ])
            writer.writeheader()
            for idx, comment in enumerate(self.comments, start=1):
                writer.writerow({
                    "stt": idx,
                    "ten_tai_khoan": comment.username or "(ẩn danh)",
                    "noi_dung": comment.text,
                    "thoi_gian": comment.timestamp or "",
                })

        print(f"  💾 Đã lưu {len(self.comments)} bình luận vào: {filepath}")

    def save_to_json(self, filepath: str):
        """Lưu bình luận ra file JSON."""
        if not self.comments:
            print("  ⚠️  Không có bình luận để lưu!")
            return

        data = {
            "platform": self.config["name"],
            "total_comments": len(self.comments),
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "comments": [asdict(c) for c in self.comments],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"  💾 Đã lưu {len(self.comments)} bình luận vào: {filepath}")

    def print_preview(self, max_items: int = 10):
        """In xem trước một vài bình luận đầu tiên."""
        if not self.comments:
            print("  Không có bình luận nào.")
            return

        print(f"\n  📋 XEM TRƯỚC ({min(max_items, len(self.comments))}/{len(self.comments)} bình luận):")
        print("  " + "-" * 60)

        for i, c in enumerate(self.comments[:max_items]):
            username_display = c.username or "(ẩn danh)"
            text_display = c.text[:120] + "..." if len(c.text) > 120 else c.text
            rating_display = f" ⭐{c.rating}" if c.rating else ""

            print(f"  [{i+1}] 👤 {username_display}{rating_display}")
            print(f"      💬 {text_display}")
            if c.timestamp:
                print(f"      🕐 {c.timestamp}")
            print()

        if len(self.comments) > max_items:
            print(f"  ... và {len(self.comments) - max_items} bình luận khác")


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="🕷️ Comment Scraper - Bốc tách bình luận tự động",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  python comment_scraper.py --url "https://shopee.vn/product/123" --platform shopee
  python comment_scraper.py --url "https://tiki.vn/product/456" --platform tiki --output reviews.csv
  python comment_scraper.py --url "https://facebook.com/post/789" --platform facebook --headless
  python comment_scraper.py --url "https://tiktok.com/@user/video/012" --platform tiktok --max-scrolls 50
        """
    )

    parser.add_argument(
        "--url", "-u",
        required=True,
        help="URL trang cần bốc tách bình luận"
    )
    parser.add_argument(
        "--platform", "-p",
        required=True,
        choices=PLATFORM_CONFIG.keys(),
        help="Nền tảng: shopee, tiki, facebook, tiktok"
    )
    parser.add_argument(
        "--output", "-o",
        default="data.csv",
        help="File đầu ra (.csv hoặc .json). Mặc định: data.csv"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=False,
        help="Chạy ngầm (không hiện trình duyệt)"
    )
    parser.add_argument(
        "--max-scrolls", "-s",
        type=int,
        default=30,
        help="Số lần cuộn trang tối đa (mặc định: 30)"
    )
    parser.add_argument(
        "--preview", "-v",
        type=int,
        default=10,
        help="Số bình luận xem trước (mặc định: 10)"
    )

    args = parser.parse_args()

    # Tạo scraper và chạy
    scraper = CommentScraper(
        platform=args.platform,
        headless=args.headless,
        max_scrolls=args.max_scrolls,
    )

    comments = scraper.scrape(args.url)

    if comments:
        # In xem trước
        scraper.print_preview(max_items=args.preview)

        # Xác định file đầu ra
        output_file = args.output

        # Lưu file
        if output_file.endswith(".json"):
            scraper.save_to_json(output_file)
        else:
            scraper.save_to_csv(output_file)
    else:
        print("\n  ❌ Không trích xuất được bình luận nào.")
        print("  💡 Gợi ý:")
        print("     - Thử chạy không có --headless để xem trình duyệt hoạt động")
        print("     - Kiểm tra lại URL có đúng không")
        print("     - Trang có thể cần đăng nhập (Facebook)")
        print("     - Tăng --max-scrolls nếu trang có nhiều bình luận")


if __name__ == "__main__":
    main()
