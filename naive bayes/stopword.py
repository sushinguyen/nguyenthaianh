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
    FILE_INPUT = 'data.csv'  # Tên file gốc của bạn (chứa dữ liệu chưa lọc)
    FILE_OUTPUT = 'data_clean1.csv' # Tên file output bạn yêu cầu

    # B. Tải danh sách stopwords vào bộ nhớ
    my_stopwords = load_stopwords(FILE_JSON_STOPWORDS)

    # C. Đọc dữ liệu văn bản vào Pandas
    # Lưu ý: Thay đổi 'data_raw.csv' bằng file dữ liệu thực của bạn. 
    # Nếu bạn chưa có file CSV, bạn có thể tạo một DataFrame từ một list/dictionary.
    try:
        df = pd.read_csv(FILE_INPUT)
        
        # D. Xử lý dữ liệu
        # Giả sử cột chứa văn bản của bạn tên là 'noi_dung'. Hãy đổi lại nếu tên cột của bạn khác.
        col_name = 'noi_dung' 
        df['noi_dung_da_loc'] = df[col_name].apply(lambda x: remove_stopwords(x, my_stopwords))

        # E. Xuất ra file data_clean1.csv
        # Tham số encoding='utf-8-sig' rất quan trọng để khi mở bằng Excel không bị lỗi font Tiếng Việt
        df.to_csv(FILE_OUTPUT, index=False, encoding='utf-8-sig')
        
        print(f"\n✅ THÀNH CÔNG! Đã lưu kết quả tại file: {FILE_OUTPUT}")
        
    except FileNotFoundError:
         print(f"Không tìm thấy file đầu vào: {FILE_INPUT}")