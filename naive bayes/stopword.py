"""
=============================================================================
STOPWORD FILTER — Lọc stopwords cho cả CSV và TXT
=============================================================================
Đọc dữ liệu đã làm sạch, áp dụng:
  1. Clean cơ bản (in thường, xóa emoji, dấu câu)
  2. Chuẩn hoá teen code
  3. Loại bỏ stopwords

Đầu ra:
  - data_clean1.csv  (từ data.csv)
  - data_clean1.txt  (từ data1.txt)

Sử dụng:
    python stopword.py
"""

import json
import re
import pandas as pd

# Import module chuẩn hoá teen code
from teen_code import normalize_teen_code


# ==========================================
# 1. Hàm tải Stopwords từ file JSON
# ==========================================
def load_stopwords(json_path):
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            # Chuyển list từ file JSON thành cấu trúc 'set' để tốc độ tra cứu siêu nhanh
            return set(json.load(f))
    except FileNotFoundError:
        print(f"Loi: Khong tim thay {json_path}. Vui long kiem tra lai duong dan!")
        return set()


# ==========================================
# 2. Hàm clean cơ bản
# ==========================================
def clean_text_basic(text):
    """Làm sạch cơ bản: in thường, xóa emoji, dấu câu, khoảng trắng."""
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
    return text


# ==========================================
# 3. Hàm lọc Stopwords trên một chuỗi
# ==========================================
def remove_stopwords(text, stopword_set):
    # Đảm bảo giá trị truyền vào là chuỗi (tránh lỗi nếu ô bị trống/NaN)
    if not isinstance(text, str):
        return ""

    # Bước 1: Clean cơ bản
    text = clean_text_basic(text)

    # Bước 2: Chuẩn hoá teen code
    text = normalize_teen_code(text)

    # Bước 3: Tách từ và lọc stopwords
    words = text.split()
    # Giữ lại từ KHÔNG thuộc danh sách stopwords
    filtered_words = [word for word in words if word not in stopword_set]

    return " ".join(filtered_words)


if __name__ == "__main__":
    # A. Cấu hình tên file
    FILE_JSON_STOPWORDS = 'stopwords-vi.json'

    # File CSV
    FILE_CSV_INPUT = 'data.csv'
    FILE_CSV_OUTPUT = 'data_clean1.csv'

    # File TXT (sửa: data1.txt chứ không phải data.txt)
    FILE_TXT_INPUT = 'data1.txt'
    FILE_TXT_OUTPUT = 'data_clean1.txt'

    # B. Tải danh sách stopwords vào bộ nhớ
    my_stopwords = load_stopwords(FILE_JSON_STOPWORDS)

    # ==========================================
    # C. XỬ LÝ DỮ LIỆU CSV
    # ==========================================
    try:
        df = pd.read_csv(FILE_CSV_INPUT)

        # Tìm cột chứa nội dung bình luận
        col_name = None
        for candidate in ['noi_dung', 'text', 'content', 'comment']:
            if candidate in df.columns:
                col_name = candidate
                break

        if col_name is None:
            print(f"Loi: Khong tim thay cot noi dung trong CSV.")
            print(f"Cac cot hien co: {list(df.columns)}")
        else:
            # Clean + chuẩn hoá teen code + lọc stopwords
            df['noi_dung_da_loc'] = df[col_name].apply(lambda x: remove_stopwords(x, my_stopwords))

            # Xuất ra file data_clean1.csv
            df.to_csv(FILE_CSV_OUTPUT, index=False, encoding='utf-8-sig')
            print(f"THANH CONG! Da xu ly CSV va luu tai: {FILE_CSV_OUTPUT}")
            print(f"  Pipeline: clean -> teen code -> stopwords")

    except FileNotFoundError:
        print(f"Khong tim thay file CSV dau vao: {FILE_CSV_INPUT}")
    except KeyError as e:
        print(f"Loi cot CSV: {e}")

    # ==========================================
    # D. XỬ LÝ DỮ LIỆU TXT
    # ==========================================
    try:
        # Mở file txt gốc để đọc và file txt mới để ghi
        with open(FILE_TXT_INPUT, 'r', encoding='utf-8') as f_in, \
             open(FILE_TXT_OUTPUT, 'w', encoding='utf-8') as f_out:

            # Đọc và xử lý từng dòng để giữ nguyên cấu trúc đoạn văn/xuống dòng
            for line in f_in:
                # Xóa khoảng trắng thừa ở 2 đầu
                line = line.strip()
                if line:  # Nếu dòng không trống
                    cleaned_line = remove_stopwords(line, my_stopwords)
                    f_out.write(cleaned_line + "\n")
                else:
                    # Nếu là dòng trống thì vẫn giữ lại dòng trống đó cho đúng format
                    f_out.write("\n")

        print(f"THANH CONG! Da xu ly TXT va luu tai: {FILE_TXT_OUTPUT}")
        print(f"  Pipeline: clean -> teen code -> stopwords")

    except FileNotFoundError:
         print(f"Khong tim thay file TXT dau vao: {FILE_TXT_INPUT}")