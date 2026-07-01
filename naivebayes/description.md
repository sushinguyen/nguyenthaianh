# 🏥 Hệ thống Phân loại Thuốc — Naive Bayes (GaussianNB)

> Hệ thống Machine Learning phân loại 5 loại thuốc dựa trên thông số bệnh nhân,  
> sử dụng thuật toán **Gaussian Naive Bayes** kết hợp **sklearn Pipeline** chuẩn production.

---

## 📖 Giới thiệu hệ thống

### Bài toán
Bác sĩ cần chỉ định thuốc phù hợp cho bệnh nhân dựa trên các chỉ số lâm sàng. Hệ thống này học từ dữ liệu lịch sử (200 bệnh nhân) và tự động gợi ý loại thuốc phù hợp nhất, kèm theo xác suất tin cậy cho từng nhãn.

### Dataset
| Thuộc tính | Giá trị |
|-----------|---------|
| File | `drug200.csv` |
| Số bệnh nhân | 200 dòng |
| Đặc trưng đầu vào | Age, Sex, BP, Cholesterol, Na_to_K |
| Nhãn đầu ra | DrugY, drugA, drugB, drugC, drugX |
| Kiểu dữ liệu | Hỗn hợp (số liên tục + phân loại) |

### Kết quả đạt được
| Metric | Giá trị |
|--------|---------|
| Test Accuracy | **82.5%** |
| Test f1_macro | **0.824** |
| Vượt baseline | **+66.4%** so với DummyClassifier |
| CV ↔ Test gap | **0.035** — mô hình ổn định |

---

## 🗂️ Cấu trúc thư mục

```
naivebayes/
│
├── drug200.csv            ← Dataset gốc (KHÔNG ghi đè)
│
├── utils.py               ← Module hỗ trợ dùng chung
├── train_model.py         ← Script train + đánh giá
├── predict.py             ← Script dự đoán bệnh nhân mới
│
├── pipeline_model.pkl     ← Model đã train (tự sinh ra khi chạy train)
├── confusion_matrix.png   ← Biểu đồ đánh giá (tự sinh ra khi chạy train)
│
├── requirements.txt       ← Danh sách thư viện (pin version)
└── description.md         ← Tài liệu này
```

---

## ⚙️ Hướng dẫn cài đặt & chạy hệ thống

### Yêu cầu
- Python 3.10+
- pip

### Bước 1 — Cài thư viện
```bash
pip install -r requirements.txt
```

### Bước 2 — Train model
```bash
python train_model.py
```

Script sẽ tự động:
- Đọc `drug200.csv`
- Chia dữ liệu Train/Test (80/20, Stratified)
- Train Pipeline (StandardScaler + OneHotEncoder + GaussianNB)
- Đánh giá bằng Cross-Validation 5-fold
- So sánh với DummyClassifier baseline
- Lưu `pipeline_model.pkl` và `confusion_matrix.png`

### Bước 3 — Dự đoán bệnh nhân mới
```bash
python predict.py
```

Hoặc dùng trong code của bạn:
```python
from predict import predict_drug

result = predict_drug(
    age=30,
    sex='M',
    bp='HIGH',
    cholesterol='NORMAL',
    na_to_k=15.5
)

print(result['drug'])           # DrugY
print(result['confidence'])     # 99.95
print(result['probabilities'])  # {'DrugY': 99.95, 'drugX': 0.05, ...}
```

---

## 🔄 Workflow — Quy trình hoạt động

