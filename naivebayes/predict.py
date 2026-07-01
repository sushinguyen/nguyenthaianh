# -*- coding: utf-8 -*-
"""
predict.py — Du doan thuoc cho benh nhan moi
=============================================
Nhiem vu   : Load pipeline va predict tu du lieu tho (string / so)
Doc tu     : pipeline_model.pkl
Khong can  : scaler.pkl rieng, encoder.pkl rieng
              → Pipeline chua tat ca ben trong (Bai hoc #16)

Ly do thiet ke:
  pipeline_model.pkl = [StandardScaler + OneHotEncoder + GaussianNB]
  → predict.py truyen thang Sex='F', BP='HIGH' (string goc)
  → Pipeline tu encode + scale chinh xac theo thong so da hoc tu X_train
"""

import sys
import io
import pandas as pd
import joblib

from pathlib import Path
from utils import log_info, log_success, log_section

# Fix encoding cho Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ═══════════════════════════════════════════════════════
# CAU HINH — dung pathlib (Bai hoc fix: khong hard-code path)
# ═══════════════════════════════════════════════════════
BASE_DIR   = Path(__file__).parent
MODEL_FILE = BASE_DIR / "pipeline_model.pkl"

DRUG_INFO = {
    "DrugY": "Drug Y — Thuong dung cho benh nhan co Na_to_K cao (> ~14.8)",
    "drugA": "Drug A — Danh cho benh nhan lon tuoi, huyet ap cao",
    "drugB": "Drug B — Nhom lon tuoi, huyet ap cao",
    "drugC": "Drug C — Nhom tre, huyet ap thap",
    "drugX": "Drug X — Thuoc pho thong, nhieu truong hop",
}

# ═══════════════════════════════════════════════════════
# LOAD PIPELINE
# ═══════════════════════════════════════════════════════
log_info("LOAD", f"Doc model tu: {MODEL_FILE}")
pipeline = joblib.load(MODEL_FILE)
log_success("Pipeline da san sang (StandardScaler + OneHotEncoder + GaussianNB)")


# ═══════════════════════════════════════════════════════
# HAM DU DOAN
# ═══════════════════════════════════════════════════════
def predict_drug(
    age: int,
    sex: str,
    bp: str,
    cholesterol: str,
    na_to_k: float,
) -> dict:
    """
    Du doan loai thuoc phu hop cho benh nhan moi.

    Args:
        age         : Tuoi benh nhan (int), vi du: 23
        sex         : Gioi tinh ('F' hoac 'M')
        bp          : Huyet ap ('HIGH', 'NORMAL', 'LOW')
        cholesterol : Muc cholesterol ('HIGH', 'NORMAL')
        na_to_k     : Ti le Na/K trong mau (float), vi du: 25.355

    Returns:
        dict:
            'drug'          → Ten thuoc duoc du doan
            'info'          → Mo ta ngan ve thuoc
            'confidence'    → Xac suat cua nhan duoc chon (%)
            'probabilities' → Xac suat tat ca cac nhan (dict, sap xep giam dan)
    """
    # Tao DataFrame dung cau truc — Pipeline tu xu ly encode + scale
    patient = pd.DataFrame([{
        "Age":         int(age),
        "Sex":         sex.strip().upper(),
        "BP":          bp.strip().upper(),
        "Cholesterol": cholesterol.strip().upper(),
        "Na_to_K":     float(na_to_k),
    }])

    drug_pred    = pipeline.predict(patient)[0]
    proba_arr    = pipeline.predict_proba(patient)[0]
    drug_classes = pipeline.classes_

    prob_dict   = {cls: round(p * 100, 2) for cls, p in zip(drug_classes, proba_arr)}
    prob_sorted = dict(sorted(prob_dict.items(), key=lambda x: x[1], reverse=True))

    return {
        "drug":          drug_pred,
        "info":          DRUG_INFO.get(drug_pred, "Khong co thong tin"),
        "confidence":    prob_sorted[drug_pred],
        "probabilities": prob_sorted,
    }


def print_result(result: dict, patient_label: str = ""):
    """In ket qua du doan theo format dep."""
    print()
    if patient_label:
        print(f"  Benh nhan: {patient_label}")
    print(f"  {'-' * 50}")
    print(f"  Thuoc du doan : {result['drug']}  (tin cay {result['confidence']:.1f}%)")
    print(f"  {result['info']}")
    print(f"\n  Xac suat tung nhan:")
    for drug, pct in result["probabilities"].items():
        bar  = "|" * int(pct / 4)
        flag = " <- chon" if drug == result["drug"] else ""
        print(f"     {drug:<10}: {pct:>6.2f}%  {bar}{flag}")
    print(f"  {'-' * 50}")


# ═══════════════════════════════════════════════════════
# VI DU DU DOAN
# ═══════════════════════════════════════════════════════
if __name__ == "__main__":
    log_section("DU DOAN BENH NHAN MAU")

    test_cases = [
        {
            "label":       "Benh nhan 1 — ky vong: DrugY",
            "age": 23, "sex": "F", "bp": "HIGH",
            "cholesterol": "HIGH", "na_to_k": 25.355,
        },
        {
            "label":       "Benh nhan 2 — ky vong: drugC",
            "age": 47, "sex": "M", "bp": "LOW",
            "cholesterol": "HIGH", "na_to_k": 13.093,
        },
        {
            "label":       "Benh nhan 3 — ky vong: drugB",
            "age": 74, "sex": "M", "bp": "HIGH",
            "cholesterol": "HIGH", "na_to_k": 9.567,
        },
        {
            "label":       "Benh nhan 4 — ky vong: drugX",
            "age": 28, "sex": "F", "bp": "NORMAL",
            "cholesterol": "HIGH", "na_to_k": 7.798,
        },
        {
            "label":       "Benh nhan 5 — benh nhan moi (khong co trong dataset)",
            "age": 35, "sex": "M", "bp": "NORMAL",
            "cholesterol": "NORMAL", "na_to_k": 20.0,
        },
    ]

    for case in test_cases:
        label = case.pop("label")
        result = predict_drug(**case)
        print_result(result, patient_label=label)

    print()
    log_success("Hoan thanh du doan tat ca benh nhan mau.")
    print()
    print("-" * 62)
    print("  Cach dung trong code cua ban:")
    print("-" * 62)
    print("""
  from predict import predict_drug

  result = predict_drug(
      age=30, sex='M', bp='HIGH',
      cholesterol='NORMAL', na_to_k=15.5
  )
  print(result['drug'])          # vi du: 'DrugY'
  print(result['confidence'])    # vi du: 87.32
  print(result['probabilities']) # dict xac suat tat ca nhan
    """)
