import os
import re
import json
import pandas as pd

# ==========================================
# 1. HÀM TẢI STOPWORDS TỪ FILE JSON
# ==========================================
def load_stopwords(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return set(json.load(f)) # Chuyển thành set để xử lý cực nhanh
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file stopwords tại {file_path}")
        return set()

# Lấy thư mục hiện tại để đường dẫn luôn chuẩn
current_dir = os.path.dirname(__file__)
stopword_path = os.path.join(current_dir, "stopwords-vi.json")
file_path = os.path.join(current_dir, "data.csv")
output_path = os.path.join(current_dir, "data_clean1.csv")

# Tải danh sách stopwords vào biến
tap_stopwords = load_stopwords(stopword_path)


# ==========================================
# 2. HÀM LÀM SẠCH & LOẠI BỎ STOPWORD
# ==========================================
def lam_sach_van_ban(text):
    if not isinstance(text, str):
        return ""
        
    # 1. Chuyển thành chữ thường
    text = text.lower()
    
    # 2. Xóa các ký tự đặc biệt, dấu câu... (chỉ giữ lại chữ, số và khoảng trắng)
    text = re.sub(r"[^\w\s]", "", text)
    
    # 3. Xóa khoảng trắng thừa
    text = re.sub(r"\s+", " ", text).strip()
    
    # 4. LOẠI BỎ STOPWORDS
    words = text.split()
    filtered_words = [word for word in words if word not in tap_stopwords]
    
    return " ".join(filtered_words)


# ==========================================
# 3. ĐỌC DỮ LIỆU VÀ ÁP DỤNG
# ==========================================
df = pd.read_csv(file_path, encoding="utf-8")
ten_cot_can_lam_sach = "noi_dung"

# Gọi đúng tên hàm là lam_sach_van_ban
df["NoiDung_Da_Tach_Tu"] = df[ten_cot_can_lam_sach].apply(lam_sach_van_ban)

print("KIỂM TRA DỮ LIỆU SAU KHI LÀM SẠCH:")
print(df[[ten_cot_can_lam_sach, "NoiDung_Da_Tach_Tu"]].head())

# Xuất dữ liệu vào file data_clean1.csv (sử dụng biến output_path cho an toàn)
df.to_csv(output_path, index=False, encoding="utf-8-sig")

print(f"\n[Thành công] Đã lưu dữ liệu sạch vào file 'data_clean1.csv'!")