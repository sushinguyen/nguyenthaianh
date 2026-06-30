# 📋 MÔ TẢ DỰ ÁN — Naive Bayes Comment Analysis

## Tổng quan

Hệ thống bốc tách bình luận tự động từ **Facebook** và **TikTok**
bằng trình duyệt ảo Playwright, sau đó xử lý văn bản qua nhiều bước
để huấn luyện mô hình phân loại cảm xúc Naive Bayes.

**Pipeline đầy đủ:**
```
Scrape → NFC → Clean → Teen Code → Tokenize (underthesea) → Stopwords → TF-IDF → Train
```

---

## Sơ đồ Pipeline

```
[Nguồn: Facebook, TikTok]
       │
       ├─── LUỒNG CSV ─────────────────────────────────────────────────────
       │    comment_scraper.py
       │         │
       │         ▼
       │    data.csv           ← Dữ liệu thô (platform, username, text, nhan, ...)
       │         │
       │         ├──▶ text_cleaner.py ──▶ data_clean.csv
       │         │     (NFC + clean + teen code + tokenize, GIỮ nghĩa)
       │         │
       │         └──▶ stopword.py ──▶ data_clean1.csv ─────────┐
       │               (NFC + clean + teen code + tokenize       │
       │                + loại bỏ stopwords)                     │
       │                                                         ▼
       └─── LUỒNG TXT ──────────────────────────────────▶ tfidf_vectorizer.py
            comment_extractor.py                                 │
                 │                                               ▼
                 ▼                                         tfidf_matrix.npz
            data1.txt          ← Dữ liệu thô              tfidf_vocab.json
                 │                                         tfidf_vectorizer.pkl
                 ├──▶ data_clean.txt                             │
                 │                                               ▼
                 └──▶ data_clean1.txt ───────────────────▶ train_model.py
                                                                 │
                                                                 ▼
                                                           nb_model.pkl
                                                      confusion_matrix.png
```

**Modules dùng chung:**
```
utils.py          ← Thư viện tiện ích (clean, tokenize, stopwords)
teen_code.py      ← Từ điển & hàm chuẩn hoá teen code
stopwords-vi.json ← Danh sách stopwords tiếng Việt
```

---

## Mô tả từng file

### Scripts (Code)

| File                   | Chức năng |
|------------------------|-----------|
| `comment_scraper.py`   | Bốc tách bình luận bằng Playwright → xuất `data.csv` |
| `comment_extractor.py` | Bốc tách bình luận → xuất `data1.txt`, `data_clean.txt`, `data_clean1.txt` |
| `utils.py`             | **[DÙNG CHUNG]** NFC normalize, clean, tokenize (underthesea), stopwords |
| `teen_code.py`         | Từ điển 95 mục teen code + hàm chuẩn hoá |
| `text_cleaner.py`      | Bước 1: Clean + tokenize, KHÔNG lọc stopwords → `data_clean.csv` |
| `stopword.py`          | Bước 2: Clean + tokenize + lọc stopwords → `data_clean1.csv / .txt` |
| `tfidf_vectorizer.py`  | Bước 3: Vector hoá TF-IDF → ma trận số |
| `train_model.py`       | Bước 4: Train Naive Bayes + Cross-Validation + Confusion Matrix |

### Tài nguyên dùng chung

| File                  | Nội dung |
|-----------------------|----------|
| `stopwords-vi.json`   | 635 stopwords tiếng Việt (ĐÃ xoá "không", "chưa", "chẳng") |
| `teen_code_dict.json` | Từ điển teen code dạng JSON (xuất từ `teen_code.py`) |
| `requirements.txt`    | Danh sách thư viện cần cài |
| `.gitignore`          | Bỏ qua cache, model, data đã xử lý |

### Dữ liệu — Luồng CSV

| File              | Nội dung |
|-------------------|----------|
| `data.csv`        | Dữ liệu thô (platform, username, text, **nhan**, rating, timestamp) |
| `data_clean.csv`  | Đã xử lý: NFC + clean + teen code + tokenize — giữ nguyên nghĩa |
| `data_clean1.csv` | Đã clean + teen code + tokenize + lọc stopwords — đầu vào TF-IDF |

### Dữ liệu — Luồng TXT