```
┌─────────────────────────────────────────────────┐
│                  drug200.csv                    │
│     Age | Sex | BP | Cholesterol | Na_to_K      │
└───────────────────┬─────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│           train_test_split (Stratified)         │
│              80% Train / 20% Test               │
│   Giữ nguyên tỉ lệ nhãn ở cả hai tập           │
└──────────┬──────────────────────────────────────┘
           │
           ▼ (chỉ dùng X_train)
┌─────────────────────────────────────────────────┐
│              ColumnTransformer                  │
│                                                 │
│  StandardScaler ─→ Age, Na_to_K                 │
│  (chuẩn hoá số)    (cột số liên tục)            │
│                                                 │
│  OneHotEncoder  ─→ Sex, BP, Cholesterol         │
│  (mã hoá 0/1)      (cột phân loại)              │
└──────────┬──────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────┐
│              GaussianNB Classifier              │
│   Học phân phối Gaussian cho từng đặc trưng     │
│   theo từng nhãn thuốc                          │
└──────────┬──────────────────────────────────────┘
           │
           ├──────────────────────────────────────┐
           │                                      │
           ▼                                      ▼
┌─────────────────────┐           ┌───────────────────────────┐
│  Đánh giá (Evaluate)│           │   Lưu model (Deploy)      │
│                     │           │                           │
│  CV 5-fold f1_macro │           │   pipeline_model.pkl      │
│  vs DummyClassifier │           │   = StandardScaler        │
│  Classification     │           │   + OneHotEncoder         │
│  Report             │           │   + GaussianNB            │
│  Confusion Matrix   │           │                           │
└─────────────────────┘           └──────────┬────────────────┘
                                             │
                                             ▼
                                  ┌──────────────────────┐
                                  │    predict.py        │
                                  │                      │
                                  │  Input thô:          │
                                  │  age=30, sex='M'     │
                                  │  bp='HIGH', ...      │
                                  │         │            │
                                  │         ▼            │
                                  │  Pipeline tự động:   │
                                  │  scale + encode      │
                                  │         │            │
                                  │         ▼            │
                                  │  Output:             │
                                  │  drug='DrugY'        │
                                  │  confidence=99.9%    │
                                  └──────────────────────┘
```

---

## 🧩 Các chức năng chính

### 1. `utils.py` — Module hỗ trợ trung tâm

| Hàm | Chức năng |
|-----|-----------|
| `log_info(step, msg)` | In log theo format `[INFO] [STEP] message` |
| `log_warning(msg)` | In cảnh báo vàng `[⚠️ WARN]` |
| `log_success(msg)` | In thông báo xanh `[✅ OK]` |
| `log_section(title)` | In tiêu đề phân cách |
| `load_data(filepath)` | Đọc CSV, kiểm tra missing values |
| `check_class_distribution(y)` | Kiểm tra tỉ lệ nhãn, cảnh báo mất cân bằng > 3:1 |
| `compare_with_baseline(pipeline, X, y, cv)` | So sánh f1_macro với DummyClassifier |
| `plot_confusion_matrix(...)` | Vẽ & lưu heatmap confusion matrix |

---

### 2. `train_model.py` — Pipeline Training

**Đầu vào:** `drug200.csv`  
**Đầu ra:** `pipeline_model.pkl`, `confusion_matrix.png`

| Bước | Hành động |
|------|-----------|
| Bước 0 | Đọc dữ liệu, kiểm tra class distribution |
| Bước 1 | `train_test_split` Stratified 80/20 — **TRƯỚC** khi xử lý |
| Bước 2 | Định nghĩa `ColumnTransformer` (StandardScaler + OneHotEncoder) |
| Bước 3 | Ghép vào `sklearn.Pipeline` với `GaussianNB` |
| Bước 4A | Cross-Validation 5-fold (StratifiedKFold) trên X_train |
| Bước 4B | So sánh với `DummyClassifier` baseline |
| Bước 4C | Train trên X_train → Đánh giá trên X_test |
| Bước 4D | Vẽ Confusion Matrix + phân tích sai số |
| Bước 5 | Lưu toàn bộ Pipeline vào `pipeline_model.pkl` |

**3 vấn đề được giải quyết:**

