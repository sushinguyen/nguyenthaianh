import re
import pandas as pd
from underthesea import word_tokenize


def clean_text(text):
    if pd.isna(text):
        return '' # nếu dòng trống -> bỏ qua

    text = text.lower()                          # "TỆ" → "tệ"
    text = re.sub(r'[^\w\s]', ' ', text)        # bỏ dấu câu, !!! ...
    text = re.sub(r'\d+', '', text)             # bỏ số
    text = re.sub(r'\s+', ' ', text).strip()   # chuẩn hoá khoảng trắng
    return text

    if text: 
        text = word_tokenize(text, format="text")   # format="text" tạo dấu gạch dưới: giao_hàng

text = "giao hàng chậm không mua nữa"
tokens = word_tokenize(text)
# → ['giao hàng', 'chậm', 'không', 'mua', 'nữa']

def doc_file_cam_xuc(file_path):
    binh_luan = []
    cam_xuc = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            # Tách câu bằng dấu '|' (thay đổi tùy theo file của bạn)
            if "|" in line:
                cau, nhan = line.strip().split("|")
                binh_luan.append(cau.strip().lower())
                cam_xuc.append(nhan.strip())

    return binh_luan, cam_xuc


x, y = doc_file_cam_xuc("data1.txt")
print("Danh sách bình luận:", x)
print("Danh sách cảm xúc:", y)