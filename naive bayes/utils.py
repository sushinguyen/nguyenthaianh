"""
=============================================================================
UTILS — Thư viện tiện ích dùng chung cho toàn bộ pipeline
=============================================================================
Gom tất cả hàm dùng chung (clean, tokenize, stopword...) vào 1 nơi
để tránh trùng lặp code giữa text_cleaner.py, stopword.py, comment_extractor.py.

Import:
    from utils import clean_text, remove_stopwords, load_stopwords, tokenize_vi
"""

import re
import json
import os
import unicodedata

# Import teen code normalizer
from teen_code import normalize_teen_code

# ========================
# UNDERTHESEA (tuỳ chọn)
# ========================
try:
    from underthesea import word_tokenize as _uts_tokenize
    UNDERTHESEA_AVAILABLE = True
except ImportError:
    UNDERTHESEA_AVAILABLE = False


# =============================================================================
# BƯỚC 0 — Chuẩn hoá Unicode NFC
# =============================================================================

def normalize_unicode(text: str) -> str:
    """
    Chuẩn hoá Unicode về dạng NFC (Composed).

    Tại sao cần:
      - Dữ liệu scrape từ Facebook/TikTok đôi khi dùng NFD (Decomposed)
      - NFD: chữ 'ộ' = o + dấu móc + dấu nặng (3 code point)
      - NFC: chữ 'ộ' = 1 code point duy nhất
      - Nếu không chuẩn hoá: TF-IDF coi 'giao' (NFC) và 'giao' (NFD) là 2 từ khác nhau!

    Args:
        text: Chuỗi văn bản bất kỳ encoding

    Returns:
        Chuỗi đã chuẩn hoá NFC
    """
    if not isinstance(text, str):
        return ""
    return unicodedata.normalize('NFC', text)


# =============================================================================
# BƯỚC 1 — Làm sạch văn bản cơ bản
# =============================================================================

def clean_text(text: str) -> str:
    """
    Làm sạch văn bản thô:
      0. Chuẩn hoá Unicode NFC
      1. Chuyển thành chữ thường
      2. Xóa emoji (toàn bộ Unicode emoji ranges)
      3. Xóa URL và email
      4. Xóa dấu câu, ký tự đặc biệt
      5. Xóa khoảng trắng thừa
      6. Chuẩn hoá teen code

    Args:
        text: Chuỗi văn bản thô

    Returns:
        Chuỗi đã làm sạch + chuẩn hoá teen code
    """
    if not isinstance(text, str) or not text.strip():
        return ""

    # 0. Chuẩn hoá Unicode NFC
    text = normalize_unicode(text)

    # 1. Chuyển thành chữ thường
    text = text.lower()

    # 2. Xóa emoji — bao phủ toàn bộ Unicode emoji blocks
    text = re.sub(
        r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF'
        r'\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U0000FE00-\U0000FE0F'
        r'\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF'
        r'\U00002600-\U000026FF\U00002700-\U000027BF\U0001F004-\U0001F0CF'
        r'\U00010000-\U0010FFFF]+',
        '', text
    )

    # 3. Xóa URL
    text = re.sub(r'http\S+|www\.\S+', ' ', text)

    # 4. Xóa dấu câu, ký tự đặc biệt (giữ lại chữ, số, khoảng trắng)
    text = re.sub(r'[^\w\s]', ' ', text)

    # 5. Xóa khoảng trắng thừa
    text = re.sub(r'\s+', ' ', text).strip()

    # 6. Chuẩn hoá teen code
    text = normalize_teen_code(text)

    return text


# =============================================================================
# BƯỚC 2 — Tách từ tiếng Việt (Word Segmentation)
# =============================================================================

def tokenize_vi(text: str) -> str:
    """
    Tách từ tiếng Việt dùng underthesea (nếu có cài).
    Nếu không có underthesea: tách theo khoảng trắng (fallback).

    Tại sao quan trọng:
      - "giao hàng" là 1 từ ghép → phải giữ nguyên làm 1 token
      - Nếu tách thành ["giao", "hàng"] → mất nghĩa
      - underthesea nhận diện và nối từ ghép bằng dấu _
        "giao hàng" → "giao_hàng"

    Args:
        text: Chuỗi văn bản đã clean

    Returns:
        Chuỗi các token cách nhau bằng khoảng trắng
        Từ ghép được nối bằng _ (ví dụ: "giao_hàng")
    """
    if not text or not isinstance(text, str):
        return ""

    if UNDERTHESEA_AVAILABLE:
        try:
            tokens = _uts_tokenize(text)
            # Nối từ ghép bằng dấu _ để TF-IDF nhận ra là 1 đơn vị
            tokens = [t.replace(' ', '_') for t in tokens]
            tokens = [t for t in tokens if t.strip()]
            return ' '.join(tokens)
        except Exception:
            pass  # Fallback nếu lỗi

    # Fallback: tách theo khoảng trắng
    return text


