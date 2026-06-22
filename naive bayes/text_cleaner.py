import re
import pandas as pd
from underthesea import word_tokenize
import os


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

current_dir = os.path.dirname(__file__)
file_path = os.path.join(current_dir, "data.csv")
output_path = os.path.join(current_dir, "data_clean.csv")

df = pd.read_csv(file_path, encoding="utf-8")

ten_cot_can_lam_sach = "noi_dung"

#goi ham de xu ly
df["NoiDung_Da_Tach_Tu"] = df[ten_cot_can_lam_sach].apply(clean_text)

print("KIỂM TRA DỮ LIỆU SAU KHI LÀM SẠCH ")
print(df[[ten_cot_can_lam_sach, "NoiDung_Da_Tach_Tu"]].head())


df.to_csv(output_path, index=False, encoding="utf-8-sig")
print("\n[Thành công] Đã lưu dữ liệu sạch vào file 'data_clean.csv'!")

