"""
STOPWORD FILTER — Lọc stopwords → data_clean1.csv / data_clean1.txt
Pipeline: NFC → clean → teen code → tokenize → lọc stopwords

Lưu ý: 'không', 'chưa', 'chẳng' KHÔNG bị lọc (giữ nghĩa phủ định).

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

from utils import preprocess_full, load_stopwords, UNDERTHESEA_AVAILABLE


if __name__ == "__main__":
    SCRIPT_DIR      = os.path.dirname(os.path.abspath(__file__))
    FILE_CSV_INPUT  = os.path.join(SCRIPT_DIR, 'data.csv')
    FILE_CSV_OUTPUT = os.path.join(SCRIPT_DIR, 'data_clean1.csv')
    FILE_TXT_INPUT  = os.path.join(SCRIPT_DIR, 'data1.txt')
    FILE_TXT_OUTPUT = os.path.join(SCRIPT_DIR, 'data_clean1.txt')

    # Xử lý CSV
    try:
        df = pd.read_csv(FILE_CSV_INPUT)
        col = None
        for c in ['noi_dung', 'text', 'content', 'comment']:
            if c in df.columns:
                col = c
                break

        if col is None:
            print(f"Loi: Khong tim thay cot noi dung. Cac cot: {list(df.columns)}")
        else:
            df['noi_dung_da_loc'] = df[col].apply(preprocess_full)
            df.to_csv(FILE_CSV_OUTPUT, index=False, encoding='utf-8-sig')
            print(f"[OK] stopword CSV: {len(df)} dong -> {FILE_CSV_OUTPUT}")
    except FileNotFoundError:
        print(f"Loi: Khong tim thay {FILE_CSV_INPUT}")

    # Xử lý TXT
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