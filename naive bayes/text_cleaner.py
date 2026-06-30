"""
TEXT CLEANER — Làm sạch dữ liệu CSV → data_clean.csv
Pipeline: NFC → lowercase → xóa emoji → xóa dấu câu → teen code → tokenize
Giữ nguyên nghĩa gốc (KHÔNG lọc stopwords ở bước này).

Sử dụng:
    python text_cleaner.py
"""

import sys
import os
import pandas as pd

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

from utils import preprocess_clean_only, UNDERTHESEA_AVAILABLE


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path   = os.path.join(current_dir, "data.csv")
    output_path = os.path.join(current_dir, "data_clean.csv")

    df = pd.read_csv(file_path, encoding="utf-8")

    col = None
    for c in ["noi_dung", "text", "content", "comment"]:
        if c in df.columns:
            col = c
            break

    if col is None:
        print(f"Loi: Khong tim thay cot noi dung. Cac cot: {list(df.columns)}")
        sys.exit(1)

    df["noi_dung_da_lam_sach"] = df[col].apply(preprocess_clean_only)

    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[OK] text_cleaner: {len(df)} dong -> {output_path}")