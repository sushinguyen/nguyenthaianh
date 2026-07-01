# -*- coding: utf-8 -*-
"""
train_model.py
Train GaussianNB phan loai thuoc tu drug200.csv.

Doc tu  : drug200.csv  (khong ghi de)
Luu ra  : pipeline_model.pkl, confusion_matrix.png

Pipeline:
  train_test_split (Stratified, 80/20)
  -> ColumnTransformer:
       StandardScaler  : Age, Na_to_K
       OneHotEncoder   : Sex, BP, Cholesterol
  -> GaussianNB
  -> Danh gia: accuracy + f1_macro + baseline
  -> Luu pipeline_model.pkl
"""

import sys
import io
import joblib
import pandas as pd
import numpy as np

from pathlib import Path
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix

from utils import (
    log_info, log_warning, log_success, log_section,
    load_data, check_class_distribution,
    compare_with_baseline, plot_confusion_matrix,
)

# --- CAU HINH ---
BASE_DIR         = Path(__file__).parent
DATA_FILE        = BASE_DIR / "drug200.csv"
MODEL_FILE       = BASE_DIR / "pipeline_model.pkl"
CHART_FILE       = BASE_DIR / "confusion_matrix.png"
RANDOM_STATE     = 42
TEST_SIZE        = 0.20
NUMERIC_COLS     = ["Age", "Na_to_K"]
CATEGORICAL_COLS = ["Sex", "BP", "Cholesterol"]
TARGET_COL       = "Drug"


def train():
    """Toan bo quy trinh: doc data -> pipeline -> danh gia -> luu model."""

    # Buoc 0: Doc du lieu
    log_section("Buoc 0: Doc du lieu")
    df = load_data(str(DATA_FILE))
    X  = df[NUMERIC_COLS + CATEGORICAL_COLS]
    y  = df[TARGET_COL]
    check_class_distribution(y, TARGET_COL)

    # Buoc 1: Chia Train/Test truoc khi xu ly (chong Data Leakage)
    log_section("Buoc 1: Chia Train / Test (Stratified 80/20)")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size    = TEST_SIZE,
        random_state = RANDOM_STATE,
        stratify     = y,
    )
    log_info("SPLIT", f"Train: {X_train.shape[0]} mau  |  Test: {X_test.shape[0]} mau")
    log_info("SPLIT", "StandardScaler chi fit() tren X_train, khong thay X_test")

    # Buoc 2: ColumnTransformer
    log_section("Buoc 2: ColumnTransformer")
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(),                                   NUMERIC_COLS),
            ("cat", OneHotEncoder(drop="first", sparse_output=False),   CATEGORICAL_COLS),
        ],
        remainder="drop",
    )
    log_info("PREP", f"StandardScaler -> {NUMERIC_COLS}")
    log_info("PREP", f"OneHotEncoder  -> {CATEGORICAL_COLS}  (drop='first')")

    # Buoc 3: Xay dung Pipeline
    log_section("Buoc 3: Xay dung Pipeline (ColumnTransformer -> GaussianNB)")
    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier",   GaussianNB()),
    ])
    log_success("Pipeline san sang.")

    # Buoc 4A: Cross-Validation tren X_train
    log_section("Buoc 4A: Cross-Validation 5-fold (StratifiedKFold, tren X_train)")
    cv     = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    cv_acc = cross_val_score(pipeline, X_train, y_train, cv=cv, scoring="accuracy")
    cv_f1  = cross_val_score(pipeline, X_train, y_train, cv=cv, scoring="f1_macro")
    print(f"  CV Accuracy : {cv_acc.mean():.4f} +/- {cv_acc.std():.4f}")
    print(f"  CV f1_macro : {cv_f1.mean():.4f} +/- {cv_f1.std():.4f}")
    print(f"  Fold detail : {[round(s, 4) for s in cv_f1]}")

    # Buoc 4B: So sanh voi Baseline
    compare_with_baseline(pipeline, X_train, y_train, cv)

    # Buoc 4C: Train va danh gia tren tap Test
    log_section("Buoc 4C: Train va danh gia tren tap Test")
    pipeline.fit(X_train, y_train)
    y_pred   = pipeline.predict(X_test)
    test_acc = accuracy_score(y_test, y_pred)
    test_f1  = f1_score(y_test, y_pred, average="macro")
    print(f"  Test Accuracy : {test_acc:.4f}  ({test_acc * 100:.1f}%)")
    print(f"  Test f1_macro : {test_f1:.4f}")

    gap = abs(cv_f1.mean() - test_f1)
    if gap > 0.10:
        log_warning(f"CV vs Test f1_macro chenh {gap:.3f} > 0.10 — kiem tra lai du lieu!")
    else:
        log_success(f"CV va Test f1_macro sat nhau (gap={gap:.3f}) — mo hinh on dinh.")

    print()
    print(classification_report(y_test, y_pred))
    _analyze_mistakes(y_test, y_pred)

    # Buoc 4D: Confusion Matrix
    log_section("Buoc 4D: Confusion Matrix")
    plot_confusion_matrix(
        y_test, y_pred,
        labels      = sorted(y.unique()),
        title       = "Confusion Matrix - GaussianNB Drug Classification",
        output_file = str(CHART_FILE),
    )

    # Buoc 5: Luu Pipeline
    log_section("Buoc 5: Luu Pipeline model")
    joblib.dump(pipeline, MODEL_FILE)
    log_success(f"Da luu pipeline -> {MODEL_FILE}")
    log_info("SAVE", "Noi dung: StandardScaler + OneHotEncoder + GaussianNB")

    return pipeline


def _analyze_mistakes(y_true, y_pred):
    """Phan tich nhan nao hay bi nham — luu y trong bai toan y te."""
    labels = sorted(set(y_true))
    cm     = confusion_matrix(y_true, y_pred, labels=labels)
    print("Phan tich sai so:")
    for i, label in enumerate(labels):
        total   = cm[i, :].sum()
        correct = cm[i, i]
        wrong   = total - correct
        if wrong > 0:
            confused_to = max(
                {labels[j]: cm[i, j] for j in range(len(labels)) if j != i and cm[i, j] > 0},
                key=lambda k: cm[i, labels.index(k)]
            )
            print(f"  [{label}]: {wrong}/{total} sai -> hay bi nham sang [{confused_to}]")
        else:
            print(f"  [{label}]: Du doan dung 100%")
    print("  Luu y: Recall thap = benh nhan can thuoc nhung khong duoc chi dinh (nguy hiem hon chi dinh sai).")
    print()


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    train()
