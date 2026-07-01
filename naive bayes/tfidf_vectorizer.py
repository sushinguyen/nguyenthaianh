"""
=============================================================================
TF-IDF VECTORIZER — Công cụ phân tích & khảo sát vocabulary (STANDALONE)
=============================================================================

⚠️  LƯU Ý QUAN TRỌNG VỀ PIPELINE:
    File này là công cụ STANDALONE để khảo sát và phân tích vocabulary.
    Nó KHÔNG phải một bước bắt buộc trong pipeline huấn luyện Naive Bayes.

    train_model.py đã tự tạo TfidfVectorizer bên trong sklearn.Pipeline
    (kết hợp với MultinomialNB) nên:
      - KHÔNG cần chạy file này trước train_model.py
      - tfidf_vectorizer.pkl sinh ra ở đây KHÁC với vectorizer trong nb_model.pkl
      - nb_model.pkl đã chứa cả vectorizer + model → dùng để predict

    Dùng file này khi muốn:
      - Xem top từ có TF-IDF cao nhất
      - Kiểm tra vocabulary trước khi train
      - Xuất ma trận TF-IDF ra file .npz để phân tích riêng

Chuyển dữ liệu đã tiền xử lý (data_clean1.csv / data_clean1.txt) thành
ma trận TF-IDF, sẵn sàng đưa vào mô hình MultinomialNB.

Tinh chỉnh phù hợp với hệ thống:
  - Hỗ trợ cả 2 luồng: CSV (cột noi_dung_da_loc) và TXT (mỗi dòng 1 bình luận)
  - Tham số TF-IDF được điều chỉnh cho dataset nhỏ (~67 bình luận)
  - Token pattern nhận diện từ ghép có dấu _ (giao_hàng, sản_phẩm)

Output:
  - tfidf_matrix.npz      : Ma trận TF-IDF dạng sparse
  - tfidf_vocab.json       : Từ điển vocabulary {từ: index}
  - tfidf_vectorizer.pkl   : Vectorizer object (standalone — KHÁC nb_model.pkl)

Sử dụng:
  python tfidf_vectorizer.py
  python tfidf_vectorizer.py --input data_clean1.csv
  python tfidf_vectorizer.py --input data_clean1.txt
  python tfidf_vectorizer.py --input data_clean1.csv --top 30

Cài đặt:
  pip install scikit-learn pandas joblib scipy
"""

import os
import sys
import json
import argparse

# Fix encoding cho Windows console (cp1252 không hỗ trợ tiếng Việt)
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

import pandas as pd
import joblib
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer


# =============================================================================
# CẤU HÌNH MẶC ĐỊNH
# =============================================================================

# Thư mục hiện tại (nơi chứa script)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# File đầu vào mặc định (ưu tiên CSV)
DEFAULT_CSV_INPUT = os.path.join(CURRENT_DIR, "data_clean1.csv")
DEFAULT_TXT_INPUT = os.path.join(CURRENT_DIR, "data_clean1.txt")

# File đầu ra
OUTPUT_MATRIX = os.path.join(CURRENT_DIR, "tfidf_matrix.npz")
OUTPUT_VOCAB = os.path.join(CURRENT_DIR, "tfidf_vocab.json")
OUTPUT_VECTORIZER = os.path.join(CURRENT_DIR, "tfidf_vectorizer.pkl")

# Tên cột chứa văn bản đã lọc stopword trong CSV
CSV_COLUMN = "noi_dung_da_loc"

# Tham số TF-IDF (tinh chỉnh cho dataset nhỏ)
TFIDF_CONFIG = {
    "max_features": 5000,           # Dataset nhỏ → không cần 10000
    "ngram_range": (1, 2),          # Unigram + bigram (quan trọng cho tiếng Việt)
    "min_df": 2,                    # Bỏ từ chỉ xuất hiện ở 1 văn bản
    "max_df": 0.90,                 # Bỏ từ xuất hiện ở >90% văn bản
    "sublinear_tf": True,           # Dùng log(TF) thay vì TF thô
    "token_pattern": r"(?u)\b\w[\w_]+\b",  # Nhận diện từ ghép có dấu _
    "norm": "l2",                   # Chuẩn hoá L2 (mặc định sklearn)
    "use_idf": True,                # Bật IDF
    "smooth_idf": True,             # Tránh chia cho 0
}


# =============================================================================
# HÀM ĐỌC DỮ LIỆU
# =============================================================================

