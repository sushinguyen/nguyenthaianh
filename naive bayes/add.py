"""
ADD.PY — Tự động gán nhãn cảm xúc cho bình luận
Chiến lược: Dựa vào từ khoá đặc trưng của từng lớp cảm xúc.
Lưu ý: Đây là "weak labeling" — độ chính xác ~60-70%.

Sử dụng:
    python add.py
"""

import os
import sys
import re
import pandas as pd

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
FILE_INPUT  = os.path.join(SCRIPT_DIR, 'data.csv')
FILE_OUTPUT = os.path.join(SCRIPT_DIR, 'data.csv')

# --- TIÊU CỰC: phàn nàn, chê, bực bội ---
TU_KHOA_TIEU_CUC = [
    'nhạc to', 'nhỏ nhạc', 'nhạc lớn', 'nhạc to quá',
    'không tập trung', 'khó tập trung',
    'méo hiểu', 'không hiểu', 'chẳng hiểu', 'khó hiểu',
    'dốt', 'ngu', 'mất gốc', 'khó nhìn', 'khó đọc',
    'chết não', 'đau đầu', 'nhức đầu',
    'quằn què', 'chán', 'thất vọng',
    'tội', 'tội nghiệp', 'xui', 'bị phạt', 'sai',
    'vừa bị', 'đền', 'mất',
    'ác', 'tức', 'bực', 'ghét',
    'hài vl', 'vãi', 'vl', 'ỉa',
]

# --- TÍCH CỰC: khen, thích, ủng hộ ---
TU_KHOA_TICH_CUC = [
    'hay', 'cuốn', 'thích', 'tuyệt', 'đỉnh', 'ok',
    'giỏi', 'chăm chú', 'tập trung',
    'thú vị', 'thú vip', 'hấp dẫn',
    'hay thật', 'hay vl', 'hay vcl',
    'nghe cuốn', 'nhạc hay',
    'cảm ơn', 'cám ơn',
    'tuyệt vời', 'xuất sắc',
    'ổn rồi', 'ổn thôi', 'đỡ hơn', 'may',
    '600k đỡ', 'nhỉnh hơn',
    'cười chết', 'cười ỉa', 'haha', ':)))', ':))',
]


def gan_nhan_tu_dong(text: str) -> str:
    """Gán nhãn tự động theo từ khoá. Ưu tiên tiêu cực trước."""
    if pd.isna(text) or not str(text).strip():
        return 'trung_tinh'
    text_lower = str(text).lower()
    for tu in TU_KHOA_TIEU_CUC:
        if tu in text_lower:
            return 'tieu_cuc'
    for tu in TU_KHOA_TICH_CUC:
        if tu in text_lower:
            return 'tich_cuc'
    return 'trung_tinh'


def la_binh_luan_that(text) -> bool:
    """Lọc bỏ metadata: hashtag, UI TikTok, timestamp, tên user..."""
    if pd.isna(text):
        return False
    t = str(text).strip()
    if t.startswith('#') or t.startswith('@'):         return False
    if t.startswith('[Nhãn dán]') or t.startswith('© '): return False
    if 'Xem' in t and 'câu trả lời' in t:             return False
    if 'bình luận' in t.lower() and len(t) < 25:      return False
    if t.lower() in ['đăng nhập', 'để bình luận']:    return False
    if 'capcut' in t.lower():                          return False
    if 'Bạn có thể thích' in t:                       return False
    if re.fullmatch(r'\d+:\d+\s*/\s*\d+:\d+', t):    return False
    if re.fullmatch(r'[\d\s:/.\-@_]+', t):            return False
    if t == t.upper() and len(t) > 20 and t[0].isalpha(): return False
    if re.fullmatch(r'[a-zA-Z0-9._\-]+', t) and ' ' not in t: return False
    if len(t.split()) < 3:                             return False
    return True


if __name__ == "__main__":
    if not os.path.exists(FILE_INPUT):
        print(f"Loi: Khong tim thay {FILE_INPUT}")
        sys.exit(1)

    df = pd.read_csv(FILE_INPUT, encoding='utf-8')

    col = None
    for c in ['text', 'noi_dung', 'content', 'comment']:
        if c in df.columns:
            col = c
            break

    if col is None:
        print(f"Loi: Khong tim thay cot noi dung. Cac cot: {list(df.columns)}")
        sys.exit(1)

    truoc = len(df)
    df = df[df[col].apply(la_binh_luan_that)].copy()
    sau = len(df)
    print(f"Loc metadata: {truoc} -> {sau} dong (bo {truoc - sau} dong)")

    df['nhan'] = df[col].apply(gan_nhan_tu_dong)

    # Thống kê
    counts = df['nhan'].value_counts()
    for label, cnt in counts.items():
        print(f"  {label}: {cnt} ({cnt/len(df)*100:.1f}%)")

    # Ví dụ mẫu mỗi nhãn
    print()
    for label in ['tieu_cuc', 'tich_cuc', 'trung_tinh']:
        sample = df[df['nhan'] == label][col].head(2).tolist()
        print(f"[{label}]")
        for s in sample:
            print(f"  - {str(s)[:70]}")

    df.to_csv(FILE_OUTPUT, index=False, encoding='utf-8-sig')
    print(f"\n[OK] Da luu {len(df)} dong co nhan vao: {FILE_OUTPUT}")
    print("Buoc tiep: python stopword.py -> python train_model.py")