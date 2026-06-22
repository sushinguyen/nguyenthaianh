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

import re


def lam_sach_van_ban(text):
    # 1. Chuyển thành chữ thường
    text = text.lower()
    # 2. Xóa các ký tự đặc biệt, dấu câu, icon (chỉ giữ lại chữ, số và khoảng trắng)
    text = re.sub(r"[^\w\s]", "", text)
    # 3. Xóa khoảng trắng thừa ở giữa và 2 đầu câu
    text = re.sub(r"\s+", " ", text).strip()
    return text


def xu_ly_va_luu_file(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f_in, open(
        output_path, "w", encoding="utf-8"
    ) as f_out:

        for line in f_in:
            if "|" in line:
                cau, nhan = line.split("|")

                # Làm sạch bình luận và chuẩn hóa nhãn
                cau_sach = lam_sach_van_ban(cau)
                nhan_sach = nhan.strip()

                # Chỉ ghi vào file mới nếu câu sau khi xử lý không bị rỗng
                if cau_sach:
                    f_out.write(f"{cau_sach} | {nhan_sach}\n")


# === CHẠY LỆNH CHUYỂN ĐỔI ===
xu_ly_va_luu_file("data1.txt", "data1_cleaner.txt")
print("Đã xử lý dữ liệu thô và lưu thành công sang file 'data1_cleaner.txt'!")