def load_corpus_csv(file_path: str, column: str = CSV_COLUMN) -> list:
    """
    Đọc corpus từ file CSV.

    Args:
        file_path: Đường dẫn file CSV
        column: Tên cột chứa văn bản đã xử lý

    Returns:
        Danh sách chuỗi văn bản (mỗi phần tử = 1 bình luận)
    """
    df = pd.read_csv(file_path, encoding="utf-8")

    if column not in df.columns:
        # Thử tên cột thay thế
        alt_columns = ["NoiDung_Da_Tach_Tu", "noi_dung", "text", "content"]
        found = None
        for alt in alt_columns:
            if alt in df.columns:
                found = alt
                break

        if found:
            print(f"  [!] Khong tim thay cot '{column}', dung cot '{found}' thay the")
            column = found
        else:
            raise KeyError(
                f"Không tìm thấy cột '{column}' trong CSV.\n"
                f"Các cột hiện có: {list(df.columns)}"
            )

    # Lấy dữ liệu, bỏ dòng trống/NaN
    corpus = df[column].dropna().astype(str).tolist()
    corpus = [text.strip() for text in corpus if text.strip()]

    return corpus


def load_corpus_txt(file_path: str) -> list:
    """
    Đọc corpus từ file TXT (mỗi dòng = 1 bình luận).

    Args:
        file_path: Đường dẫn file TXT

    Returns:
        Danh sách chuỗi văn bản
    """
    corpus = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            text = line.strip()
            if text:
                corpus.append(text)

    return corpus


