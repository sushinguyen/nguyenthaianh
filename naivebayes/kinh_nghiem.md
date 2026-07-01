# 📓 Kinh nghiệm rút ra — Dự án Naive Bayes Phân loại Bình luận

> **Dự án:** Phân loại cảm xúc bình luận Facebook/TikTok bằng Naive Bayes + TF-IDF
> **Ngôn ngữ:** Python · Thư viện: scikit-learn, underthesea, Playwright
> **Ngày tổng kết:** 01/07/2026

---

## 🗂️ Mục lục

1. [Kinh nghiệm về Dữ liệu](#1-kinh-nghiệm-về-dữ-liệu)
2. [Kinh nghiệm về Tiền xử lý Văn bản](#2-kinh-nghiệm-về-tiền-xử-lý-văn-bản)
3. [Kinh nghiệm về Thuật toán & Mô hình](#3-kinh-nghiệm-về-thuật-toán--mô-hình)
4. [Kinh nghiệm về Thiết kế Hệ thống](#4-kinh-nghiệm-về-thiết-kế-hệ-thống)
5. [Kinh nghiệm về Quy trình Phát triển](#5-kinh-nghiệm-về-quy-trình-phát-triển)
6. [Checklist trước khi train model](#6-checklist-trước-khi-train-model)

---

## 1. Kinh nghiệm về Dữ liệu

### ⭐ Bài học #1 — Dữ liệu quan trọng hơn thuật toán

> *"Garbage in, garbage out — thuật toán tốt đến đâu cũng vô nghĩa nếu data sai."*

Trong dự án này, nhãn được gán **tự động bằng từ khoá cứng** (câu có từ "hay" → tích cực, câu có từ "chán" → tiêu cực). Hậu quả:

- Câu *"hay thật nhưng nhạc **to quá**"* → bị gán `tich_cuc` thay vì `tieu_cuc`
- Câu *"**chán** quá, thích bài này"* → bị gán `tieu_cuc` thay vì `tich_cuc`
- Model học từ nhãn sai → accuracy cao nhưng thực tế dự đoán sai

**✅ Rút kinh nghiệm:**
- Luôn **gán nhãn thủ công** cho ít nhất ~300–500 mẫu đầu tiên
- Dùng auto-label chỉ như bước **khởi tạo sơ bộ**, sau đó **review lại từng dòng** có `confidence = low`
- Nếu dùng keyword-matching để gán nhãn: dùng **scoring** (đếm tất cả từ khoá, lấy lớp nhiều điểm nhất) thay vì **first-match** (dừng khi gặp từ đầu tiên)

---

### ⭐ Bài học #2 — Xác định số lượng mẫu tối thiểu TRƯỚC khi bắt đầu

Dự án khởi đầu với ~150 dòng → kết quả cross-validation **không có ý nghĩa thống kê**:
- Mỗi fold chỉ có ~30 mẫu test
- Accuracy dao động ±15% chỉ vì vài mẫu thay đổi

**✅ Rút kinh nghiệm — Ngưỡng tối thiểu cho Supervised Learning:**

| Tình huống | Số mẫu tối thiểu |
|-----------|-----------------|
| 2 lớp | 200 mẫu (100/lớp) |
| 3 lớp (dự án này) | 300 mẫu (100/lớp) |
| Kết quả đáng tin cậy | 1500+ mẫu (500/lớp) |
| Cross-val 5-fold có nghĩa | ≥ 250 mẫu |

---

### ⭐ Bài học #3 — Luôn kiểm tra phân phối nhãn (Class Distribution)

Khi dùng keyword-matching để gán nhãn, phần lớn câu không khớp từ khoá → mặc định `trung_tinh`. Kết quả:
- 70% `trung_tinh`, 20% `tieu_cuc`, 10% `tich_cuc`
- Model học cách predict `trung_tinh` cho mọi câu → accuracy = 70% nhưng **vô dụng**

**✅ Rút kinh nghiệm:**
```python
# Luôn in class distribution trước khi train
print(df['nhan'].value_counts(normalize=True))

# Cảnh báo nếu imbalance ratio > 3:1
ratio = counts.max() / counts.min()
if ratio > 3:
    print(f"⚠️ Dataset mất cân bằng! Tỉ lệ max/min = {ratio:.1f}x")
```

- Với imbalance: dùng `class_prior=[1/n, 1/n, 1/n]` trong `MultinomialNB` để không bị bias
- Metric đánh giá: dùng **`f1_macro`** thay `accuracy` khi dataset mất cân bằng

---

### ⭐ Bài học #4 — Không ghi đè file dữ liệu gốc

`add.py` ban đầu có `FILE_OUTPUT = FILE_INPUT = 'data.csv'` → ghi đè lên data gốc mà không có backup.

**✅ Rút kinh nghiệm:**
- **Luôn** xuất ra file mới, không ghi đè file đầu vào
- Quy tắc đặt tên theo luồng pipeline:

```
data.csv          → Thu thập thô
data_clean.csv    → Đã clean (bước 1)
data_clean1.csv   → Đã lọc stopwords (bước 2)
data_labeled.csv  → Đã gán nhãn (bước 3)
```

---

## 2. Kinh nghiệm về Tiền xử lý Văn bản

### ⭐ Bài học #5 — Thứ tự các bước tiền xử lý rất quan trọng

**Thứ tự đúng cho tiếng Việt:**

```
1. Unicode NFC normalize      → chuẩn hoá encoding
2. Lowercase                  → đồng nhất chữ hoa/thường
3. Xoá emoji, URL, dấu câu   → loại nhiễu
4. Teen code normalize        → chuẩn hoá từ viết tắt
5. Word tokenize (underthesea) → tách từ ghép tiếng Việt
6. Stopword filter            → lọc từ không mang nghĩa
```

**Lỗi từng mắc phải:** Xoá dấu câu trước khi chuẩn hoá teen code → một số pattern teen code có ký tự đặc biệt bị mất trước khi được tra từ điển.

---

### ⭐ Bài học #6 — Unicode NFC là bước BẮT BUỘC với tiếng Việt scrape từ mạng

Dữ liệu Facebook/TikTok đôi khi dùng NFD (Decomposed):
- `'ộ'` (NFD) = `o` + dấu móc + dấu nặng = **3 code point**
- `'ộ'` (NFC) = **1 code point**

→ Cùng 1 từ `"giao hàng"` nhưng TF-IDF coi là **2 feature khác nhau** nếu không normalize!

```python
import unicodedata
text = unicodedata.normalize('NFC', text)  # Luôn làm bước đầu tiên
```

---

### ⭐ Bài học #7 — Từ phủ định KHÔNG được lọc khỏi stopwords trong Sentiment Analysis

Một sai lầm phổ biến: `"không"` nằm trong danh sách stopwords → bị lọc bỏ:

| Câu gốc | Sau khi lọc stopword | Nhãn thực | Nhãn bị suy ra |
|---------|---------------------|-----------|---------------|
| `"sản phẩm không tệ"` | `"sản phẩm tệ"` | `tich_cuc` | ❌ `tieu_cuc` |
| `"giao hàng không chậm"` | `"giao hàng chậm"` | `tich_cuc` | ❌ `tieu_cuc` |

**✅ Rút kinh nghiệm:** Xoá `"không"`, `"chưa"`, `"chẳng"`, `"được"` ra khỏi danh sách stopwords trong bất kỳ bài toán Sentiment Analysis nào.

---

### ⭐ Bài học #8 — Teen code từ 1 ký tự gây ambiguity nghiêm trọng

```python
# Nguy hiểm — thay nhầm ký tự đơn lẻ:
't': 'tôi',   # "lớp t" → "lớp tôi"   ← SAI (t là ký hiệu lớp T)
'c': 'chị',   # "đến c nào" → "đến chị nào"  ← SAI
'n': 'nó',    # "lớp n học" → "lớp nó học"   ← SAI
```

**✅ Rút kinh nghiệm:**
- Với từ 1 ký tự: **chỉ thay thế khi đứng đầu câu hoặc sau dấu câu** (không phải giữa câu)
- Hoặc dùng hàm `normalize_teen_code_safe()` với regex kiểm tra word boundary
- Tốt nhất: **bỏ** các từ 1 ký tự quá mơ hồ ra khỏi từ điển

---

### ⭐ Bài học #9 — Token pattern ảnh hưởng đến từ nào được đưa vào TF-IDF

```python
# Sai: yêu cầu ≥ 2 ký tự → mất từ đơn âm tiết tiếng Việt
token_pattern=r'(?u)\b\w[\w_]+\b'   # [\w_]+ = 1 hoặc nhiều → tổng ≥ 2 ký tự

# Đúng: yêu cầu ≥ 1 ký tự
token_pattern=r'(?u)\b\w[\w_]*\b'   # [\w_]* = 0 hoặc nhiều → tổng ≥ 1 ký tự
```

Tiếng Việt có nhiều từ đơn âm tiết quan trọng về nghĩa — không được bỏ mất vì regex sai.

---

## 3. Kinh nghiệm về Thuật toán & Mô hình

### ⭐ Bài học #10 — Chọn đúng biến thể Naive Bayes

| Biến thể | Khi nào dùng |
|----------|-------------|
| `MultinomialNB` | TF-IDF, Bag-of-Words (feature không âm) ✅ |
| `BernoulliNB` | Binary feature (từ có/không có) |
| `GaussianNB` | Feature liên tục (số thực) |
| `ComplementNB` | Dataset **mất cân bằng** — tốt hơn MultinomialNB |

**Khi có class imbalance:** Đổi sang `ComplementNB` hoặc thêm `class_prior` đều nhau:
```python
n = len(y.unique())
MultinomialNB(alpha=1.0, class_prior=[1/n]*n)
```

---

### ⭐ Bài học #11 — Dùng `sklearn.Pipeline` để tránh Data Leakage

```python
# ❌ SAI — Data leakage: vectorizer học từ toàn bộ X (kể cả test)
vectorizer.fit(X)
X_vec = vectorizer.transform(X)
X_train, X_test = train_test_split(X_vec, ...)

# ✅ ĐÚNG — Pipeline đảm bảo vectorizer chỉ fit trên train fold
pipeline = Pipeline([('tfidf', TfidfVectorizer()), ('nb', MultinomialNB())])
cross_val_score(pipeline, X, y, cv=StratifiedKFold(5))
```

Data leakage khiến accuracy trên test set **cao hơn thực tế** — mô hình "thấy" test data khi học vocabulary.

---

### ⭐ Bài học #12 — `accuracy` là metric tệ nhất cho dataset mất cân bằng

```
Dataset: 80% trung_tinh, 10% tich_cuc, 10% tieu_cuc
→ Model luôn predict "trung_tinh" → accuracy = 80% nhưng vô dụng!
```

**✅ Rút kinh nghiệm — Metric phù hợp:**

| Metric | Ý nghĩa | Dùng khi |
|--------|---------|----------|
| `accuracy` | % đúng tổng thể | Dataset **cân bằng** |
| `f1_macro` | F1 trung bình đều nhau mỗi lớp | Dataset **mất cân bằng** ✅ |
| `f1_weighted` | F1 có trọng số theo số mẫu | Quan tâm lớp lớn hơn |

```python
# Luôn dùng ít nhất 2 metric:
cv_scores = cross_val_score(pipeline, X, y, cv=cv, scoring='f1_macro')
```

---

### ⭐ Bài học #13 — Luôn so sánh với Baseline trước khi tự hào về kết quả

```python
from sklearn.dummy import DummyClassifier

dummy = DummyClassifier(strategy='most_frequent')
dummy_f1 = cross_val_score(dummy, X, y, cv=cv, scoring='f1_macro').mean()
nb_f1    = cross_val_score(pipeline, X, y, cv=cv, scoring='f1_macro').mean()

print(f"Baseline  f1_macro : {dummy_f1:.3f}")
print(f"NaiveBayes f1_macro: {nb_f1:.3f}")
print(f"Cải thiện so với baseline: +{nb_f1 - dummy_f1:.3f}")
# Nếu chênh lệch < 5% → model chưa học được gì có ý nghĩa!
```

---

### ⭐ Bài học #14 — Hyperparameter `alpha` ảnh hưởng lớn với dataset nhỏ

```python
# Chưa tối ưu:
MultinomialNB(alpha=1.0)  # Giá trị mặc định

# Tốt hơn — tìm alpha tốt nhất bằng GridSearchCV:
from sklearn.model_selection import GridSearchCV
params = {'nb__alpha': [0.01, 0.1, 0.5, 1.0, 2.0, 5.0]}
grid = GridSearchCV(pipeline, params, cv=5, scoring='f1_macro')
grid.fit(X_train, y_train)
print(f"Best alpha: {grid.best_params_['nb__alpha']}")
```

Với dataset nhỏ (~150 mẫu): `alpha` nhỏ hơn (0.1–0.5) thường tốt hơn `alpha=1.0`.

---

## 4. Kinh nghiệm về Thiết kế Hệ thống

### ⭐ Bài học #15 — Mỗi script chỉ làm 1 việc (Single Responsibility)

**Sai lầm ban đầu:** `text_cleaner.py` vừa clean vừa lọc stopwords → khó test, khó debug.

**Đúng:** Tách riêng từng bước rõ ràng:

| File | Nhiệm vụ duy nhất |
|------|------------------|
| `text_cleaner.py` | Clean + tokenize |
| `stopword.py` | Lọc stopwords |
| `tfidf_vectorizer.py` | Phân tích vocabulary (standalone) |
| `train_model.py` | Train + evaluate |

→ Dễ debug từng bước, dễ thay thế một bước mà không ảnh hưởng bước khác.

---

### ⭐ Bài học #16 — Gom code dùng chung vào một module

Ban đầu 3 file cùng viết lại `clean_text()`, `load_stopwords()`, `remove_stopwords()` → khi sửa phải sửa 3 nơi, dễ không đồng bộ.

**✅ Rút kinh nghiệm:** Tạo `utils.py` làm thư viện trung tâm:
```python
# Mọi file đều import từ 1 nơi — sửa 1 chỗ, toàn bộ pipeline được cập nhật
from utils import clean_text, tokenize_vi, remove_stopwords, preprocess_full
```

---

### ⭐ Bài học #17 — Phân biệt rõ tool "standalone" với bước trong pipeline

`tfidf_vectorizer.py` dễ bị nhầm là bước bắt buộc phải chạy trước `train_model.py`.

**Thực tế:** `train_model.py` đã tự tạo `TfidfVectorizer` bên trong `sklearn.Pipeline` → `tfidf_vectorizer.py` là **công cụ phân tích vocabulary độc lập**.

**✅ Rút kinh nghiệm:** Ghi rõ trong docstring của mỗi file:
- Đầu vào / đầu ra là file nào
- Có phải chạy trước/sau file nào không
- Đây là bước pipeline hay công cụ độc lập

---

### ⭐ Bài học #18 — CSS Selector cứng trong scraper là rủi ro lớn

```python
"comment_text": "[data-ad-comet-preview='message'], .x1lliihq",  # class tự gen
```

Facebook/TikTok thay đổi class name liên tục → scraper ngừng hoạt động mà không báo lỗi, chỉ trả về dataset trống.

**✅ Rút kinh nghiệm:**
- Ưu tiên dùng `aria-label`, `role`, `data-testid` (ổn định hơn class tự gen)
- Thêm assertion: nếu collect được 0 bình luận → raise error rõ ràng
- Kiểm tra scraper định kỳ hoặc sau mỗi lần platform deploy UI mới

---

## 5. Kinh nghiệm về Quy trình Phát triển

### ⭐ Bài học #19 — Viết unit test cho hàm tiền xử lý ngay từ đầu

Những câu hỏi tưởng đơn giản nhưng khó kiểm tra bằng mắt:
- `clean_text("Không")` → trả về `"không"` hay `"khong"`?
- `remove_stopwords("không tốt", stopwords)` → giữ `"không"` không?
- `normalize_teen_code("ko dc")` → trả về `"không được"` hay `"không dc"`?

```python
# test_utils.py — ví dụ đơn giản không cần framework phức tạp
assert "không" in remove_stopwords("sản phẩm không tệ", stopwords), \
    "Từ phủ định phải được giữ lại!"
assert normalize_teen_code("ko dc") == "không được"
```

---

### ⭐ Bài học #20 — Pin version trong `requirements.txt`

```
# ❌ Tệ — không biết version nào sẽ được cài:
scikit-learn
pandas

# ✅ Tốt — reproducible sau 1 năm:
scikit-learn==1.4.2
pandas==2.2.1
underthesea==6.8.4
playwright==1.44.0
```

Một năm sau pull code về → `pip install -r requirements.txt` cài phiên bản mới → API thay đổi → lỗi không rõ nguyên nhân.

---

### ⭐ Bài học #21 — Kiểm tra pipeline bằng cách đọc file từ INPUT đúng

**Lỗi thực tế đã mắc:** `stopword.py` đọc `data.csv` (thô) thay vì `data_clean.csv` (output của `text_cleaner.py`) → `text_cleaner.py` hoàn toàn bị bỏ qua trong luồng CSV mà không có lỗi nào!

**✅ Rút kinh nghiệm:**
- Sau khi viết xong pipeline, **kiểm tra thủ công từng bước**: file nào tạo ra, file đó có được bước tiếp theo đọc vào không?
- Thêm log rõ ràng trong mỗi script: `[INFO] Đọc từ: X → ghi ra: Y`

---

### ⭐ Bài học #22 — Ghi lại mọi bug đã fix vào tài liệu

Mỗi lần fix bug, ghi vào `description.md` mục **"Đã fix"**:

```markdown
| F14 | stopword.py đọc data.csv thô thay vì data_clean.csv | Sửa FILE_CSV_INPUT |
| F15 | token_pattern bỏ mất từ 1 ký tự | Đổi [\w_]+ thành [\w_]* |
```

→ Sau này nhìn lại biết hệ thống từng có vấn đề gì, tránh mắc lại lỗi cũ, và người khác join project hiểu được lịch sử.

---

## 6. Checklist trước khi train model

Dùng checklist này trước mỗi lần chạy `train_model.py`:

```
✅ DỮ LIỆU
  [ ] Có ≥ 300 mẫu có nhãn (ưu tiên ≥ 500)
  [ ] Mỗi lớp có ≥ 100 mẫu
  [ ] Imbalance ratio < 3:1 (hoặc đã bật class_prior đều)
  [ ] Đã review ít nhất 50% nhãn tự động
  [ ] File input: data_clean1.csv có cột 'noi_dung_da_loc' VÀ 'nhan'

✅ TIỀN XỬ LÝ
  [ ] Đã chạy text_cleaner.py → data_clean.csv
  [ ] Đã chạy stopword.py (đọc data_clean.csv) → data_clean1.csv
  [ ] Từ phủ định ("không", "chưa") còn trong text sau stopword
  [ ] Unicode đã NFC normalize

✅ MÔ HÌNH
  [ ] Pipeline dùng StratifiedKFold, không split trước khi tạo pipeline
  [ ] Metric là f1_macro (không chỉ accuracy)
  [ ] Có so sánh với DummyClassifier baseline
  [ ] alpha đã được thử ít nhất vài giá trị (0.1, 0.5, 1.0, 2.0)

✅ KẾT QUẢ
  [ ] f1_macro của NB cao hơn baseline ≥ 10%
  [ ] Confusion matrix không bị lệch hoàn toàn về 1 lớp
  [ ] Đã lưu model: nb_model.pkl (bao gồm cả TfidfVectorizer bên trong)
```

---

## 📌 Top 5 bài học quan trọng nhất

| # | Bài học | Áp dụng ngay |
|---|---------|-------------|
| 1 | **Gán nhãn thủ công** — không có shortcut | Trước khi thu thập data |
| 2 | **Giữ "không/chưa/chẳng" trong stopwords** | Mọi bài toán Sentiment Analysis |
| 3 | **Dùng Pipeline để tránh data leakage** | Mọi bài toán ML có vectorization |
| 4 | **Metric là f1_macro** khi dataset mất cân bằng | Trước khi train |
| 5 | **So sánh với DummyClassifier baseline** | Trước khi tuyên bố kết quả tốt |

---

*📅 Tài liệu này được tổng kết từ quá trình xây dựng, debug và review dự án Naive Bayes.*
*Cập nhật lần cuối: 01/07/2026*
