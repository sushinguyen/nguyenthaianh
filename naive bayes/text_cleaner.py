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
    
    if text: 
        text = word_tokenize(text, format="text")   # format="text" tạo dấu gạch dưới: giao_hàng
        return text

df = pd.read_csv("data.csv", encoding = "utf-8")
ten_cot_can_lam_sach = "noi_dung"

#goi ham de xu ly 
print("--- KIỂM TRA DỮ LIỆU SAU KHI LÀM SẠCH ---")
print(df[[ten_cot_can_lam_sach, "NoiDung_Da_Tach_Tu"]].head())
#xuat data da xu ly ra file data clean
df.to_csv("data_clean.csv", index=False, encoding="utf-8-sig")
print("\n[Thành công] Đã lưu dữ liệu sạch vào file 'data_clean.csv'!")