| File              | Nội dung |
|-------------------|----------|
| `data1.txt`       | Dữ liệu thô văn bản |
| `data_clean.txt`  | Đã xử lý: NFC + clean + teen code + tokenize |
| `data_clean1.txt` | Đã clean + teen code + tokenize + lọc stopwords |

### Output

| File                    | Nội dung |
|-------------------------|----------|
| `tfidf_matrix.npz`      | Ma trận TF-IDF dạng sparse |
| `tfidf_vocab.json`      | Vocabulary `{từ: index}` |
| `tfidf_vectorizer.pkl`  | Vectorizer object (dùng cho predict) |
| `nb_model.pkl`          | Model Naive Bayes đã train |
| `confusion_matrix.png`  | Hình ảnh đánh giá model |

---

## Chi tiết từng bước xử lý văn bản

### Bước 0 — Chuẩn hoá Unicode NFC

Dữ liệu scrape từ Facebook/TikTok đôi khi dùng NFD (Decomposed).
Nếu không chuẩn hoá, TF-IDF sẽ coi cùng 1 từ là 2 feature khác nhau.

```python
# Tất cả hàm clean đều gọi bước này đầu tiên (trong utils.py)
text = unicodedata.normalize('NFC', text)
```

### Bước 1 — Làm sạch cơ bản

Trong `utils.clean_text()`:
1. Unicode NFC
2. Chuyển chữ thường
3. Xóa emoji (toàn bộ Unicode blocks)
4. Xóa URL, email
5. Xóa dấu câu, ký tự đặc biệt
6. Xóa khoảng trắng thừa
7. Chuẩn hoá teen code

### Bước 2 — Chuẩn hoá Teen Code

95 mục teen code xây dựng từ dữ liệu thực tế. Ví dụ:

```
TRƯỚC: "ko hc hoá vẫn ngồi nghe"
SAU:   "không học hoá vẫn ngồi nghe"

TRƯỚC: "xe đạp mà cục dàng cx kh tha"
SAU:   "xe đạp mà cục dáng cũng không tha"
```

| Nhóm | Ví dụ |
|------|-------|
| Phủ định | `ko/k/kh/hok/hong` → `không` |
| Động từ | `đc/dc` → `được`, `hc` → `học`, `ms` → `mới` |
| Đại từ | `mn` → `mọi người`, `t` → `tôi` |
| Cảm xúc | `vl/vc` → `vãi`, `nhiu` → `nhiều` |

### Bước 3 — Tách từ tiếng Việt (Word Segmentation)

Dùng `underthesea.word_tokenize()` để tách từ ghép tiếng Việt.
Từ ghép được nối bằng `_` để TF-IDF nhận ra là 1 đơn vị.

```
TRƯỚC: "giao hàng nhanh"
SAU:   "giao_hàng nhanh"

TRƯỚC: "sản phẩm không tệ"
SAU:   "sản_phẩm không tệ"
```

> Nếu chưa cài `underthesea`, pipeline tự động fallback về tách theo khoảng trắng.

### Bước 4 — Lọc Stopwords

Danh sách `stopwords-vi.json` đã được **cập nhật**:

> ⚠️ **Đã xoá `"không"`, `"chưa"`, `"chẳng"`, `"được"` khỏi stopwords.**
> Những từ này mang nghĩa phủ định quan trọng trong sentiment analysis.
> Nếu lọc "không" → "sản phẩm không tệ" biến thành "sản phẩm tệ" → đảo nghĩa!

---

## Cách sử dụng

```bash
# --- Cài thư viện ---
python -m pip install -r requirements.txt
playwright install chromium

# --- BƯỚC 0: Scrape dữ liệu ---
python comment_scraper.py --url "https://..." --platform facebook
# → Xuất: data.csv

# --- BƯỚC 1: Clean ---
python text_cleaner.py
# → Xuất: data_clean.csv (clean + teen code + tokenize, GIỮ nghĩa)

# --- BƯỚC 2: Lọc stopwords ---
python stopword.py
# → Xuất: data_clean1.csv + data_clean1.txt

# --- BƯỚC 3: Vector hoá ---
python tfidf_vectorizer.py
# → Xuất: tfidf_matrix.npz, tfidf_vocab.json, tfidf_vectorizer.pkl

# --- BƯỚC 4: Train model ---
# (Phải thêm cột 'nhan' vào data_clean1.csv trước!)
python train_model.py
# → Xuất: nb_model.pkl + confusion_matrix.png
```

