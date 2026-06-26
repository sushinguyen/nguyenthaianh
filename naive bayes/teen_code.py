"""
=============================================================================
TEEN CODE NORMALIZER — Chuẩn hoá teen code tiếng Việt
=============================================================================
Module chuẩn hoá các từ viết tắt, teen code phổ biến trên mạng xã hội
(Facebook, TikTok) về dạng tiếng Việt chuẩn.

Mục đích:
  - Đồng nhất các biến thể viết tắt ("ko", "k", "kh" → "không")
  - Giúp TF-IDF nhận ra các từ cùng nghĩa là MỘT feature duy nhất
  - Tăng chất lượng đầu vào cho mô hình Naive Bayes

Sử dụng:
  from teen_code import normalize_teen_code

  text = "ko hc hoá vẫn ngồi nghe"
  result = normalize_teen_code(text)
  # → "không học hoá vẫn ngồi nghe"

Cài đặt: Không cần thư viện bên ngoài (chỉ dùng Python built-in)
"""

import re
import json
import os


# =============================================================================
# TỪ ĐIỂN TEEN CODE
# =============================================================================
# Xây dựng dựa trên dữ liệu thực tế từ bình luận Facebook & TikTok
# trong project. Chia theo nhóm ngữ nghĩa để dễ bảo trì.

TEEN_CODE_DICT = {
    # ----- PHỦ ĐỊNH (quan trọng nhất cho Sentiment Analysis) -----
    'ko':    'không',
    'k':     'không',
    'kh':    'không',
    'hok':   'không',
    'hong':  'không',
    'hông':  'không',
    'kg':    'không',
    'khg':   'không',
    'kô':    'không',
    'hem':   'không',

    # ----- ĐỘNG TỪ / TRẠNG TỪ -----
    'dc':    'được',
    'đc':    'được',
    'đk':    'được',
    'bt':    'biết',       # Ngữ cảnh phổ biến: "bt mà", "ai bt"
    'bth':   'bình thường',
    'lm':    'làm',
    'ms':    'mới',
    'r':     'rồi',
    'ik':    'đi',
    'ntn':   'như thế nào',
    'trc':   'trước',
    'trl':   'trả lời',
    'hc':    'học',
    'ns':    'nói',
    'thik':  'thích',
    'thít':  'thích',

    # ----- ĐẠI TỪ -----
    'mk':    'mình',
    'mik':   'mình',
    'mn':    'mọi người',
    'tui':   'tôi',
    't':     'tôi',        # Cẩn thận: "t" đơn lẻ thường là "tôi" trong ngữ cảnh chat
    'm':     'mày',        # Cẩn thận: "m" đơn lẻ thường là "mày" trong chat
    'e':     'em',
    'a':     'anh',
    'c':     'chị',
    'n':     'nó',

    # ----- LIÊN TỪ / GIỚI TỪ -----
    'vs':    'với',
    'cg':    'cũng',
    'cx':    'cũng',
    'v':     'vậy',
    'z':     'vậy',        # "sao z", "gì z"
    'j':     'gì',
    'ji':    'gì',
    'g':     'gì',
    'mà':    'mà',
    'vk':    'vợ',
    'ck':    'chồng',

    # ----- DANH TỪ PHỔ BIẾN -----
    'sp':    'sản phẩm',
    'vd':    'ví dụ',
    'hl':    'hài lòng',
    'cmt':   'bình luận',
    'nt':    'nhắn tin',
    'nv':    'nhiệm vụ',
    'nk':    'nhớ kỷ',
    'nki':   'nhớ kỷ',
    'flo':   'follow',
    'folow': 'follow',

    # ----- MỨC ĐỘ / CẢM XÚC -----
    'nhiu':  'nhiều',
    'nhìu':  'nhiều',
    'nhieu': 'nhiều',
    'qá':    'quá',
    'wa':    'quá',
    'lun':   'luôn',
    'lắm':   'lắm',
    'vl':    'vãi',        # Thường là từ cảm thán
    'vcl':   'vãi',
    'vc':    'vãi',
    'vkl':   'vãi',

    # ----- TỪ VIẾT TẮT KHÁC -----
    'ad':    'admin',
    'bn':    'bạn',
    'ní':    'bạn',
    'tht':   'thật',
    'thậc':  'thật',
    'đag':   'đang',
    'ngta':  'người ta',
    'bik':   'biết',
    'kiu':   'kiểu',
    'kỉu':  'kiểu',
    'loi':   'lỗi',
    'lói':   'nói',
    'nhma':  'nhưng mà',
    'nma':   'nhưng mà',
    'tưởn':  'tưởng',
    'ntố':   'nguyên tố',
    'ngto':  'nguyên tố',
    'cta':   'chúng ta',
    'bnh':   'bao nhiêu',
    'nhà':   'nhà',
    'ae':    'anh em',
    'pà':    'bà',
    'nha':   'nha',
    'ak':    'à',
    'thì':   'thì',
    'dàng':  'dáng',
    'chc':   'chắc',
}


