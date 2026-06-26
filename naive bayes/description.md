# 📋 MÔ TẢ DỰ ÁN — Naive Bayes Comment Analysis

## Tổng quan

Hệ thống bốc tách bình luận tự động từ **Facebook** và **TikTok**
bằng trình duyệt ảo Playwright, sau đó làm sạch dữ liệu qua nhiều bước
(clean → chuẩn hoá teen code → loại stopwords → TF-IDF)
để chuẩn bị cho mô hình phân loại Naive Bayes.

---

## Sơ đồ Pipeline

```
[Nguồn: Facebook, TikTok]
       │
       ├─── LUỒNG CSV ──────────────────────────────────────────────
       │    comment_scraper.py
       │         │
       │         ▼
       │    data.csv              ← Dữ liệu thô (platform, username, text, ...)
       │         │
       │         ├──▶ text_cleaner.py ──▶ data_clean.csv
       │         │     (in thường, emoji, dấu câu, khoảng trắng)
       │         │
       │         └──▶ stopword.py ──▶ data_clean1.csv ─┐
       │               (clean + chuẩn hoá teen code     │
       │                + loại bỏ stopwords)            │
       │                                               ├──▶ tfidf_vectorizer.py
       └─── LUỒNG TXT ────────────────────────────────│        │
            comment_extractor.py                       │        ▼
                 │                                     │   tfidf_matrix.npz
                 ▼                                     │   tfidf_vocab.json
            data1.txt              ← Dữ liệu thô     │   tfidf_vectorizer.pkl
                 │                                     │
                 ├──▶ data_clean.txt                   │
                 │     (in thường, xóa emoji, dấu câu) │
                 │                                     │
                 └──▶ data_clean1.txt ─────────────────┘
                       (clean + teen code + stopwords)
```

**Module dùng chung:**

```
teen_code.py         ← Từ điển & hàm chuẩn hoá teen code tiếng Việt
stopwords-vi.json    ← Danh sách stopwords tiếng Việt
```

---

## Mô tả từng file

### 🔧 Scripts (Code)

| File                   | Chức năng                                                        |
|------------------------|------------------------------------------------------------------|
| `comment_scraper.py`   | Bốc tách bình luận bằng trình duyệt ảo → xuất **data.csv**     |
| `comment_extractor.py` | Bốc tách bình luận → xuất **data1.txt**, **data_clean.txt**, **data_clean1.txt** |
| `text_cleaner.py`      | Làm sạch CSV: in thường, dấu câu, khoảng trắng → **data_clean.csv** |
| `teen_code.py`         | Chuẩn hoá teen code: "ko"→"không", "dc"→"được", "kh"→"không"... |
| `stopword.py`          | Lọc stopwords cho cả CSV và TXT → **data_clean1.csv**, **data_clean1.txt** |
| `tfidf_vectorizer.py`  | Vector hoá TF-IDF: chuyển văn bản → ma trận số cho Naive Bayes  |

### 📄 Tài nguyên dùng chung

| File                 | Nội dung                                                          |
|----------------------|-------------------------------------------------------------------|
| `stopwords-vi.json`  | Danh sách stopwords tiếng Việt (dùng chung cho cả 2 luồng)       |
| `teen_code_dict.json` | Từ điển teen code dạng JSON (xuất từ teen_code.py, dễ chỉnh sửa) |

### 📄 Dữ liệu — Luồng CSV

| File               | Nội dung                                                          |
|--------------------|-------------------------------------------------------------------|
| `data.csv`         | Dữ liệu thô dạng bảng (platform, username, text, rating, timestamp) |
| `data_clean.csv`   | Đã xử lý: in thường, xóa emoji, dấu câu, khoảng trắng — **giữ nguyên nghĩa** |
| `data_clean1.csv`  | Đã clean + chuẩn hoá teen code + loại bỏ stopwords — sẵn sàng cho TF-IDF |

### 📄 Dữ liệu — Luồng TXT

| File               | Nội dung                                                          |
|--------------------|-------------------------------------------------------------------|
| `data1.txt`        | Dữ liệu thô văn bản (tên, rating, nội dung, thời gian)           |
| `data_clean.txt`   | Đã xử lý: in thường, xóa emoji, dấu câu — **giữ nguyên nghĩa**  |
| `data_clean1.txt`  | Đã clean + chuẩn hoá teen code + loại bỏ stopwords                |

