import re
from underthesea import word_tokenize

def clean_text(text):
    text = text.lower()                          # "TỆ" → "tệ"
    text = re.sub(r'[^\w\s]', ' ', text)        # bỏ dấu câu, !!! ...
    text = re.sub(r'\d+', '', text)             # bỏ số
    text = re.sub(r'\s+', ' ', text).strip()   # chuẩn hoá khoảng trắng
    return text


text = "giao hàng chậm không mua nữa"
tokens = word_tokenize(text)
# → ['giao hàng', 'chậm', 'không', 'mua', 'nữa']