# =============================================================================
# HÀM CHUẨN HÓA
# =============================================================================

def normalize_teen_code(text: str) -> str:
    """
    Chuẩn hoá teen code trong một chuỗi văn bản.

    Quy trình:
      1. Tách câu thành danh sách từ (split theo khoảng trắng)
      2. Mỗi từ tra trong từ điển TEEN_CODE_DICT
      3. Nếu khớp → thay thế bằng từ chuẩn
      4. Nếu không khớp → giữ nguyên

    Args:
        text: Chuỗi văn bản đầu vào (nên là lowercase)

    Returns:
        Chuỗi đã được chuẩn hoá teen code

    Ví dụ:
        >>> normalize_teen_code("ko hc hoá vẫn ngồi nghe")
        'không học hoá vẫn ngồi nghe'
        >>> normalize_teen_code("chú kh đội mũ bảo hiểm voi")
        'chú không đội mũ bảo hiểm voi'
        >>> normalize_teen_code("cx k cho đc")
        'cũng không cho được'
    """
    if not isinstance(text, str) or not text.strip():
        return text if isinstance(text, str) else ""

    words = text.split()
    normalized = []

    for word in words:
        # Tra cứu chính xác trong từ điển
        replacement = TEEN_CODE_DICT.get(word, word)
        normalized.append(replacement)

    return ' '.join(normalized)


def normalize_teen_code_safe(text: str) -> str:
    """
    Phiên bản an toàn hơn: Chỉ thay thế các từ viết tắt KHI chúng
    đứng một mình (không phải một phần của từ dài hơn).

    Bổ sung thêm: xử lý các biến thể có dấu câu dính liền.
    Ví dụ: "ko???" → "không???", "đc." → "được."

    Args:
        text: Chuỗi văn bản đầu vào

    Returns:
        Chuỗi đã được chuẩn hoá
    """
    if not isinstance(text, str) or not text.strip():
        return text if isinstance(text, str) else ""

    words = text.split()
    normalized = []

    for word in words:
        # Tách phần chữ và phần dấu câu/emoji ở cuối
        # Ví dụ: "ko???" → core="ko", suffix="???"
        match = re.match(r'^([a-zA-ZÀ-ỹđĐ]+)([\W]*)$', word)

        if match:
            core = match.group(1)
            suffix = match.group(2)
            replacement = TEEN_CODE_DICT.get(core, core)
            normalized.append(replacement + suffix)
        else:
            # Nếu không match pattern (số, emoji thuần...) → giữ nguyên
            normalized.append(word)

    return ' '.join(normalized)


# =============================================================================
# TIỆN ÍCH
# =============================================================================

def get_teen_code_dict() -> dict:
    """Trả về bản sao của từ điển teen code (để dùng bên ngoài module)."""
    return TEEN_CODE_DICT.copy()