### 📄 Dữ liệu — Output TF-IDF

| File                    | Nội dung                                                        |
|-------------------------|-----------------------------------------------------------------|
| `tfidf_matrix.npz`     | Ma trận TF-IDF dạng sparse (n_samples × n_features)             |
| `tfidf_vocab.json`     | Từ điển vocabulary `{từ: index}` — dễ đọc, dễ debug             |
| `tfidf_vectorizer.pkl` | Vectorizer object — dùng cho predict văn bản mới                |

---

## Nền tảng hỗ trợ

| Nền tảng   | Loại nội dung        |
|------------|----------------------|
| Facebook   | Bài viết, bình luận  |
| TikTok     | Video, bình luận     |

---

## Chi tiết bước chuẩn hoá Teen Code

### Tại sao cần chuẩn hoá teen code?

Bình luận tiếng Việt trên mạng xã hội có rất nhiều từ viết tắt.
Nếu không chuẩn hoá, mô hình sẽ coi `"ko"`, `"k"`, `"kh"` là **ba từ khác nhau**,
trong khi chúng đều có nghĩa là `"không"`.

### Ví dụ thực tế từ dữ liệu

```
TRƯỚC chuẩn hoá:
  "ko hc hoá vẫn ngồi nghe"
  "t ko hiểu tại sao mấy ông đó tìm ra đc ntố Oganesson"
  "xe đạp mà cục dàng cx kh tha"
  "nhậu đi xe đạp đc ko tao toàn đạp xe ms dám uống"

SAU chuẩn hoá:
  "không học hoá vẫn ngồi nghe"
  "tôi không hiểu tại sao mấy ông đó tìm ra được nguyên tố Oganesson"
  "xe đạp mà cục dáng cũng không tha"
  "nhậu đi xe đạp được không tao toàn đạp xe mới dám uống"
```

### Danh sách teen code được hỗ trợ

| Nhóm | Teen code | Từ chuẩn |
|------|-----------|----------|
| Phủ định | ko, k, kh, hok, hong, hông, kg, khg | không |
| Động từ | dc/đc → được, lm → làm, ms → mới, hc → học, ns → nói | ... |
| Đại từ | mk/mik → mình, mn → mọi người, t → tôi, m → mày | ... |
| Liên từ | vs → với, cx/cg → cũng, v/z → vậy, j → gì | ... |
| Cảm xúc | nhiu/nhìu → nhiều, wa/qá → quá, lun → luôn | ... |

> 📌 **Tổng cộng: ~80 mục teen code**, xây dựng từ dữ liệu thực tế của project.

---

## Lưu ý quan trọng

> ⚠️ Dữ liệu trong `.csv` và `.txt` là **KHÁC NHAU**, được xử lý qua **2 luồng riêng biệt**.
> - Luồng CSV: `comment_scraper.py` → `text_cleaner.py` / `stopword.py`
> - Luồng TXT: `comment_extractor.py` (tích hợp sẵn clean + stopword)
>
> Cả hai luồng đều sử dụng chung `teen_code.py` và `stopwords-vi.json`.

---

## Cách sử dụng

```bash
# --- LUỒNG CSV ---
python comment_scraper.py --url "https://facebook.com/post/123" --platform facebook
python comment_scraper.py --url "https://tiktok.com/@user/video/456" --platform tiktok
# → Xuất: data.csv

python text_cleaner.py
# → Xuất: data_clean.csv

python stopword.py
# → Xuất: data_clean1.csv + data_clean1.txt

# --- LUỒNG TXT ---
python comment_extractor.py --url "https://facebook.com/post/123" --platform facebook
python comment_extractor.py --url "https://tiktok.com/@user/video/456" --platform tiktok
# → Xuất: data1.txt, data_clean.txt, data_clean1.txt (tự động cả 3)

# --- TF-IDF ---
python tfidf_vectorizer.py
# → Xuất: tfidf_matrix.npz, tfidf_vocab.json, tfidf_vectorizer.pkl

# --- TEEN CODE (demo & xuất JSON) ---
python teen_code.py
# → Chạy demo + xuất teen_code_dict.json
```

