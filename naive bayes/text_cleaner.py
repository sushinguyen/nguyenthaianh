"""
=============================================================================
TEXT CLEANER — Làm sạch dữ liệu CSV + Chuẩn hoá teen code
=============================================================================
Đọc data.csv, xử lý qua 2 bước:
  Bước 1: Làm sạch cơ bản (in thường, xóa emoji, dấu câu, khoảng trắng)
  Bước 2: Chuẩn hoá teen code ("ko" → "không", "dc" → "được", ...)

Đầu ra: data_clean.csv (giữ nguyên nghĩa, chỉ chuẩn hoá)

Sử dụng:
    python text_cleaner.py
"""

import os
import re
import sys
import pandas as pd

# Fix encoding cho Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

# Import module chuẩn hoá teen code
from teen_code import normalize_teen_code


# ==========================================
# 1. HÀM LÀM SẠCH CƠ BẢN
# ==========================================
def lam_sach_van_ban(text):
    """
    Làm sạch cơ bản: in thường, xóa emoji, dấu câu, khoảng trắng.
    Sau đó chuẩn hoá teen code.
    Giữ nguyên nghĩa gốc của bình luận.
    """
    if not isinstance(text, str):
        return ""

    # 1. Chuyển thành chữ thường
    text = text.lower()

    # 2. Xóa emoji (Unicode emoji ranges)
    text = re.sub(
        r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF'
        r'\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U0000FE00-\U0000FE0F'
        r'\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF'
        r'\U00002600-\U000026FF\U00002700-\U000027BF]+',
        '', text
    )

    # 3. Xóa các ký tự đặc biệt, dấu câu (giữ lại chữ, số, khoảng trắng)
    text = re.sub(r'[^\w\s]', '', text)

    # 4. Xóa khoảng trắng thừa
    text = re.sub(r'\s+', ' ', text).strip()

    # 5. Chuẩn hoá teen code
    text = normalize_teen_code(text)

    return text


# ==========================================
# 2. ĐỌC DỮ LIỆU VÀ ÁP DỤNG
# ==========================================
if __name__ == "__main__":
    # Lấy thư mục hiện tại để đường dẫn luôn chuẩn
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "data.csv")
    output_path = os.path.join(current_dir, "data_clean.csv")

    df = pd.read_csv(file_path, encoding="utf-8")

    # Tìm cột chứa nội dung bình luận
    # Hỗ trợ nhiều tên cột khác nhau tuỳ nguồn dữ liệu
    ten_cot_can_lam_sach = None
    for col_name in ["noi_dung", "text", "content", "comment"]:
        if col_name in df.columns:
            ten_cot_can_lam_sach = col_name
            break

    if ten_cot_can_lam_sach is None:
        print(f"Loi: Khong tim thay cot noi dung trong CSV.")
        print(f"Cac cot hien co: {list(df.columns)}")
        exit(1)

    # Áp dụng hàm làm sạch + chuẩn hoá teen code
    df["noi_dung_da_lam_sach"] = df[ten_cot_can_lam_sach].apply(lam_sach_van_ban)

    print("KIEM TRA DU LIEU SAU KHI LAM SACH + CHUAN HOA TEEN CODE:")
    print(df[[ten_cot_can_lam_sach, "noi_dung_da_lam_sach"]].head(10))

    # Xuất dữ liệu đã làm sạch
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"\n[Thanh cong] Da luu du lieu sach vao file '{output_path}'!")
    print(f"  So dong: {len(df)}")
    print(f"  Cot moi: 'noi_dung_da_lam_sach' (da clean + chuan hoa teen code)")