| Vấn đề | Nguyên nhân | Giải pháp |
|--------|-------------|-----------|
| **Data Leakage** | Scale toàn dataset trước split | Split TRƯỚC, Scaler chỉ `fit(X_train)` qua Pipeline |
| **LabelEncoder sai toán học** | Ép `HIGH/LOW/NORMAL` → 0/1/2 giả tạo thứ tự | Đổi sang `OneHotEncoder` |
| **Encoder không được lưu** | predict.py không biết cách encode string | Pipeline bao gồm encoder → 1 file pkl duy nhất |

---

### 3. `predict.py` — Dự đoán bệnh nhân mới

**Đầu vào:** `pipeline_model.pkl` + thông số bệnh nhân (dạng thô — string/số)  
**Đầu ra:** tên thuốc, xác suất tin cậy, xác suất tất cả nhãn

```python
predict_drug(age, sex, bp, cholesterol, na_to_k) → {
    'drug':          'DrugY',          # Thuốc được chọn
    'info':          'Drug Y — ...',   # Mô tả
    'confidence':    99.95,            # % tin cậy
    'probabilities': {                 # Tất cả nhãn
        'DrugY': 99.95,
        'drugX':  0.05,
        ...
    }
}
```

Pipeline **tự động xử lý** toàn bộ:
- `sex='f'` → tự `.upper()` → OneHotEncoder xử lý
- `age=30` → StandardScaler chuẩn hoá
- Không cần gọi riêng encoder hay scaler

---

## 🛡️ Thiết kế an toàn — Các nguyên tắc áp dụng

| Nguyên tắc | Cách áp dụng |
|-----------|-------------|
| Không ghi đè file gốc | `drug200.csv` chỉ đọc, output ra file mới |
| Single Responsibility | Mỗi file 1 nhiệm vụ duy nhất |
| Không Data Leakage | Split trước → Scaler chỉ fit trên Train |
| Log rõ ràng | Mọi bước in `[INFO] [STEP] message` |
| Pathlib thay hard-code | `Path(__file__).parent / "file.csv"` |
| Pin version | `requirements.txt` ghi rõ version |
| `if __name__ == '__main__'` | `train_model.py` an toàn khi import |
| Metric đúng | `f1_macro` (dataset mất cân bằng 5.69x) |
| So sánh baseline | DummyClassifier làm điểm tham chiếu |

---

## 🐛 Lịch sử Bug đã Fix

| ID | Mô tả vấn đề | Phát hiện khi | Cách fix |
|----|-------------|--------------|---------|
| F01 | Data Leakage: scale toàn bộ dataset trước split → mean/var của X_test rò rỉ vào scaler | Review kiến trúc | Đưa StandardScaler vào Pipeline, chỉ `fit(X_train)` |
| F02 | LabelEncoder sai toán học: `HIGH=0, LOW=1, NORMAL=2` tạo thứ tự giả tạo cho GaussianNB | Review kiến trúc | Đổi sang `OneHotEncoder` trong `ColumnTransformer` |
| F03 | Encoder không được lưu → predict.py không xử lý được string input | Review kiến trúc | Pipeline bao gồm encoder → lưu 1 file `pipeline_model.pkl` |
| F04 | `plt.show()` block script trên Windows — script dừng chờ đóng cửa sổ | Khi chạy lần đầu | Dùng `matplotlib.use('Agg')` + `plt.close()` |
| F05 | `UnicodeEncodeError` trên Windows (cp1252 không encode được ký tự Unicode) | Khi chạy lần đầu | Thêm `sys.stdout = io.TextIOWrapper(..., encoding='utf-8')` |
| F06 | Logic train chạy lại khi import file từ nơi khác | Review code | Bọc toàn bộ logic trong `if __name__ == '__main__'` |
| F07 | Hard-code đường dẫn tương đối → lỗi nếu chạy từ thư mục khác | Review code | Dùng `Path(__file__).parent` |

---

*Tài liệu cập nhật: 02/07/2026*