---

## Thư viện cần cài đặt

```bash
pip install playwright pandas scikit-learn joblib scipy
playwright install chromium
```

---

## 🐛 Known Issues & Roadmap

Ghi nhận toàn bộ điểm sai, thiếu sót — đã fix hay chưa — và thứ tự ưu tiên xử lý.

---

### ✅ Đã fix

| # | Vấn đề | File liên quan | Cách đã sửa |
|---|--------|----------------|-------------|
| F1 | `stopword.py` đọc `data.txt` không tồn tại | `stopword.py` | Sửa thành `data1.txt` |
| F2 | `text_cleaner.py` xuất nhầm ra `data_clean1.csv` thay vì `data_clean.csv` | `text_cleaner.py` | Sửa đúng output path |
| F3 | `text_cleaner.py` vừa clean vừa lọc stopword trong cùng 1 hàm, sai pipeline | `text_cleaner.py` | Tách riêng: chỉ clean + teen code |
| F4 | Không có bước chuẩn hoá teen code trong bất kỳ file nào | tất cả | Tạo `teen_code.py`, tích hợp vào `text_cleaner.py`, `stopword.py`, `comment_extractor.py` |
| F5 | Emoji còn sót lại sau khi lọc stopword (`:)))`, `😁` vẫn còn trong output) | `stopword.py`, `comment_extractor.py` | Thêm bước xóa emoji trước khi lọc stopword |
| F6 | `stopword.py` không có bước clean trước khi lọc (nhận text thô, chứa emoji) | `stopword.py` | Thêm `clean_text_basic()` vào `remove_stopwords()` |
| F7 | Tên hàm và tên cột không nhất quán giữa các file (`lam_sach_van_ban` vs `clean_text_basic`, `NoiDung_Da_Tach_Tu` vs `noi_dung_da_loc`) | `text_cleaner.py` | Chuẩn hoá lại tên cột thành `noi_dung_da_lam_sach` / `noi_dung_da_loc` |
| F8 | `help` trong argparse vẫn ghi "shopee, tiki" nhưng config chỉ có facebook, tiktok | `comment_scraper.py`, `comment_extractor.py` | *(Còn trong code nhưng không ảnh hưởng runtime)* |

---

### 🔴 Chưa fix — Ưu tiên 1 (Bắt buộc — chặn toàn bộ pipeline ML)

| # | Vấn đề | File liên quan | Cần làm |
|---|--------|----------------|---------|
| **P1** | **Không có cột nhãn (label)** trong dữ liệu. Naive Bayes là Supervised Learning — bắt buộc phải có nhãn `tích_cực / tiêu_cực / trung_tính` để train. Không có nhãn = không thể train bất kỳ mô hình nào. | `data.csv` | Gán nhãn thủ công cho từng dòng, thêm cột `nhan` vào `data.csv` |
| **P2** | **Không có file train model**. Pipeline dừng ở bước TF-IDF, chưa có bước train `MultinomialNB`, đánh giá, hay predict. | *(thiếu file)* | Tạo file `train_model.py` bao gồm: `train_test_split` → `MultinomialNB.fit()` → `classification_report` |
| **P3** | **Dữ liệu quá nhỏ** (~150 dòng, chủ yếu là bình luận hài hước về xe đạp/hoá học). Không đủ để học được pattern có ý nghĩa. Minimum khuyến nghị: 500+ mẫu, mỗi class ≥100 mẫu. | `data.csv`, `data1.txt` | Thu thập thêm dữ liệu từ nhiều bài viết, nhiều chủ đề hơn |

---

### 🟡 Chưa fix — Ưu tiên 2 (Quan trọng — ảnh hưởng chất lượng ML)