def load_corpus(file_path: str) -> list:
    """
    Tự động đọc corpus từ file CSV hoặc TXT dựa trên đuôi file.

    Args:
        file_path: Đường dẫn file đầu vào

    Returns:
        Danh sách chuỗi văn bản
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".csv":
        return load_corpus_csv(file_path)
    elif ext == ".txt":
        return load_corpus_txt(file_path)
    else:
        raise ValueError(f"Định dạng file không hỗ trợ: {ext}. Chỉ hỗ trợ .csv và .txt")


# =============================================================================
# HÀM XÂY DỰNG TF-IDF
# =============================================================================

def build_tfidf(corpus: list, config: dict = None):
    """
    Xây dựng TF-IDF vectorizer và transform corpus.

    Tham số đã được tinh chỉnh cho hệ thống phân tích bình luận tiếng Việt:
      - max_features=5000: Phù hợp dataset nhỏ
      - ngram_range=(1,2): Giữ bigram cho từ ghép tiếng Việt
      - min_df=2: Loại từ quá hiếm
      - max_df=0.90: Loại từ quá phổ biến
      - sublinear_tf=True: Giảm ảnh hưởng từ lặp nhiều
      - token_pattern nhận diện từ ghép có dấu _

    Args:
        corpus: Danh sách văn bản đã tiền xử lý
        config: Dict tham số TF-IDF (mặc định dùng TFIDF_CONFIG)

    Returns:
        vectorizer: TfidfVectorizer đã fit
        matrix: Ma trận TF-IDF sparse (n_samples × n_features)
    """
    if config is None:
        config = TFIDF_CONFIG.copy()

    # Nếu corpus quá nhỏ, giảm min_df để không mất hết từ
    if len(corpus) < 10:
        config["min_df"] = 1
        print(f"  [!] Corpus rat nho ({len(corpus)} van ban) -> dat min_df=1")

    vectorizer = TfidfVectorizer(**config)
    matrix = vectorizer.fit_transform(corpus)

    return vectorizer, matrix


# =============================================================================
# HÀM LƯU KẾT QUẢ
# =============================================================================

def save_results(vectorizer, matrix, output_dir: str = CURRENT_DIR):
    """
    Lưu kết quả TF-IDF ra 3 file:
      1. tfidf_matrix.npz      — Ma trận sparse
      2. tfidf_vocab.json       — Vocabulary {từ: index}
      3. tfidf_vectorizer.pkl   — Vectorizer object

    Args:
        vectorizer: TfidfVectorizer đã fit
        matrix: Ma trận TF-IDF sparse
        output_dir: Thư mục lưu file đầu ra
    """
    # 1. Lưu ma trận sparse
    matrix_path = os.path.join(output_dir, "tfidf_matrix.npz")
    sparse.save_npz(matrix_path, matrix)
    print(f"  [SAVE] Ma tran TF-IDF   -> {matrix_path}")

    # 2. Lưu vocabulary (JSON cho dễ đọc)
    vocab_path = os.path.join(output_dir, "tfidf_vocab.json")
    vocab = vectorizer.vocabulary_
    # Chuyển key/value để JSON serializable
    vocab_serializable = {word: int(idx) for word, idx in vocab.items()}
    with open(vocab_path, "w", encoding="utf-8") as f:
        json.dump(vocab_serializable, f, ensure_ascii=False, indent=2)
    print(f"  [SAVE] Vocabulary       -> {vocab_path}")

    # 3. Lưu vectorizer object (dùng cho predict sau này)
    vectorizer_path = os.path.join(output_dir, "tfidf_vectorizer.pkl")
    joblib.dump(vectorizer, vectorizer_path)
    print(f"  [SAVE] Vectorizer (pkl) -> {vectorizer_path}")


# =============================================================================
# HÀM HIỂN THỊ KẾT QUẢ
# =============================================================================

def show_stats(corpus: list, vectorizer, matrix):
    """
    In thống kê tổng quan về ma trận TF-IDF.

    Args:
        corpus: Danh sách văn bản gốc
        vectorizer: TfidfVectorizer đã fit
        matrix: Ma trận TF-IDF sparse
    """
    n_samples, n_features = matrix.shape
    density = matrix.nnz / (n_samples * n_features) * 100

    print()
    print("  [STATS] THONG KE MA TRAN TF-IDF:")
    print(f"     So van ban (dong)  : {n_samples}")
    print(f"     So tu vung (cot)   : {n_features}")
    print(f"     Shape              : {matrix.shape}")
    print(f"     Phan tu khac 0     : {matrix.nnz}")
    print(f"     Mat do (density)   : {density:.2f}%")
    print(f"     Kich thuoc bo nho  : {matrix.data.nbytes / 1024:.1f} KB")


def show_top_features(vectorizer, matrix, n: int = 20):
    """
    Hiển thị top N từ/cụm từ có TF-IDF trung bình cao nhất trong corpus.

    Args:
        vectorizer: TfidfVectorizer đã fit
        matrix: Ma trận TF-IDF sparse
        n: Số từ hiển thị (mặc định 20)
    """
    feature_names = vectorizer.get_feature_names_out()

    # Tính TF-IDF trung bình của mỗi từ trên toàn bộ corpus
    mean_tfidf = matrix.mean(axis=0).A1  # .A1 chuyển matrix → array 1D

    # Sắp xếp giảm dần
    top_indices = mean_tfidf.argsort()[::-1][:n]

    print()
    print(f"  [TOP] TOP {n} TU / CUM TU CO TF-IDF CAO NHAT:")
    print(f"  {'-' * 45}")
    print(f"  {'STT':<5} {'Tu/cum tu':<25} {'TF-IDF TB':>10}")
    print(f"  {'-' * 45}")

    for rank, idx in enumerate(top_indices, start=1):
        word = feature_names[idx]
        score = mean_tfidf[idx]
        print(f"  {rank:<5} {word:<25} {score:>10.4f}")

    print(f"  {'-' * 45}")


def show_sample_vectors(vectorizer, matrix, corpus: list, n: int = 3):
    """
    Hiển thị vector TF-IDF của một vài văn bản mẫu.

    Args:
        vectorizer: TfidfVectorizer đã fit
        matrix: Ma trận TF-IDF sparse
        corpus: Danh sách văn bản gốc
        n: Số văn bản mẫu hiển thị
    """
    feature_names = vectorizer.get_feature_names_out()
    n = min(n, len(corpus))

    print()
    print(f"  [SAMPLE] MAU VECTOR TF-IDF ({n} van ban dau tien):")

    for i in range(n):
        print(f"\n  > Van ban [{i+1}]: \"{corpus[i][:80]}{'...' if len(corpus[i]) > 80 else ''}\"")

        # Lấy vector của văn bản này
        row = matrix[i]
        nonzero_indices = row.nonzero()[1]

        if len(nonzero_indices) == 0:
            print("    (Khong co tu nao trong vocabulary)")
            continue

        # Sắp xếp theo TF-IDF giảm dần
        scores = [(feature_names[j], row[0, j]) for j in nonzero_indices]
        scores.sort(key=lambda x: x[1], reverse=True)

        # Hiển thị tối đa 8 từ
        top_words = scores[:8]
        parts = [f"{word}: {score:.3f}" for word, score in top_words]
        print(f"    TF-IDF: {{{', '.join(parts)}}}")
        if len(scores) > 8:
            print(f"    ... và {len(scores) - 8} từ khác")


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="TF-IDF Vectorizer - Vector hoa van ban tieng Viet cho Naive Bayes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  python tfidf_vectorizer.py
  python tfidf_vectorizer.py --input data_clean1.csv
  python tfidf_vectorizer.py --input data_clean1.txt
  python tfidf_vectorizer.py --input data_clean1.csv --top 30

Output:
  tfidf_matrix.npz      — Ma trận TF-IDF (sparse)
  tfidf_vocab.json       — Từ điển vocabulary
  tfidf_vectorizer.pkl   — Vectorizer object (cho predict)
        """
    )

    parser.add_argument(
        "--input", "-i",
        default=None,
        help="File đầu vào (.csv hoặc .txt). Mặc định: tự tìm data_clean1.csv rồi data_clean1.txt"
    )
    parser.add_argument(
        "--top", "-t",
        type=int,
        default=20,
        help="Số từ top features hiển thị (mặc định: 20)"
    )
    parser.add_argument(
        "--samples", "-s",
        type=int,
        default=3,
        help="Số văn bản mẫu hiển thị vector (mặc định: 3)"
    )

    args = parser.parse_args()

    # ---- Banner ----
    print()
    print("=" * 65)
    print("  TF-IDF VECTORIZER")
    print("  Vector hoa van ban tieng Viet cho Naive Bayes")
    print("=" * 65)

    # ---- Xác định file đầu vào ----
    if args.input:
        input_path = os.path.join(CURRENT_DIR, args.input) if not os.path.isabs(args.input) else args.input
    else:
        # Tự tìm: ưu tiên CSV trước, rồi TXT
        if os.path.exists(DEFAULT_CSV_INPUT):
            input_path = DEFAULT_CSV_INPUT
        elif os.path.exists(DEFAULT_TXT_INPUT):
            input_path = DEFAULT_TXT_INPUT
        else:
            print("\n  [ERROR] Khong tim thay file dau vao!")
            print(f"     Da tim: {DEFAULT_CSV_INPUT}")
            print(f"     Da tim: {DEFAULT_TXT_INPUT}")
            print("     Hay chay text_cleaner.py hoac stopword.py truoc.")
            sys.exit(1)

    if not os.path.exists(input_path):
        print(f"\n  [ERROR] File khong ton tai: {input_path}")
        sys.exit(1)

    file_type = "CSV" if input_path.endswith(".csv") else "TXT"
    print(f"  [INPUT] File dau vao : {os.path.basename(input_path)} ({file_type})")

    # ---- Đọc corpus ----
    print(f"\n  [READ] Dang doc du lieu...")
    try:
        corpus = load_corpus(input_path)
    except (KeyError, ValueError) as e:
        print(f"\n  [ERROR] Loi doc du lieu: {e}")
        sys.exit(1)

    if not corpus:
        print("\n  [ERROR] Corpus rong! Khong co van ban nao de vector hoa.")
        sys.exit(1)

    print(f"  [OK] Da doc {len(corpus)} van ban")

    # ---- Xây dựng TF-IDF ----
    print(f"\n  [BUILD] Dang xay dung ma tran TF-IDF...")
    print(f"     max_features = {TFIDF_CONFIG['max_features']}")
    print(f"     ngram_range  = {TFIDF_CONFIG['ngram_range']}")
    print(f"     min_df       = {TFIDF_CONFIG['min_df']}")
    print(f"     max_df       = {TFIDF_CONFIG['max_df']}")
    print(f"     sublinear_tf = {TFIDF_CONFIG['sublinear_tf']}")

    vectorizer, matrix = build_tfidf(corpus)

    # ---- Hiển thị kết quả ----
    show_stats(corpus, vectorizer, matrix)
    show_top_features(vectorizer, matrix, n=args.top)
    show_sample_vectors(vectorizer, matrix, corpus, n=args.samples)

    # ---- Lưu kết quả ----
    print(f"\n  [SAVE] Dang luu ket qua...")
    save_results(vectorizer, matrix)

    # ---- Hoàn tất ----
    print()
    print("=" * 65)
    print("  HOAN TAT! Vector hoa TF-IDF thanh cong.")
    print(f"     Ma tran  : {matrix.shape[0]} van ban x {matrix.shape[1]} features")
    print(f"     Output   : tfidf_matrix.npz, tfidf_vocab.json, tfidf_vectorizer.pkl")
    print("=" * 65)
    print()


if __name__ == "__main__":
    main()
