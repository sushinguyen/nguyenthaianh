# 📋 MÔ TẢ DỰ ÁN — Naive Bayes Comment Analysis

## Tổng quan

Hệ thống bốc tách bình luận tự động từ **Facebook** và **TikTok**
bằng trình duyệt ảo Playwright, sau đó làm sạch dữ liệu qua nhiều bước
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
       │    data.csv              ← Dữ liệu thô (bảng/cột)
       │         │
       │         ├──▶ text_cleaner.py ──▶ data_clean.csv
       │         │     (in thường, dấu câu, khoảng trắng — giữ nguyên nghĩa)
       │         │
       │         └──▶ stopword.py ──▶ data_clean1.csv ─┐
       │               (clean + loại bỏ stopwords)      │
       │                                                ├──▶ tfidf_vectorizer.py
       └─── LUỒNG TXT ─────────────────────────────────│        │
            comment_extractor.py                        │        ▼
                 │                                      │   tfidf_matrix.npz
                 ▼                                      │   tfidf_vocab.json
            data1.txt              ← Dữ liệu thô      │   tfidf_vectorizer.pkl
                 │                                      │
                 ├──▶ data_clean.txt                    │
                 │     (in thường, xóa emoji, dấu câu)  │
                 │                                      │
                 └──▶ data_clean1.txt ──────────────────┘
                       (clean + loại bỏ stopwords)
```

---

## Mô tả từng file

### 🔧 Scripts (Code)

| File                   | Chức năng                                                       |
|------------------------|-----------------------------------------------------------------|
| `comment_scraper.py`   | Bốc tách bình luận → xuất **data.csv**                          |
| `comment_extractor.py` | Bốc tách bình luận → xuất **data1.txt**, **data_clean.txt**, **data_clean1.txt** |
| `text_cleaner.py`      | Làm sạch CSV: in thường, dấu câu, khoảng trắng → **data_clean.csv** |
| `stopword.py`          | Lọc stopwords cho cả CSV và TXT → **data_clean1.csv**, **data_clean1.txt** |
| `stopwords-vi.json`    | Từ điển stopwords tiếng Việt (dùng chung cho cả 2 luồng)        |
| `tfidf_vectorizer.py`  | Vector hoá TF-IDF: chuyển văn bản → ma trận số cho Naive Bayes  |

### 📄 Dữ liệu — Luồng CSV

| File               | Nội dung                                                          |
|--------------------|-------------------------------------------------------------------|
| `data.csv`         | Dữ liệu thô dạng bảng (platform, username, text, rating, timestamp) |
| `data_clean.csv`   | Đã xử lý đơn giản: in thường, xóa dấu câu, khoảng trắng — **giữ nguyên nghĩa** |
| `data_clean1.csv`  | Đã clean + loại bỏ stopwords — sẵn sàng cho vector hoá           |

### 📄 Dữ liệu — Luồng TXT

| File               | Nội dung                                                          |
|--------------------|-------------------------------------------------------------------|
| `data1.txt`        | Dữ liệu thô văn bản (tên, rating, nội dung, thời gian)           |
| `data_clean.txt`   | Đã xử lý đơn giản: in thường, xóa emoji, dấu câu, khoảng trắng — **giữ nguyên nghĩa** |
| `data_clean1.txt`  | Đã clean + loại bỏ stopwords — sẵn sàng cho vector hoá           |

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

## Lưu ý quan trọng

> ⚠️ Dữ liệu trong `.csv` và `.txt` là **KHÁC NHAU**, được xử lý qua **2 luồng riêng biệt**.
> - Luồng CSV: `comment_scraper.py` → `text_cleaner.py` / `stopword.py`
> - Luồng TXT: `comment_extractor.py` (tích hợp sẵn clean + stopword)

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
```