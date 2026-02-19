"""
SentinelAI — Fraud Detector Training Script

Trains a classifier to detect phishing/fraudulent emails vs legitimate ones.

Pipeline:
1. Load fraud_detection_dataset.csv (or generate synthetic data as fallback)
2. Extract stylometric features
3. Train LogisticRegression and RandomForestClassifier
4. Evaluate accuracy + F1
5. Save best model to ai/models/fraud_detector.pkl

Usage:
    cd <project_root>
    python -m ai.training.train_fraud_detector
"""

import os
import sys
import logging
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, f1_score, accuracy_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ai.utils.feature_engineering import extract_features, features_to_vector, FEATURE_NAMES

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────
DATASET_PATH = PROJECT_ROOT / "ai" / "data" / "processed" / "fraud_detection_dataset.csv"
MODEL_DIR = PROJECT_ROOT / "ai" / "models"
MODEL_OUTPUT = MODEL_DIR / "fraud_detector.pkl"


# ── Synthetic Data Fallback ───────────────────────────────────────────────

def generate_synthetic_data(n_samples: int = 2000) -> tuple:
    """
    Generate synthetic training data when real dataset is unavailable.
    Mimics feature distributions of normal vs phishing emails.
    """
    np.random.seed(42)
    n_normal = n_samples // 2
    n_phishing = n_samples - n_normal

    # Features: avg_sent_len, sent_var, punct_freq, stopword_ratio,
    #           uppercase_ratio, word_count, lexical_diversity
    normal_features = np.column_stack([
        np.random.normal(20, 7, n_normal),            # avg_sentence_length
        np.random.gamma(4, 25, n_normal),              # sentence_length_variance
        np.random.normal(0.06, 0.02, n_normal),        # punctuation_frequency
        np.random.normal(0.40, 0.06, n_normal),        # stopword_ratio
        np.random.normal(0.03, 0.015, n_normal),       # uppercase_ratio
        np.random.normal(200, 100, n_normal),           # word_count
        np.random.normal(0.60, 0.10, n_normal),        # lexical_diversity
    ])

    phishing_features = np.column_stack([
        np.random.normal(14, 4, n_phishing),            # avg_sentence_length (shorter)
        np.random.gamma(2, 8, n_phishing),              # sentence_length_variance (lower)
        np.random.normal(0.07, 0.025, n_phishing),      # punctuation_frequency (higher)
        np.random.normal(0.45, 0.05, n_phishing),       # stopword_ratio (higher)
        np.random.normal(0.06, 0.03, n_phishing),       # uppercase_ratio (higher)
        np.random.normal(150, 60, n_phishing),           # word_count (shorter)
        np.random.normal(0.50, 0.09, n_phishing),       # lexical_diversity (lower)
    ])

    X = np.vstack([normal_features, phishing_features])
    y = np.concatenate([np.zeros(n_normal), np.ones(n_phishing)])

    # Clip to valid ranges
    X = np.clip(X, 0, None)
    X[:, 2] = np.clip(X[:, 2], 0, 1)
    X[:, 3] = np.clip(X[:, 3], 0, 1)
    X[:, 4] = np.clip(X[:, 4], 0, 1)
    X[:, 6] = np.clip(X[:, 6], 0, 1)

    return X, y


def extract_features_from_dataset(df: pd.DataFrame) -> tuple:
    """Extract feature vectors from a DataFrame with 'text' and 'label_fraud' columns."""
    logger.info("Extracting features from %d texts...", len(df))

    vectors = []
    valid_indices = []
    for idx, row in df.iterrows():
        try:
            features = extract_features(str(row["text"]))
            vec = features_to_vector(features)
            vectors.append(vec)
            valid_indices.append(idx)
        except Exception as e:
            logger.debug("Skipping row %d: %s", idx, e)

    X = np.vstack(vectors) if vectors else np.empty((0, len(FEATURE_NAMES)))
    y = df.loc[valid_indices, "label_fraud"].values.astype(float)
    return X, y


# ── Training ──────────────────────────────────────────────────────────────

def train() -> None:
    """Main training pipeline for fraud detection."""
    print("=" * 60)
    print("SentinelAI — Fraud Detector Training")
    print("=" * 60)

    # ── Load data ─────────────────────────────────────────────────
    if DATASET_PATH.exists():
        print(f"\n[1/5] Loading dataset from {DATASET_PATH} ...")
        df = pd.read_csv(DATASET_PATH)
        df = df.dropna(subset=["text", "label_fraud"])
        print(f"  Total rows: {len(df)}")
        print(f"  Normal (0):   {(df['label_fraud'] == 0).sum()}")
        print(f"  Phishing (1): {(df['label_fraud'] == 1).sum()}")

        print("\n[2/5] Extracting features...")
        X, y = extract_features_from_dataset(df)
    else:
        print(f"\n[1/5] Dataset not found at {DATASET_PATH}")
        print("  Using synthetic training data as fallback...")
        print("\n[2/5] Generating synthetic features...")
        X, y = generate_synthetic_data(n_samples=2000)

    print(f"  Feature matrix shape: {X.shape}")
    print(f"  Labels: {int(np.sum(y == 0))} normal, {int(np.sum(y == 1))} phishing")

    # ── Split data ────────────────────────────────────────────────
    print("\n[3/5] Splitting data (80/20)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"  Train: {len(y_train)} | Test: {len(y_test)}")

    # ── Train models ──────────────────────────────────────────────
    print("\n[4/5] Training models...")

    models = {
        "LogisticRegression": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(
                max_iter=1000,
                C=1.0,
                random_state=42,
                class_weight="balanced",
            )),
        ]),
        "RandomForest": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", RandomForestClassifier(
                n_estimators=100,
                max_depth=12,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1,
                class_weight="balanced",
            )),
        ]),
    }

    best_model = None
    best_name = ""
    best_f1 = -1.0

    for name, model in models.items():
        print(f"\n  Training {name}...")
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average="weighted")

        print(f"    Accuracy: {acc:.4f}")
        print(f"    F1 Score: {f1:.4f}")
        print(classification_report(y_test, y_pred,
                                     target_names=["Normal", "Phishing"]))

        if f1 > best_f1:
            best_f1 = f1
            best_model = model
            best_name = name

    # ── Cross-validation ──────────────────────────────────────────
    print(f"\n  Best model: {best_name} (F1={best_f1:.4f})")
    cv_scores = cross_val_score(best_model, X, y, cv=5, scoring="f1_weighted")
    print(f"  5-Fold CV F1: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

    # ── Save model ────────────────────────────────────────────────
    print(f"\n[5/5] Saving model...")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_model, MODEL_OUTPUT)
    size_kb = os.path.getsize(MODEL_OUTPUT) / 1024
    print(f"  Model saved: {MODEL_OUTPUT}")
    print(f"  File size: {size_kb:.1f} KB")

    # ── Feature importances ───────────────────────────────────────
    if hasattr(best_model.named_steps.get("clf", None), "feature_importances_"):
        importances = best_model.named_steps["clf"].feature_importances_
        print("\n  Feature Importances:")
        for name, imp in sorted(zip(FEATURE_NAMES, importances), key=lambda x: -x[1]):
            bar = "█" * int(imp * 50)
            print(f"    {name:30s} {imp:.4f} {bar}")

    print("\n" + "=" * 60)
    print("Training complete!")
    print("=" * 60)


if __name__ == "__main__":
    train()