| # | Vấn đề | File liên quan | Cần làm |
|---|--------|----------------|---------|
| **P4** | **Không có word segmentation (tách từ tiếng Việt)**. Hiện tại tách theo khoảng trắng. "giao hàng" bị split thành `["giao", "hàng"]` thay vì `["giao_hàng"]` → mất nghĩa từ ghép. | tất cả file clean | Tích hợp `underthesea.word_tokenize()` sau bước clean, nối từ ghép bằng `_` |
| **P5** | **Không có chuẩn hoá Unicode NFC**. Dữ liệu scrape từ Facebook/TikTok có thể dùng NFD — cùng một từ nhưng khác code point → TF-IDF tạo 2 feature riêng. | tất cả file clean | Thêm `unicodedata.normalize('NFC', text)` làm bước đầu tiên trong mọi hàm clean |
| **P6** | **Stopword list chứa từ `"không"` và `"được"`** — cả hai là từ phủ định/quan trọng trong sentiment analysis. Loại bỏ chúng làm mất nghĩa câu: `"sản phẩm không tệ"` → `"sản phẩm tệ"`. | `stopwords-vi.json` | Xoá `"không"`, `"chưa"`, `"chẳng"`, `"được"` khỏi danh sách stopwords |
| **P7** | **TF-IDF `min_df=2`** với dataset ~150 dòng quá chặt — loại bỏ hầu hết từ, chỉ còn ~148 features. Với dataset nhỏ nên `min_df=1`. | `tfidf_vectorizer.py` | Giảm `min_df` xuống `1` khi dataset < 500 dòng |
| **P8** | **Trùng lặp code**: `load_stopwords()`, `clean_text_basic()`, `remove_stopwords()` được viết lại ở 3 file khác nhau (`text_cleaner.py`, `stopword.py`, `comment_extractor.py`). | 3 file trên | Gom vào `utils.py` dùng chung, import từ đó |

---

### 🟠 Chưa fix — Ưu tiên 3 (Nên có — hoàn thiện project)

| # | Vấn đề | File liên quan | Cần làm |
|---|--------|----------------|---------|
| **P9** | **Không có `requirements.txt`** — người dùng mới không biết cần cài gì. | *(thiếu file)* | Tạo `requirements.txt` với: `playwright`, `pandas`, `scikit-learn`, `joblib`, `scipy`, `underthesea` |
| **P10** | **Không có `.gitignore`** — `__pycache__/`, `*.pkl`, `*.npz`, `*.csv` (data nhạy cảm) đang bị commit lên git. | *(thiếu file)* | Tạo `.gitignore` phù hợp |
| **P11** | **Không có cross-validation**. Dùng 1 lần `train_test_split` với dataset nhỏ rất dễ overfit/underfit tuỳ lần random. | *(chưa có train_model.py)* | Dùng `StratifiedKFold` (k=5) thay vì split 1 lần |
| **P12** | **Không có confusion matrix / visualization**. Khó biết model nhầm ở đâu. | *(chưa có train_model.py)* | Thêm `confusion_matrix`, `classification_report`, vẽ heatmap bằng `matplotlib` |
| **P13** | **`claude.md` (tài liệu lý thuyết) không khớp với code thực tế**. Mô tả pipeline 6 bước nhưng code chỉ thực hiện ~3 bước, và bước nào implement cũng khác mô tả. | `claude.md` | Cập nhật lại `claude.md` theo đúng code hiện tại |
| **P14** | **Dữ liệu scrape lẫn metadata** (tên trang, hashtag, timestamp, UI text như "Xem 39 câu trả lời"). Những dòng này lọt qua clean và làm nhiễu TF-IDF. | `comment_scraper.py`, `data.csv` | Thêm bộ lọc độ dài tối thiểu (ví dụ: bỏ dòng < 5 từ) và loại các pattern metadata |

---

### 📋 Thứ tự fix đề xuất

```
Ngay bây giờ (chặn ML):
  P1 → Gán nhãn dữ liệu
  P3 → Thu thập thêm data

Sau khi có đủ data có nhãn:
  P6 → Sửa stopword list (xoá "không", "chưa")
  P5 → Thêm normalize Unicode NFC
  P4 → Tích hợp underthesea word segmentation
  P7 → Điều chỉnh min_df theo kích thước dataset
  P2 → Viết train_model.py

Hoàn thiện:
  P8 → Tách utils.py dùng chung
  P9 → Tạo requirements.txt
  P10 → Tạo .gitignore
  P11 + P12 → Cross-validation + Visualization
  P13 → Cập nhật claude.md
  P14 → Lọc metadata trong scraper
```