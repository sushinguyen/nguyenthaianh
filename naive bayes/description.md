# 📋 MÔ TẢ DỰ ÁN — Naive Bayes Comment Analysis

## Tổng quan

Hệ thống bốc tách bình luận tự động từ các nền tảng (Shopee, Tiki, Facebook, TikTok)
bằng trình duyệt ảo Playwright, sau đó làm sạch dữ liệu qua nhiều bước để chuẩn bị
cho mô hình phân loại Naive Bayes.

---

## Sơ đồ Pipeline

```
[Nguồn: Shopee, Facebook, TikTok, Tiki...]
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
       │         └──▶ stopword.py ──▶ data_clean1.csv
       │               (clean + loại bỏ stopwords)
       │
       └─── LUỒNG TXT ──────────────────────────────────────────────
            comment_extractor.py
                 │
                 ▼
            data1.txt              ← Dữ liệu thô (văn bản thuần)
                 │
                 ├──▶ data_clean.txt
                 │     (in thường, xóa emoji, dấu câu, khoảng trắng — giữ nguyên nghĩa)
                 │
                 └──▶ data_clean1.txt
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

### 📄 Dữ liệu — Luồng CSV

| File               | Nội dung                                                          |
|--------------------|-------------------------------------------------------------------|
| `data.csv`         | Dữ liệu thô dạng bảng (platform, username, text, rating, timestamp) |
| `data_clean.csv`   | Đã xử lý đơn giản: in thường, xóa dấu câu, khoảng trắng — **giữ nguyên nghĩa** |
| `data_clean1.csv`  | Đã clean + loại bỏ stopwords — sẵn sàng cho mô hình             |

### 📄 Dữ liệu — Luồng TXT

| File               | Nội dung                                                          |
|--------------------|-------------------------------------------------------------------|
| `data1.txt`        | Dữ liệu thô văn bản (tên, rating, nội dung, thời gian)           |
| `data_clean.txt`   | Đã xử lý đơn giản: in thường, xóa emoji, dấu câu, khoảng trắng — **giữ nguyên nghĩa** |
| `data_clean1.txt`  | Đã clean + loại bỏ stopwords — sẵn sàng cho mô hình             |

---

## Lưu ý quan trọng

> ⚠️ Dữ liệu trong `.csv` và `.txt` là **KHÁC NHAU**, được xử lý qua **2 luồng riêng biệt**.
> - Luồng CSV: `comment_scraper.py` → `text_cleaner.py` / `stopword.py`
> - Luồng TXT: `comment_extractor.py` (tích hợp sẵn clean + stopword)

---

## Cách sử dụng

```bash
# --- LUỒNG CSV ---
python comment_scraper.py --url "https://tiktok.com/..." --platform tiktok
# → Xuất: data.csv

python text_cleaner.py
# → Xuất: data_clean.csv

python stopword.py
# → Xuất: data_clean1.csv + data_clean1.txt

# --- LUỒNG TXT ---
python comment_extractor.py --url "https://tiktok.com/..." --platform tiktok
# → Xuất: data1.txt, data_clean.txt, data_clean1.txt (tự động cả 3)
```