# =============================================================================
# BƯỚC 3 — Lọc Stopwords
# =============================================================================

def load_stopwords(json_path: str = None) -> set:
    """
    Tải danh sách stopwords từ file JSON.

    Args:
        json_path: Đường dẫn file JSON.
                   Mặc định: stopwords-vi.json cùng thư mục với utils.py

    Returns:
        set các stopword (tra cứu O(1))
    """
    if json_path is None:
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stopwords-vi.json')

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    except FileNotFoundError:
        print(f"  [WARN] Khong tim thay stopwords: {json_path}. Dung set rong.")
        return set()


def remove_stopwords(text: str, stopword_set: set) -> str:
    """
    Loại bỏ stopwords khỏi chuỗi văn bản.

    Lưu ý: KHÔNG loại 'không', 'chưa', 'chẳng' (đã xoá khỏi stopwords-vi.json)
            vì chúng mang nghĩa phủ định quan trọng trong sentiment analysis.

    Args:
        text: Chuỗi văn bản đã qua clean + tokenize
        stopword_set: Tập hợp stopwords (dùng set để tra cứu O(1))

    Returns:
        Chuỗi đã lọc stopword
    """
    if not isinstance(text, str):
        return ""
    words = text.split()
    filtered = [w for w in words if w not in stopword_set and len(w) > 0]
    return ' '.join(filtered)


# =============================================================================
# PIPELINE ĐẦY ĐỦ
# =============================================================================

# Tải stopwords 1 lần khi import module
_STOPWORDS = load_stopwords()


def preprocess_full(text: str, use_stopwords: bool = True) -> str:
    """
    Pipeline tiền xử lý đầy đủ:
      NFC → clean → teen code → tokenize (underthesea) → stopwords

    Args:
        text: Văn bản thô
        use_stopwords: True = lọc stopwords (cho TF-IDF / train model)
                       False = chỉ clean + tokenize (giữ nguyên nghĩa)

    Returns:
        Chuỗi đã xử lý đầy đủ, sẵn sàng cho TF-IDF
    """
    text = clean_text(text)           # NFC + lowercase + emoji + teen code
    text = tokenize_vi(text)          # word segmentation (underthesea nếu có)
    if use_stopwords:
        text = remove_stopwords(text, _STOPWORDS)
    return text


def preprocess_clean_only(text: str) -> str:
    """
    Chỉ clean + teen code + tokenize, KHÔNG lọc stopwords.
    Dùng để tạo data_clean (giữ nguyên nghĩa gốc).
    """
    return preprocess_full(text, use_stopwords=False)


# =============================================================================
# TRẠNG THÁI MODULE
# =============================================================================

if __name__ == "__main__":
    import sys
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 60)
    print("  UTILS — Kiem tra trang thai module")
    print("=" * 60)
    print(f"  underthesea  : {'Co san' if UNDERTHESEA_AVAILABLE else 'CHUA CAI - dang dung fallback'}")
    print(f"  Stopwords    : {len(_STOPWORDS)} tu")
    print(f"  Teen code    : {len(__import__('teen_code').TEEN_CODE_DICT)} muc")
    print()

    test_cases = [
        "ko hc hoá vẫn ngồi nghe",
        "xe đạp mà cục dàng cx kh tha",
        "chú chạy xe kiểu gì vậy",
        "sản phẩm không tệ, giao hàng nhanh",
        "Video khoa học mà lồng nhạc remix. Nhạc to hơn cả lời 😅😅",
    ]

    print("  Pipeline: clean -> tokenize -> stopwords")
    print("-" * 60)
    for text in test_cases:
        result = preprocess_full(text)
        print(f"  IN:  {text}")
        print(f"  OUT: {result}")
        print()
