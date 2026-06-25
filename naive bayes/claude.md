# Tiền Xử Lý Văn Bản Tiếng Việt cho Naive Bayes

> Tài liệu này trình bày chi tiết từng bước trong pipeline tiền xử lý văn bản tiếng Việt phục vụ bài toán phân loại cảm xúc (Sentiment Analysis) bằng thuật toán Naive Bayes.

---

## Mục lục

1. [Tổng quan pipeline](#1-tổng-quan-pipeline)
2. [Bước 1 — Làm sạch văn bản (Cleaning)](#2-bước-1--làm-sạch-văn-bản-cleaning)
3. [Bước 2 — Chuẩn hoá Teen Code](#3-bước-2--chuẩn-hoá-teen-code)
4. [Bước 3 — Tokenize (Tách từ)](#4-bước-3--tokenize-tách-từ)
5. [Bước 4 — Loại Stopwords](#5-bước-4--loại-stopwords)
6. [Bước 5 — Chuẩn hoá Unicode & Dấu câu](#6-bước-5--chuẩn-hoá-unicode--dấu-câu)
7. [Bước 6 — Vector hoá (TF-IDF)](#7-bước-6--vector-hoá-tf-idf)
8. [Pipeline hoàn chỉnh](#8-pipeline-hoàn-chỉnh)
9. [Ví dụ minh hoạ đầy đủ](#9-ví-dụ-minh-hoạ-đầy-đủ)
10. [Thư viện cần cài đặt](#10-thư-viện-cần-cài-đặt)

---

## 1. Tổng quan pipeline

```
Văn bản thô
    │
    ▼
[Bước 1] Làm sạch (Cleaning)
    │   Lowercase, bỏ emoji, số, dấu câu
    ▼
[Bước 2] Chuẩn hoá teen code
    │   ko→không, dc→được, mk→mình ...
    ▼
[Bước 3] Tokenize (Tách từ)
    │   underthesea / pyvi — xử lý từ ghép tiếng Việt
    ▼
[Bước 4] Loại Stopwords
    │   Bỏ từ không mang nghĩa: "và", "thì", "là" ...
    ▼
[Bước 5] Chuẩn hoá Unicode
    │   NFC normalization, chuẩn hoá dấu thanh
    ▼
[Bước 6] Vector hoá TF-IDF
    │   Chuyển danh sách từ → ma trận số
    ▼
Đầu vào cho MultinomialNB
```

**Tại sao tiếng Việt cần xử lý đặc biệt?**

- Tiếng Việt có **từ ghép** ("giao hàng", "sản phẩm") → không thể tách theo khoảng trắng như tiếng Anh.
- Bình luận online chứa nhiều **teen code** ("ko", "dc", "mk") → cần từ điển chuẩn hoá riêng.
- **Dấu thanh** có thể được encode theo nhiều cách khác nhau (NFC vs NFD) → phải chuẩn hoá.

---

## 2. Bước 1 — Làm sạch văn bản (Cleaning)

### Mục tiêu

Loại bỏ tất cả các ký tự không liên quan đến ý nghĩa ngữ nghĩa:
- Emoji, ký tự đặc biệt
- Dấu câu, dấu chấm than, dấu hỏi
- Số (điểm đánh giá như "5/5 sao" không giúp ích cho mô hình)
- Khoảng trắng thừa

### Code

```python
import re
import unicodedata

def clean_text(text: str) -> str:
    """
    Làm sạch văn bản thô tiếng Việt.
    
    Args:
        text: Chuỗi văn bản đầu vào
    Returns:
        Chuỗi đã được làm sạch
    """
    # 1. Lowercase
    text = text.lower()
    
    # 2. Bỏ emoji (Unicode range)
    text = re.sub(r'[\U00010000-\U0010ffff]', ' ', text, flags=re.UNICODE)
    
    # 3. Bỏ URL
    text = re.sub(r'http\S+|www\.\S+', ' ', text)
    
    # 4. Bỏ địa chỉ email
    text = re.sub(r'\S+@\S+', ' ', text)
    
    # 5. Bỏ số
    text = re.sub(r'\d+', ' ', text)
    
    # 6. Bỏ dấu câu và ký tự đặc biệt (giữ lại chữ cái và khoảng trắng)
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # 7. Chuẩn hoá khoảng trắng
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
```

### Ví dụ

```
Input:  "Sản phẩm NÀY quá TỆ!!! Giao hàng chậm... ko mua nữa 😡 chỉ 2/5 sao"
Output: "sản phẩm này quá tệ giao hàng chậm ko mua nữa chỉ sao"
```

### Lưu ý

- **Không bỏ dấu tiếng Việt** (ă, â, đ, ê, ô, ơ, ư...) vì chúng mang nghĩa quan trọng.
- Ký tự `_` thường được giữ lại vì sẽ dùng để nối từ ghép ở bước sau.

---

## 3. Bước 2 — Chuẩn hoá Teen Code

### Mục tiêu

Bình luận tiếng Việt trên mạng xã hội thường viết tắt rất nhiều. Nếu không chuẩn hoá, mô hình sẽ coi "ko" và "không" là **hai từ hoàn toàn khác nhau**, dù cùng nghĩa.

### Từ điển teen code phổ biến

```python
TEEN_CODE_DICT = {
    # Phủ định
    'ko':  'không',
    'k':   'không',
    'kh':  'không',
    'hok': 'không',
    
    # Động từ / trạng từ
    'dc':  'được',
    'đc':  'được',
    'bt':  'bình thường',
    'bth': 'bình thường',
    'r':   'rồi',
    'lm':  'làm',
    'ik':  'đi',
    'ms':  'mới',
    'vs':  'với',
    'cg':  'cũng',
    'bik': 'biết',
    
    # Đại từ
    'mk':  'mình',
    'mn':  'mọi người',
    'tui': 'tôi',
    'mik': 'mình',
    
    # Danh từ phổ biến
    'sp':  'sản phẩm',
    'ck':  'chồng',
    'vd':  'ví dụ',
    'tl':  'trả lời',
    'hl':  'hài lòng',
    
    # Mức độ / cảm xúc
    'nhiu':  'nhiều',
    'nhìu':  'nhiều',
    'qá':    'quá',
    'wa':    'quá',
    'tuyệt': 'tuyệt vời',
}

def normalize_teen_code(text: str) -> str:
    """
    Thay thế teen code bằng từ chuẩn.
    
    Args:
        text: Chuỗi đã được làm sạch (lowercase)
    Returns:
        Chuỗi đã được chuẩn hoá
    """
    words = text.split()
    normalized = [TEEN_CODE_DICT.get(word, word) for word in words]
    return ' '.join(normalized)
```

### Ví dụ

```
Input:  "sản phẩm này quá tệ giao hàng chậm ko mua nữa"
Output: "sản phẩm này quá tệ giao hàng chậm không mua nữa"
```

### Lưu ý

- Từ điển cần **cập nhật liên tục** vì teen code thay đổi theo thời gian và theo từng nền tảng.
- Nên xây dựng từ điển dựa trên **dữ liệu thực tế** của dataset bạn đang dùng.
- Một số từ ngắn như `"k"` cần cẩn thận vì có thể là tên riêng hoặc ký hiệu.

---

## 4. Bước 3 — Tokenize (Tách từ)

### Tại sao tiếng Việt khó tách từ?

Tiếng Anh: `"giao hàng"` → `["giao", "hàng"]` (2 từ đơn, tách theo space là đúng)

Tiếng Việt: `"giao hàng"` là **1 từ ghép** có nghĩa là "delivery". Nếu tách thành 2 từ:
- `"giao"` (giao cho ai đó) — nghĩa khác
- `"hàng"` (hàng hoá) — nghĩa khác

→ Phải dùng **word segmentation** đặc biệt cho tiếng Việt.

### Dùng underthesea

```python
from underthesea import word_tokenize

def tokenize_vi(text: str) -> list[str]:
    """
    Tách từ tiếng Việt bằng underthesea.
    
    Args:
        text: Chuỗi văn bản đã làm sạch
    Returns:
        Danh sách token (từ đã được tách)
    """
    tokens = word_tokenize(text)
    
    # Nối từ ghép bằng dấu _ để TF-IDF nhận ra là 1 đơn vị
    # "giao hàng" → "giao_hàng"
    tokens = [t.replace(' ', '_') for t in tokens]
    
    # Bỏ token rỗng
    tokens = [t for t in tokens if len(t) > 0]
    
    return tokens
```

### Ví dụ

```python
text = "sản phẩm này quá tệ giao hàng chậm không mua nữa"
tokens = word_tokenize(text)
# → ['sản phẩm', 'này', 'quá', 'tệ', 'giao hàng', 'chậm', 'không', 'mua', 'nữa']

# Sau khi nối dấu _:
# → ['sản_phẩm', 'này', 'quá', 'tệ', 'giao_hàng', 'chậm', 'không', 'mua', 'nữa']
```

### So sánh underthesea vs pyvi

| Tiêu chí | underthesea | pyvi |
|---|---|---|
| Độ chính xác | Cao hơn | Trung bình |
| Tốc độ | Chậm hơn | Nhanh hơn |
| Cài đặt | Cần model download | Nhẹ hơn |
| Phù hợp với | Dataset lớn, cần chính xác | Dataset nhỏ, cần nhanh |

---

## 5. Bước 4 — Loại Stopwords

### Stopwords là gì?

Stopwords là những từ xuất hiện rất nhiều trong văn bản nhưng **không mang nghĩa cảm xúc** cụ thể. Nếu giữ lại, chúng sẽ làm "nhiễu" mô hình vì chiếm tỷ trọng cao trong TF-IDF.

### Ví dụ stopwords tiếng Việt

```
và, là, thì, mà, của, cho, với, có, đã, sẽ, đang, rất, quá, 
nữa, còn, vẫn, hay, hoặc, nhưng, vì, nên, để, vào, ra, lên, 
xuống, trong, ngoài, trên, dưới, tôi, bạn, họ, chúng, ta, các, 
một, những, này, kia, đó, ấy, vậy, thôi, nào, gì, sao
```

### Code

```python
# Cách 1: Dùng danh sách tự xây dựng
STOPWORDS_VI = {
    'và', 'là', 'thì', 'mà', 'của', 'cho', 'với', 'có', 'đã',
    'sẽ', 'đang', 'rất', 'quá', 'nữa', 'còn', 'vẫn', 'hay',
    'hoặc', 'nhưng', 'vì', 'nên', 'để', 'vào', 'ra', 'lên',
    'xuống', 'trong', 'ngoài', 'trên', 'dưới', 'tôi', 'bạn',
    'họ', 'chúng', 'ta', 'các', 'một', 'những', 'này', 'kia',
    'đó', 'ấy', 'vậy', 'thôi', 'nào', 'gì', 'sao', 'thế',
    'mình', 'người', 'hơi', 'so', 'chỉ', 'cũng'
}

def remove_stopwords(tokens: list[str]) -> list[str]:
    """
    Loại bỏ stopwords khỏi danh sách token.
    
    Args:
        tokens: Danh sách token từ bước tokenize
    Returns:
        Danh sách token sau khi loại bỏ stopwords
    """
    return [t for t in tokens if t not in STOPWORDS_VI and len(t) > 1]

# Cách 2: Tải danh sách stopwords từ file
def load_stopwords(filepath: str) -> set:
    with open(filepath, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())
```

### Ví dụ

```
Input tokens:  ['sản_phẩm', 'này', 'quá', 'tệ', 'giao_hàng', 'chậm', 'không', 'mua', 'nữa']
Output tokens: ['sản_phẩm', 'tệ', 'giao_hàng', 'chậm', 'không', 'mua']
```

### Lưu ý quan trọng

> ⚠️ **Không nên loại bỏ từ phủ định** như `"không"`, `"chẳng"`, `"chưa"` ra khỏi stopwords!  
> Ví dụ: `"sản phẩm không tệ"` (tích cực) vs `"sản phẩm tệ"` (tiêu cực) → khác nhau hoàn toàn.

Nếu loại bỏ `"không"`, cả hai câu đều thành `"sản_phẩm tệ"` → mô hình bị nhầm.

---

## 6. Bước 5 — Chuẩn hoá Unicode & Dấu câu

### Vấn đề Unicode tiếng Việt

Tiếng Việt có thể được biểu diễn theo 2 chuẩn Unicode:

| Chuẩn | Ký tự "ộ" | Mô tả |
|---|---|---|
| NFC (Composed) | `ộ` (1 code point) | Ký tự dựng sẵn |
| NFD (Decomposed) | `o` + `̣` + `̂` (3 code points) | Ký tự tổ hợp |

Nếu không chuẩn hoá, `"giao"` (NFC) và `"giao"` (NFD) sẽ được coi là **2 từ khác nhau**!

### Code

```python
import unicodedata

def normalize_unicode(text: str) -> str:
    """
    Chuẩn hoá Unicode về dạng NFC.
    
    Args:
        text: Chuỗi văn bản
    Returns:
        Chuỗi đã được chuẩn hoá Unicode
    """
    return unicodedata.normalize('NFC', text)
```

### Khi nào áp dụng?

Nên áp dụng **ngay đầu tiên**, trước cả bước cleaning, để đảm bảo tất cả ký tự tiếng Việt được xử lý đúng.

---

## 7. Bước 6 — Vector hoá (TF-IDF)

### TF-IDF là gì?

TF-IDF (Term Frequency - Inverse Document Frequency) chuyển văn bản thành vector số mà mô hình có thể xử lý.

**TF (Term Frequency):** Từ xuất hiện bao nhiêu lần trong văn bản này?

```
TF(t, d) = số lần từ t xuất hiện trong văn bản d / tổng số từ trong d
```

**IDF (Inverse Document Frequency):** Từ này có phổ biến trong toàn bộ corpus không?

```
IDF(t) = log(N / df(t))

Trong đó:
  N    = tổng số văn bản
  df(t) = số văn bản chứa từ t
```

**TF-IDF = TF × IDF**

Từ xuất hiện nhiều trong 1 văn bản nhưng ít trong corpus → TF-IDF cao → từ đặc trưng.

### Ví dụ trực quan

| Từ | TF | IDF | TF-IDF | Ý nghĩa |
|---|---|---|---|---|
| "tệ" | cao | cao | **cao** | Từ đặc trưng cảm xúc |
| "giao_hàng" | trung bình | trung bình | trung bình | Từ chủ đề |
| "sản_phẩm" | cao | thấp (xuất hiện ở mọi bình luận) | **thấp** | Từ phổ biến, ít đặc trưng |

### Code

```python
from sklearn.feature_extraction.text import TfidfVectorizer

def build_tfidf(corpus: list[str], max_features: int = 10000):
    """
    Xây dựng TF-IDF vectorizer và transform corpus.
    
    Args:
        corpus: Danh sách văn bản đã được tiền xử lý (mỗi phần tử là 1 chuỗi từ)
        max_features: Số lượng từ tối đa trong từ vựng
    Returns:
        vectorizer: Đối tượng TfidfVectorizer đã fit
        X: Ma trận TF-IDF (n_samples × n_features)
    """
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        ngram_range=(1, 2),      # Unigram và bigram
        min_df=2,                 # Bỏ từ chỉ xuất hiện ở 1 văn bản
        max_df=0.95,              # Bỏ từ xuất hiện ở >95% văn bản
        sublinear_tf=True         # Dùng log(TF) thay vì TF thô
    )
    
    X = vectorizer.fit_transform(corpus)
    return vectorizer, X
```

### Tại sao dùng TF-IDF thay vì Bag of Words?

| | Bag of Words | TF-IDF |
|---|---|---|
| Cách tính | Đếm số lần xuất hiện | Tính trọng số theo độ phổ biến |
| Từ phổ biến | Điểm cao (sai) | Điểm thấp (đúng) |
| Từ đặc trưng | Điểm bình thường | Điểm cao (tốt hơn) |
| Phù hợp Naive Bayes | ✓ | ✓✓ (tốt hơn) |

---

## 8. Pipeline hoàn chỉnh

```python
import re
import unicodedata
from underthesea import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# =============================================
# CÁC HẰNG SỐ
# =============================================

TEEN_CODE_DICT = {
    'ko': 'không', 'k': 'không', 'kh': 'không', 'hok': 'không',
    'dc': 'được',  'đc': 'được',
    'mk': 'mình',  'mn': 'mọi người', 'tui': 'tôi',
    'sp': 'sản phẩm', 'bt': 'bình thường', 'bth': 'bình thường',
    'r':  'rồi', 'lm': 'làm', 'vs': 'với', 'cg': 'cũng',
    'nhiu': 'nhiều', 'nhìu': 'nhiều', 'wa': 'quá', 'qá': 'quá',
    'hl': 'hài lòng', 'tl': 'trả lời',
}

STOPWORDS_VI = {
    'và', 'là', 'thì', 'mà', 'của', 'cho', 'với', 'có', 'đã',
    'sẽ', 'đang', 'rất', 'quá', 'nữa', 'còn', 'vẫn', 'hay',
    'hoặc', 'nhưng', 'vì', 'nên', 'để', 'vào', 'ra', 'lên',
    'xuống', 'trong', 'ngoài', 'trên', 'dưới', 'tôi', 'bạn',
    'họ', 'chúng', 'ta', 'các', 'một', 'những', 'này', 'kia',
    'đó', 'ấy', 'vậy', 'thôi', 'nào', 'gì', 'sao', 'thế',
    'mình', 'người', 'hơi', 'so', 'chỉ', 'cũng'
    # Lưu ý: KHÔNG thêm 'không', 'chẳng', 'chưa' vào đây!
}


# =============================================
# CÁC HÀM TIỀN XỬ LÝ
# =============================================

def normalize_unicode(text: str) -> str:
    """Bước 0: Chuẩn hoá Unicode về NFC."""
    return unicodedata.normalize('NFC', text)


def clean_text(text: str) -> str:
    """Bước 1: Làm sạch văn bản."""
    text = text.lower()
    text = re.sub(r'[\U00010000-\U0010ffff]', ' ', text, flags=re.UNICODE)
    text = re.sub(r'http\S+|www\.\S+', ' ', text)
    text = re.sub(r'\S+@\S+', ' ', text)
    text = re.sub(r'\d+', ' ', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def normalize_teen_code(text: str) -> str:
    """Bước 2: Chuẩn hoá teen code."""
    words = text.split()
    return ' '.join(TEEN_CODE_DICT.get(w, w) for w in words)


def tokenize_vi(text: str) -> list:
    """Bước 3: Tách từ tiếng Việt."""
    tokens = word_tokenize(text)
    tokens = [t.replace(' ', '_') for t in tokens]
    return [t for t in tokens if len(t) > 0]


def remove_stopwords(tokens: list) -> list:
    """Bước 4: Loại stopwords."""
    return [t for t in tokens if t not in STOPWORDS_VI and len(t) > 1]


# =============================================
# PIPELINE TỔNG HỢP
# =============================================

def preprocess(text: str) -> str:
    """
    Pipeline tiền xử lý đầy đủ.
    
    Input:  "Sản phẩm NÀY quá TỆ!!! ko mua nữa 😡"
    Output: "sản_phẩm tệ không mua"
    """
    text = normalize_unicode(text)      # Bước 0
    text = clean_text(text)             # Bước 1
    text = normalize_teen_code(text)    # Bước 2
    tokens = tokenize_vi(text)          # Bước 3
    tokens = remove_stopwords(tokens)   # Bước 4
    return ' '.join(tokens)


# =============================================
# TRAIN MÔ HÌNH
# =============================================

def train_sentiment_model(texts: list, labels: list):
    """
    Tiền xử lý + train MultinomialNB.
    
    Args:
        texts:  Danh sách văn bản thô
        labels: Nhãn tương ứng ('tich_cuc', 'tieu_cuc', 'trung_tinh')
    Returns:
        vectorizer, model, report
    """
    # Tiền xử lý toàn bộ corpus
    processed = [preprocess(t) for t in texts]
    
    # Chia train/test
    X_train, X_test, y_train, y_test = train_test_split(
        processed, labels, test_size=0.2, random_state=42, stratify=labels
    )
    
    # Vector hoá TF-IDF
    vectorizer = TfidfVectorizer(
        max_features=10000,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95,
        sublinear_tf=True
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec  = vectorizer.transform(X_test)
    
    # Train Naive Bayes
    model = MultinomialNB(alpha=1.0)   # alpha=1.0 là Laplace smoothing
    model.fit(X_train_vec, y_train)
    
    # Đánh giá
    y_pred = model.predict(X_test_vec)
    report = classification_report(y_test, y_pred)
    
    return vectorizer, model, report


# =============================================
# DỰ ĐOÁN
# =============================================

def predict(text: str, vectorizer, model) -> str:
    """
    Dự đoán cảm xúc cho 1 văn bản mới.
    
    Args:
        text: Văn bản thô cần dự đoán
    Returns:
        Nhãn dự đoán
    """
    processed = preprocess(text)
    vec = vectorizer.transform([processed])
    return model.predict(vec)[0]
```

---

## 9. Ví dụ minh hoạ đầy đủ

### Câu 1 (Tiêu cực)

```
Input:   "Sản phẩm NÀY quá TỆ!!! Giao hàng chậm... ko mua nữa 😡 chỉ 2/5 sao"

Sau B0:  "Sản phẩm NÀY quá TỆ!!! Giao hàng chậm... ko mua nữa 😡 chỉ 2/5 sao"  [Unicode NFC]
Sau B1:  "sản phẩm này quá tệ giao hàng chậm ko mua nữa chỉ sao"               [lowercase, clean]
Sau B2:  "sản phẩm này quá tệ giao hàng chậm không mua nữa chỉ sao"            [ko→không]
Sau B3:  ["sản_phẩm","này","quá","tệ","giao_hàng","chậm","không","mua","nữa","chỉ","sao"]
Sau B4:  ["sản_phẩm","tệ","giao_hàng","chậm","không","mua"]

TF-IDF:  {"tệ": 0.82, "chậm": 0.71, "không": 0.43, "giao_hàng": 0.38, ...}
→ Dự đoán: TIÊU CỰC ✓
```

### Câu 2 (Tích cực)

```
Input:   "Hàng đẹp lắm, đóng gói cẩn thận, giao nhanh dc, mk rất hài lòng!! 5 sao"

Sau B1:  "hàng đẹp lắm đóng gói cẩn thận giao nhanh dc mk rất hài lòng sao"
Sau B2:  "hàng đẹp lắm đóng gói cẩn thận giao nhanh được mình rất hài lòng sao"
Sau B3:  ["hàng","đẹp","lắm","đóng_gói","cẩn_thận","giao","nhanh","được","mình","hài_lòng"]
Sau B4:  ["hàng","đẹp","lắm","đóng_gói","cẩn_thận","giao","nhanh","được","hài_lòng"]

TF-IDF:  {"đẹp": 0.79, "hài_lòng": 0.75, "cẩn_thận": 0.68, "nhanh": 0.61, ...}
→ Dự đoán: TÍCH CỰC ✓
```

---

## 10. Thư viện cần cài đặt

```bash
# Thư viện NLP tiếng Việt
pip install underthesea    # Tokenize, POS tagging...
pip install pyvi           # Thay thế nhẹ hơn cho underthesea

# Machine Learning
pip install scikit-learn   # TF-IDF, MultinomialNB, metrics
pip install numpy pandas   # Xử lý dữ liệu

# (Tùy chọn) Tải model underthesea lần đầu
python -c "import underthesea; underthesea.download('word_sent')"
```

### Kiểm tra cài đặt

```python
from underthesea import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

# Test tokenize
print(word_tokenize("giao hàng nhanh chóng"))
# → ['giao hàng', 'nhanh chóng']

print("✓ Tất cả thư viện đã sẵn sàng!")
```

---

*Tài liệu được tổng hợp cho bài toán phân loại cảm xúc bình luận tiếng Việt với Naive Bayes.*  
*Pipeline có thể được mở rộng thêm với Stemming, Word2Vec, hoặc PhoBERT cho kết quả tốt hơn.*
