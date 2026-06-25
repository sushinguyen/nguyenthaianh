import json
import pandas as pd

# 1. Hàm tải Stopwords từ file JSON
def load_stopwords(json_path):
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            # Chuyển list từ file JSON thành cấu trúc 'set' để tốc độ tra cứu siêu nhanh
            return set(json.load(f))
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy {json_path}. Vui lòng kiểm tra lại đường dẫn!")
        return set()

# 2. Hàm lọc Stopwords trên một chuỗi
def remove_stopwords(text, stopword_set):
    # Đảm bảo giá trị truyền vào là chuỗi (tránh lỗi nếu ô bị trống/NaN)
    if not isinstance(text, str):
        return ""
        
    # Chuyển chữ thường và tách từ
    words = text.lower().split()
    # Giữ lại từ KHÔNG thuộc danh sách stopwords
    filtered_words = [word for word in words if word not in stopword_set]
    
    return " ".join(filtered_words)

if __name__ == "__main__":
    # A. Cấu hình tên file
    FILE_JSON_STOPWORDS = 'stopwords-vi.json'
    
    # File CSV
    FILE_CSV_INPUT = 'data.csv'  
    FILE_CSV_OUTPUT = 'data_clean1.csv'
    
    # File TXT (MỚI THÊM)
    FILE_TXT_INPUT = 'data.txt' 
    FILE_TXT_OUTPUT = 'data_clean1.txt'

    # B. Tải danh sách stopwords vào bộ nhớ
    my_stopwords = load_stopwords(FILE_JSON_STOPWORDS)

    # ==========================================
    # C. XỬ LÝ DỮ LIỆU CSV (Giữ nguyên của bạn)
    # ==========================================
    try:
        df = pd.read_csv(FILE_CSV_INPUT)
        
        # Giả sử cột chứa văn bản của bạn tên là 'noi_dung'. Hãy đổi lại nếu tên cột của bạn khác.
        col_name = 'noi_dung' 
        
        # Lọc stopwords
        df['noi_dung_da_loc'] = df[col_name].apply(lambda x: remove_stopwords(x, my_stopwords))

        # Xuất ra file data_clean1.csv
        df.to_csv(FILE_CSV_OUTPUT, index=False, encoding='utf-8-sig')
        print(f"✅ THÀNH CÔNG! Đã xử lý CSV và lưu tại: {FILE_CSV_OUTPUT}")
        
    except FileNotFoundError:
        print(f"❌ Không tìm thấy file CSV đầu vào: {FILE_CSV_INPUT}")
    except KeyError:
        print(f"❌ Không tìm thấy cột '{col_name}' trong file CSV. Vui lòng kiểm tra lại tên cột!")

    # ==========================================
    # D. XỬ LÝ DỮ LIỆU TXT (PHẦN MỚI THÊM)
    # ==========================================
    try:
        # Mở file txt gốc để đọc và file txt mới để ghi
        with open(FILE_TXT_INPUT, 'r', encoding='utf-8') as f_in, \
             open(FILE_TXT_OUTPUT, 'w', encoding='utf-8') as f_out:
            
            # Đọc và xử lý từng dòng để giữ nguyên cấu trúc đoạn văn/xuống dòng
            for line in f_in:
                # Xóa khoảng trắng thừa ở 2 đầu
                line = line.strip() 
                if line: # Nếu dòng không trống
                    cleaned_line = remove_stopwords(line, my_stopwords)
                    f_out.write(cleaned_line + "\n")
                else:
                    # Nếu là dòng trống thì vẫn giữ lại dòng trống đó cho đúng format
                    f_out.write("\n")
                    
        print(f"✅ THÀNH CÔNG! Đã xử lý TXT và lưu tại: {FILE_TXT_OUTPUT}")
        
    except FileNotFoundError:
         print(f"❌ Không tìm thấy file TXT đầu vào: {FILE_TXT_INPUT}")