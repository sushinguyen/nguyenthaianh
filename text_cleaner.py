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

df = pd.read_csv("data.csv", encoding = "utf-8")