---

## Nền tảng hỗ trợ

| Nền tảng | Loại nội dung |
|----------|---------------|
| Facebook | Bài viết, bình luận |
| TikTok   | Video, bình luận |

---

## 🐛 Known Issues & Roadmap

### ✅ Đã fix

| # | Vấn đề | Cách sửa |
|---|--------|----------|
| F1 | `stopword.py` đọc `data.txt` không tồn tại | Sửa thành `data1.txt` |
| F2 | `text_cleaner.py` xuất nhầm ra `data_clean1.csv` | Sửa đúng output path |
| F3 | `text_cleaner.py` trộn clean + stopword trong 1 hàm | Tách riêng: `text_cleaner` chỉ clean, `stopword` mới lọc |
| F4 | Không có chuẩn hoá teen code | Tạo `teen_code.py` (95 mục), tích hợp toàn pipeline |
| F5 | Emoji còn sót sau khi lọc stopword | Thêm bước xóa emoji trước lọc |
| F6 | `stopword.py` nhận text thô, không clean trước | Thêm `clean_text()` vào pipeline |
| F7 | Tên hàm và cột không nhất quán giữa các file | Chuẩn hoá qua `utils.py` |
| F8 | Không có chuẩn hoá Unicode NFC | Thêm `unicodedata.normalize('NFC', ...)` làm bước đầu tiên |
| F9 | Không có word segmentation | Tích hợp `underthesea.word_tokenize()` trong `utils.tokenize_vi()` |
| F10 | `"không"`, `"chưa"`, `"được"` bị lọc khỏi stopwords | Xoá các từ phủ định khỏi `stopwords-vi.json` |
| F11 | Code trùng lặp ở 3 file (load_stopwords, clean_text, remove_stopwords) | Gom vào `utils.py` dùng chung |
| F12 | Không có `requirements.txt` | Tạo `requirements.txt` |
| F13 | Không có `.gitignore` | Tạo `.gitignore` |

---

### 🔴 Chưa fix — Ưu tiên 1 (Bắt buộc — chặn pipeline ML)

| # | Vấn đề | Cần làm |
|---|--------|---------|
| **P1** | **Không có cột nhãn `nhan`** trong `data.csv` / `data_clean1.csv`. Naive Bayes là Supervised Learning — **bắt buộc phải có nhãn** `tich_cuc / tieu_cuc / trung_tinh`. | Gán nhãn thủ công, thêm cột `nhan` vào `data.csv` |
| **P2** | **Dữ liệu quá nhỏ** (~150 dòng). Minimum khuyến nghị: 500+ mẫu, mỗi class ≥ 100 mẫu. | Thu thập thêm dữ liệu từ nhiều bài viết/chủ đề |

---

### 🟡 Chưa fix — Ưu tiên 2

| # | Vấn đề | Cần làm |
|---|--------|---------|
| **P3** | `comment_extractor.py` chưa cập nhật dùng `utils.py` | Refactor để dùng `preprocess_full()` từ `utils` |
| **P4** | `tfidf_vectorizer.py` chưa tự động điều chỉnh `min_df` theo dataset size | Thêm logic: `min_df=1` nếu < 500 dòng (đã giải quyết trong `train_model.py`) |
| **P5** | `claude.md` mô tả pipeline cũ, không khớp code hiện tại | Cập nhật lại `claude.md` |
| **P6** | Dữ liệu scrape lẫn metadata (hashtag, timestamp, UI text "Xem 39 câu trả lời") | Thêm bộ lọc trong scraper: bỏ dòng < 3 từ, bỏ dòng chỉ chứa số/ký hiệu |

---

### 📋 Thứ tự ưu tiên fix

```
1. Ngay bây giờ (bắt buộc để có kết quả ML):
   P1 → Gán nhãn dữ liệu thủ công
   P2 → Thu thập thêm data (ít nhất 500 bình luận có nhãn)

2. Sau khi có đủ data có nhãn:
   Chạy pipeline: text_cleaner.py → stopword.py → train_model.py
   → train_model.py đã tích hợp: cross-validation, confusion matrix, save model

3. Cải thiện tiếp:
   P3 → Refactor comment_extractor.py
   P4 → Auto min_df trong tfidf_vectorizer.py
   P5 → Cập nhật claude.md
   P6 → Lọc metadata trong scraper
```