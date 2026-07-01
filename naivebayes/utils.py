# -*- coding: utf-8 -*-
"""
utils.py
Cac ham tien ich dung chung: log, doc data, kiem tra nhan, baseline, confusion matrix.
Import boi: train_model.py, predict.py
"""

import sys
import io
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix
from sklearn.dummy import DummyClassifier
from sklearn.model_selection import cross_val_score


# --- LOGGING ---

def log_info(step: str, message: str):
    print(f"[INFO] [{step}] {message}")

def log_warning(message: str):
    print(f"[WARN] {message}")

def log_success(message: str):
    print(f"[ OK ] {message}")

def log_section(title: str):
    print(f"\n>>> {title}")


# --- DOC DU LIEU ---

def load_data(filepath: str) -> pd.DataFrame:
    """Doc CSV va kiem tra co ban. Ham nay chi DOC, khong ghi de file goc."""
    log_info("LOAD", f"Doc tu: {filepath}")
    df = pd.read_csv(filepath)
    log_info("LOAD", f"Shape: {df.shape[0]} dong x {df.shape[1]} cot")
    log_info("LOAD", f"Cot: {list(df.columns)}")
    missing = df.isnull().sum().sum()
    if missing > 0:
        log_warning(f"Co {missing} gia tri bi thieu (NaN)!")
    else:
        log_success("Khong co gia tri bi thieu.")
    return df


# --- KIEM TRA CLASS DISTRIBUTION (Bai hoc #3) ---

def check_class_distribution(y: pd.Series, label_name: str = "Drug"):
    """Kiem tra phan phoi nhan, canh bao neu mat can bang > 3:1."""
    print(f"\nPhan phoi nhan '{label_name}':")
    counts = y.value_counts()
    pcts   = y.value_counts(normalize=True) * 100
    for label in counts.index:
        print(f"  {label:<12}: {counts[label]:>4} mau  ({pcts[label]:>5.1f}%)")
    ratio = counts.max() / counts.min()
    print(f"  Ti le max/min = {ratio:.2f}x")
    if ratio > 3:
        log_warning(f"Dataset mat can bang! ratio={ratio:.1f}x -> Dung f1_macro thay accuracy")
    else:
        log_success("Phan phoi on (ratio <= 3x)")
    print()


# --- SO SANH BASELINE (Bai hoc #13) ---

def compare_with_baseline(pipeline, X_train, y_train, cv) -> tuple[float, float]:
    """So sanh GaussianNB voi DummyClassifier (most_frequent)."""
    log_section("So sanh voi Baseline")
    dummy    = DummyClassifier(strategy="most_frequent", random_state=42)
    dummy_f1 = cross_val_score(dummy,    X_train, y_train, cv=cv, scoring="f1_macro").mean()
    nb_f1    = cross_val_score(pipeline, X_train, y_train, cv=cv, scoring="f1_macro").mean()
    improvement = nb_f1 - dummy_f1
    print(f"  Baseline  f1_macro : {dummy_f1:.4f}")
    print(f"  GaussianNB f1_macro: {nb_f1:.4f}")
    print(f"  Cai thien           : +{improvement:.4f} ({improvement * 100:.1f}%)")
    if improvement < 0.05:
        log_warning("Cai thien < 5% — model chua hoc duoc gi co y nghia!")
    else:
        log_success(f"Model vuot baseline {improvement * 100:.1f}%!")
    return nb_f1, dummy_f1


# --- CONFUSION MATRIX ---

def plot_confusion_matrix(
    y_true,
    y_pred,
    labels: list,
    title: str = "Confusion Matrix",
    output_file: str = "confusion_matrix.png"
):
    """Ve va luu confusion matrix dang heatmap."""
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=labels,
        yticklabels=labels,
        linewidths=0.5,
        linecolor="lightgray",
        square=True
    )
    plt.title(title, fontsize=14, fontweight="bold", pad=15)
    plt.ylabel("True Label",      fontsize=11)
    plt.xlabel("Predicted Label", fontsize=11)
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches="tight")
    plt.close()
    log_success(f"Da luu confusion matrix -> {output_file}")
