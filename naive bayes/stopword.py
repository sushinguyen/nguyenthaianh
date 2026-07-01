"""
STOPWORD FILTER — Lọc stopwords → data_clean1.csv / data_clean1.txt

Input:  data_clean.csv  (output của text_cleaner.py — đã clean + teen code + tokenize)
        data1.txt       (văn bản thô dạng TXT)
Output: data_clean1.csv (đã lọc stopwords, đầu vào cho TF-IDF)
        data_clean1.txt

Pipeline (CSV): đọc cột 'noi_dung_da_lam_sach' từ data_clean.csv → lọc stopwords
Pipeline (TXT): đọc từng dòng data1.txt → clean + tokenize + lọc stopwords

Lưu ý: 'không', 'chưa', 'chẳng', 'được' KHÔNG bị lọc (giữ nghĩa phủ định).

Sử dụng:
    python stopword.py
"""

import sys
import os
import pandas as pd

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

from utils import remove_stopwords, load_stopwords, preprocess_full, UNDERTHESEA_AVAILABLE

# Tải stopwords 1 lần
_STOPWORDS = load_stopwords()


if __name__ == "__main__":
    SCRIPT_DIR      = os.path.dirname(os.path.abspath(__file__))
    # [FIX F14] Đọc data_clean.csv (output của text_cleaner.py), không phải data.csv thô
    # Đảm bảo text_cleaner.py → stopword.py đúng thứ tự trong pipeline
    FILE_CSV_INPUT  = os.path.join(SCRIPT_DIR, 'data_clean.csv')
    FILE_CSV_OUTPUT = os.path.join(SCRIPT_DIR, 'data_clean1.csv')
    FILE_TXT_INPUT  = os.path.join(SCRIPT_DIR, 'data1.txt')
    FILE_TXT_OUTPUT = os.path.join(SCRIPT_DIR, 'data_clean1.txt')

    # Xử lý CSV — đọc cột đã clean từ text_cleaner.py
    try:
        df = pd.read_csv(FILE_CSV_INPUT, encoding='utf-8-sig')

        # Ưu tiên cột output của text_cleaner.py, fallback về cột gốc nếu chạy độc lập
        if 'noi_dung_da_lam_sach' in df.columns:
            col = 'noi_dung_da_lam_sach'
            print("[INFO] Dung cot 'noi_dung_da_lam_sach' tu text_cleaner.py")
            df['noi_dung_da_loc'] = df[col].astype(str).apply(
                lambda t: remove_stopwords(t, _STOPWORDS)
            )
        else:
            # Fallback: chạy pipeline đầy đủ nếu không có cột cleaned
            col = None
            for c in ['noi_dung', 'text', 'content', 'comment']:
                if c in df.columns:
                    col = c
                    break
            if col is None:
                print(f"Loi: Khong tim thay cot noi dung. Cac cot: {list(df.columns)}")
            else:
                print(f"[WARN] Khong tim thay 'noi_dung_da_lam_sach', chay pipeline day du tu cot '{col}'")
                df['noi_dung_da_loc'] = df[col].apply(preprocess_full)

        if 'noi_dung_da_loc' in df.columns:
            df.to_csv(FILE_CSV_OUTPUT, index=False, encoding='utf-8-sig')
            print(f"[OK] stopword CSV: {len(df)} dong -> {FILE_CSV_OUTPUT}")
    except FileNotFoundError:
        print(f"Loi: Khong tim thay {FILE_CSV_INPUT}")
        print("  Hay chay text_cleaner.py truoc.")

    # Xử lý TXT — chạy pipeline đầy đủ (TXT không có bước text_cleaner riêng)
    try:
        with open(FILE_TXT_INPUT, 'r', encoding='utf-8') as f_in, \
             open(FILE_TXT_OUTPUT, 'w', encoding='utf-8') as f_out:
            for line in f_in:
                stripped = line.strip()
                if stripped:
                    f_out.write(preprocess_full(stripped) + "\n")
                else:
                    f_out.write("\n")
        print(f"[OK] stopword TXT: {FILE_TXT_INPUT} -> {FILE_TXT_OUTPUT}")
    except FileNotFoundError:
        print(f"Loi: Khong tim thay {FILE_TXT_INPUT}")