def get_teen_code_stats(text: str) -> dict:
    """
    Thống kê số lượng teen code được tìm thấy và thay thế trong văn bản.

    Args:
        text: Chuỗi văn bản đầu vào

    Returns:
        Dict chứa thống kê: total_words, teen_codes_found, replacements
    """
    if not isinstance(text, str):
        return {"total_words": 0, "teen_codes_found": 0, "replacements": []}

    words = text.split()
    replacements = []

    for word in words:
        if word in TEEN_CODE_DICT:
            replacements.append({
                "original": word,
                "replacement": TEEN_CODE_DICT[word]
            })

    return {
        "total_words": len(words),
        "teen_codes_found": len(replacements),
        "replacements": replacements
    }


def save_teen_code_dict(filepath: str = None):
    """
    Lưu từ điển teen code ra file JSON để dễ chỉnh sửa.

    Args:
        filepath: Đường dẫn file JSON đầu ra
                  (mặc định: teen_code_dict.json cùng thư mục)
    """
    if filepath is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(current_dir, "teen_code_dict.json")

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(TEEN_CODE_DICT, f, ensure_ascii=False, indent=2)

    print(f"  💾 Đã lưu {len(TEEN_CODE_DICT)} mục teen code vào: {filepath}")


def load_teen_code_dict(filepath: str) -> dict:
    """
    Tải từ điển teen code từ file JSON (mở rộng hoặc ghi đè).

    Args:
        filepath: Đường dẫn file JSON chứa từ điển teen code

    Returns:
        Dict từ điển teen code
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"  ⚠️  Không tìm thấy file: {filepath}")
        return {}


# =============================================================================
# DEMO & TEST
# =============================================================================

if __name__ == "__main__":
    import sys
    # Fix encoding cho Windows console (cp1252 không hỗ trợ emoji/tiếng Việt đặc biệt)
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

    print()
    print("=" * 65)
    print("  TEEN CODE NORMALIZER - Demo")
    print("=" * 65)

    # Các câu test từ dữ liệu thực tế trong project
    test_cases = [
        # Từ data.csv / data1.txt
        "ko hc hoá vẫn ngồi nghe",
        "t ko hiểu tại sao mấy ông đó tìm ra đc ntố Oganesson",
        "m ơi nghĩ hè r để t yên",
        "hè r tik còn k tha",
        "cx k cho đc",
        "kh đội mũ bảo hiểm voi",
        "nhma kh hiểu bằng cách nào",
        "hay thí nhưng nhạc to quá ní",
        "xe đạp mà cục dàng cx kh tha",
        "lỗi ko gương đúng ko",
        "hài v má",
        "chán k buồn ns",
        "biết z kêu 1 củ",
        "nhậu đi xe đạp đc ko tao toàn đạp xe ms dám uống",
        "chú kh đội mũ bảo hiểm voi",
    ]

    print(f"\n  Tu dien: {len(TEEN_CODE_DICT)} muc teen code")
    print(f"  {'-' * 60}")

    for i, text in enumerate(test_cases, 1):
        result = normalize_teen_code(text)
        stats = get_teen_code_stats(text)

        if stats["teen_codes_found"] > 0:
            changes = ", ".join(
                f"'{r['original']}' -> '{r['replacement']}'"
                for r in stats["replacements"]
            )
            print(f"\n  [{i}] Input:  \"{text}\"")
            print(f"      Output: \"{result}\"")
            print(f"      Thay doi: {changes}")
        else:
            print(f"\n  [{i}] \"{text}\"")
            print(f"      (Khong co teen code)")

    print(f"\n  {'-' * 60}")

    # Lưu từ điển ra JSON
    save_teen_code_dict()

    print()
    print("=" * 65)
    print("  HOAN TAT! Demo teen code normalizer thanh cong.")
    print("=" * 65)
    print()
