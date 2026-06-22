"""
=============================================================================
COMMENT EXTRACTOR - Bốc tách bình luận bằng trình duyệt ảo → lưu data1.txt
=============================================================================
Sử dụng Playwright để mở trình duyệt Chrome ảo, tự động cuộn trang,
bấm nút "Xem thêm bình luận" như người thật, sau đó trích xuất toàn bộ
bình luận (tên tài khoản, rating, nội dung, thời gian) và lưu vào data1.txt.

Module này tái sử dụng CommentScraper từ comment_scraper.py (toàn bộ logic
mở trình duyệt, cuộn trang, bấm nút, bốc tách) và chỉ thay đổi định dạng
đầu ra: thay vì CSV → lưu ra file TXT chỉ chứa nội dung bình luận.

Cài đặt:
    pip install playwright pandas
    playwright install chromium

Sử dụng:
    python comment_extractor.py --url "https://shopee.vn/..." --platform shopee
    python comment_extractor.py --url "https://tiki.vn/..." --platform tiki
    python comment_extractor.py --url "https://www.facebook.com/..." --platform facebook
    python comment_extractor.py --url "https://www.tiktok.com/..." --platform tiktok
    python comment_extractor.py --url "https://shopee.vn/..." --platform shopee --output binh_luan.txt
    python comment_extractor.py --url "https://shopee.vn/..." --platform shopee --max-scrolls 50

Đầu ra mặc định: data1.txt (mỗi dòng là nội dung 1 bình luận)
"""

import argparse
import sys
import os

# Import CommentScraper và cấu hình từ comment_scraper.py
from comment_scraper import CommentScraper, PLATFORM_CONFIG


def format_comment(index: int, comment) -> str:
    """
    Định dạng 1 bình luận thành block text đẹp.

    Ví dụ output:
        [1] 👤 nguyen_van_a ⭐5
            💬 Sản phẩm dùng rất tốt, giao hàng nhanh chóng!
            🕐 2026-06-22 14:30:22
    """
    username = comment.username if hasattr(comment, "username") and comment.username else "(ẩn danh)"
    text = comment.text.strip() if hasattr(comment, "text") else ""
    rating = comment.rating if hasattr(comment, "rating") and comment.rating else None
    timestamp = comment.timestamp if hasattr(comment, "timestamp") and comment.timestamp else ""

    # Dòng 1: STT + tên tài khoản + rating
    rating_display = f" ⭐{rating}" if rating else ""
    line1 = f"[{index}] 👤 {username}{rating_display}"

    # Dòng 2: Nội dung bình luận
    line2 = f"    💬 {text}"

    # Dòng 3: Thời gian (nếu có)
    lines = [line1, line2]
    if timestamp:
        line3 = f"    🕐 {timestamp}"
        lines.append(line3)

    return "\n".join(lines)


def save_comments_to_txt(comments: list, output_path: str = "data1.txt") -> int:
    """
    Lưu danh sách Comment objects vào file TXT với đầy đủ thông tin.
    Mỗi bình luận gồm: tên tài khoản, rating (nếu có), nội dung, thời gian.
    Bỏ qua bình luận rỗng hoặc chỉ chứa khoảng trắng.

    Args:
        comments: Danh sách Comment objects từ CommentScraper
        output_path: Đường dẫn file TXT đầu ra (mặc định: data1.txt)

    Returns:
        Số lượng bình luận đã lưu
    """
    valid_comments = [c for c in comments if hasattr(c, "text") and c.text.strip()]

    if not valid_comments:
        print("  ⚠️  Không có bình luận nào để lưu!")
        return 0

    with open(output_path, "w", encoding="utf-8") as f:
        total = len(valid_comments)
        f.write(f"📋 TỔNG CỘNG: {total} bình luận\n")
        f.write("=" * 60 + "\n\n")

        for idx, comment in enumerate(valid_comments, start=1):
            block = format_comment(idx, comment)
            f.write(block + "\n\n")

    print(f"  💾 Đã lưu {len(valid_comments)} bình luận vào: {output_path}")
    return len(valid_comments)


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "🕷️ Comment Extractor - Bốc tách bình luận tự động bằng trình duyệt ảo, "
            "lưu nội dung vào file TXT"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  python comment_extractor.py --url "https://shopee.vn/product/123" --platform shopee
  python comment_extractor.py --url "https://tiki.vn/product/456" --platform tiki
  python comment_extractor.py --url "https://facebook.com/post/789" --platform facebook --headless
  python comment_extractor.py --url "https://tiktok.com/@user/video/012" --platform tiktok
  python comment_extractor.py --url "https://shopee.vn/..." --platform shopee --output binh_luan.txt --max-scrolls 50

