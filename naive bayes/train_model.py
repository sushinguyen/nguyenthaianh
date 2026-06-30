"""
TRAIN MODEL — Huấn luyện và đánh giá mô hình Naive Bayes
Yêu cầu: data_clean1.csv phải có cột 'nhan' (tich_cuc | tieu_cuc | trung_tinh)

Sử dụng:
    python train_model.py

Output:
    nb_model.pkl         — Model đã train
    confusion_matrix.png — Confusion matrix
"""

import sys
import os
import warnings

import pandas as pd
import numpy as np

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

warnings.filterwarnings('ignore')

SCRIPT_DIR      = os.path.dirname(os.path.abspath(__file__))
FILE_DATA       = os.path.join(SCRIPT_DIR, 'data_clean1.csv')
COL_TEXT        = 'noi_dung_da_loc'
COL_LABEL       = 'nhan'
OUTPUT_MODEL    = os.path.join(SCRIPT_DIR, 'nb_model.pkl')
OUTPUT_MATRIX   = os.path.join(SCRIPT_DIR, 'confusion_matrix.png')
TEST_SIZE       = 0.2
RANDOM_STATE    = 42
N_SPLITS        = 5


def check_data(df: pd.DataFrame) -> bool:
    if COL_LABEL not in df.columns:
        print(f"Loi: Thieu cot '{COL_LABEL}'. Hay chay add.py truoc.")
        print(f"  Gia tri hop le: tich_cuc | tieu_cuc | trung_tinh")
        return False
    if COL_TEXT not in df.columns:
        print(f"Loi: Thieu cot '{COL_TEXT}'. Hay chay stopword.py truoc.")
        return False

    counts = df[COL_LABEL].value_counts()
    print("Phan bo nhan:")
    for lbl, cnt in counts.items():
        print(f"  {lbl}: {cnt}")

    if counts.min() < 10:
        print(f"[!] Canh bao: class '{counts.idxmin()}' chi co {counts.min()} mau — ket qua se kem chinh xac.")

    return True


def train_and_evaluate(df: pd.DataFrame):
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
    from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
    from sklearn.pipeline import Pipeline
    import joblib

    X = df[COL_TEXT].fillna('').astype(str)
    y = df[COL_LABEL].astype(str)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    print(f"Train/Test: {len(X_train)}/{len(X_test)} mau")

    min_df = 1 if len(X_train) < 500 else 2
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            min_df=min_df,
            max_df=0.90,
            sublinear_tf=True,
            token_pattern=r'(?u)\b\w[\w_]+\b',
            norm='l2',
            use_idf=True,
            smooth_idf=True,
        )),
        ('nb', MultinomialNB(alpha=1.0))
    ])

    # Cross-validation
    if len(df) >= N_SPLITS * 2:
        cv = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE)
        cv_scores = cross_val_score(pipeline, X, y, cv=cv, scoring='accuracy')
        print(f"Cross-val ({N_SPLITS}-fold): {[f'{s:.3f}' for s in cv_scores]}")
        print(f"  Trung binh: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    print(f"\nAccuracy: {acc:.4f} ({acc*100:.1f}%)")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, zero_division=0))

    # Confusion matrix
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        labels = sorted(y.unique())
        cm = confusion_matrix(y_test, y_pred, labels=labels)

        fig, ax = plt.subplots(figsize=(7, 5))
        im = ax.imshow(cm, interpolation='nearest', cmap='Blues')
        plt.colorbar(im, ax=ax)
        ax.set(
            xticks=range(len(labels)), yticks=range(len(labels)),
            xticklabels=labels, yticklabels=labels,
            xlabel='Predicted', ylabel='Actual',
            title=f'Confusion Matrix — Accuracy: {acc:.2%}'
        )
        thresh = cm.max() / 2.0
        for i in range(len(labels)):
            for j in range(len(labels)):
                ax.text(j, i, str(cm[i, j]), ha='center', va='center',
                        color='white' if cm[i, j] > thresh else 'black',
                        fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(OUTPUT_MATRIX, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"[OK] Confusion matrix -> {OUTPUT_MATRIX}")
    except ImportError:
        print("[!] matplotlib chua cai, bo qua confusion matrix.")

    joblib.dump(pipeline, OUTPUT_MODEL)
    print(f"[OK] Model -> {OUTPUT_MODEL}")

    return pipeline


def predict(texts: list, model_path: str = OUTPUT_MODEL) -> list:
    """Dự đoán nhãn cho văn bản mới."""
    import joblib
    from utils import preprocess_full
    pipeline = joblib.load(model_path)
    return pipeline.predict([preprocess_full(t) for t in texts])


if __name__ == "__main__":
    if not os.path.exists(FILE_DATA):
        print(f"Loi: Khong tim thay {FILE_DATA}")
        print("Hay chay: python stopword.py truoc.")
        sys.exit(1)

    df = pd.read_csv(FILE_DATA)
    print(f"Du lieu: {FILE_DATA} ({len(df)} dong)")

    if not check_data(df):
        sys.exit(1)

    df = df.dropna(subset=[COL_TEXT, COL_LABEL])
    df = df[df[COL_TEXT].str.strip() != '']
    df = df[df[COL_LABEL].str.strip() != '']

    model = train_and_evaluate(df)

    # Demo predict
    demo_texts = [
        "sản phẩm rất tốt, giao hàng nhanh, đóng gói cẩn thận",
        "hàng kém chất lượng, không như mô tả, thất vọng",
        "bình thường, không có gì đặc biệt",
    ]
    print("\nDemo predict:")
    try:
        for text, pred in zip(demo_texts, predict(demo_texts)):
            print(f"  '{text[:55]}' => {pred}")
    except Exception as e:
        print(f"  (Loi: {e})")