Quy trình hoạt động:
  1. Mở trình duyệt Chrome ảo (Playwright)
  2. Truy cập URL sản phẩm / bài viết
  3. Tự động cuộn chuột xuống cuối trang (giống người thật)
  4. Tự động bấm nút "Xem thêm bình luận" liên tục
  5. Bốc tách toàn bộ nội dung bình luận
  6. Lưu vào file data1.txt (mỗi dòng = 1 bình luận)
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
        default="data1.txt",
        help="File TXT đầu ra (mặc định: data1.txt)"
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

    # ---- Banner ----
    print()
    print("=" * 65)
    print("  📝 COMMENT EXTRACTOR → data1.txt")
    print("  Bốc tách bình luận bằng trình duyệt ảo")
    print("=" * 65)
    print(f"  🔗 URL       : {args.url}")
    print(f"  🏪 Nền tảng  : {args.platform}")
    print(f"  📄 Đầu ra    : {args.output}")
    print(f"  🖥️  Chế độ    : {'Chạy ngầm' if args.headless else 'Hiện trình duyệt'}")
    print(f"  📜 Cuộn tối đa: {args.max_scrolls} lần")
    print()

    # ---- Tạo scraper và chạy ----
    # CommentScraper sẽ:
    #   1. Mở trình duyệt Chrome ảo (Playwright)
    #   2. Truy cập URL
    #   3. Tự động cuộn chuột xuống cuối trang
    #   4. Tự động bấm nút "Xem thêm bình luận"
    #   5. Bốc tách toàn bộ bình luận
    scraper = CommentScraper(
        platform=args.platform,
        headless=args.headless,
        max_scrolls=args.max_scrolls,
    )

    comments = scraper.scrape(args.url)

    if comments:
        # In xem trước bình luận trên terminal
        preview_count = min(args.preview, len(comments))
        print()
        print(f"  📋 XEM TRƯỚC ({preview_count}/{len(comments)} bình luận):")
        print("  " + "-" * 60)
        for i, c in enumerate(comments[:args.preview]):
            block = format_comment(i + 1, c)
            # Thêm indent cho hiển thị terminal
            for line in block.split("\n"):
                print(f"  {line}")
            print()
        if len(comments) > args.preview:
            print(f"  ... và {len(comments) - args.preview} bình luận khác")
        print()

        # Lưu vào file TXT
        count = save_comments_to_txt(comments, args.output)

        print()
        print("=" * 65)
        print(f"  🎉 HOÀN TẤT! {count} bình luận đã được lưu vào {args.output}")
        print(f"  💡 File chứa đầy đủ: tên tài khoản, rating, nội dung, thời gian.")
        print("=" * 65)
    else:
        print()
        print("  ❌ Không trích xuất được bình luận nào.")
        print("  💡 Gợi ý:")
        print("     - Thử chạy không có --headless để xem trình duyệt hoạt động")
        print("     - Kiểm tra lại URL có đúng không")
        print("     - Trang có thể cần đăng nhập (Facebook)")
        print("     - Tăng --max-scrolls nếu trang có nhiều bình luận")


if __name__ == "__main__":
    main()
