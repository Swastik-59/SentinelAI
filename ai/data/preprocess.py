"""
SentinelAI — Unified Dataset Preprocessing Pipeline

Loads raw datasets (Enron, Phishing_Email, ai_vs_human_text),
cleans text, and generates labeled CSVs for AI detection and fraud detection.

Usage:
    cd ai
    python -m data.preprocess

Outputs:
    data/processed/ai_detection_dataset.csv
    data/processed/fraud_detection_dataset.csv
"""

import os
import re
import html
import logging
import pandas as pd
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Paths (relative to project root) ──────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATASETS_DIR = PROJECT_ROOT / "ai" / "datasets"
PROCESSED_DIR = PROJECT_ROOT / "ai" / "data" / "processed"

# Dataset file locations
ENRON_PATH = DATASETS_DIR / "euron" / "Enron.csv"
PHISHING_PATH = DATASETS_DIR / "Phishing_Email.csv"
AI_VS_HUMAN_PATH = DATASETS_DIR / "ai_vs_human_text.csv"


# ── Text Cleaning ─────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """
    Clean raw text:
    - Decode HTML entities
    - Remove HTML tags
    - Lowercase
    - Normalize whitespace
    - Strip leading/trailing whitespace
    """
    if not isinstance(text, str):
        return ""
    # Decode HTML entities
    text = html.unescape(text)
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Lowercase
    text = text.lower()
    # Remove null bytes and control characters
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def is_valid_text(text: str, min_length: int = 20) -> bool:
    """Check if text is long enough after cleaning."""
    return isinstance(text, str) and len(text.strip()) >= min_length


# ── Dataset Loaders ───────────────────────────────────────────────────────

def load_enron(path: Optional[Path] = None, max_rows: Optional[int] = None) -> pd.DataFrame:
    """
    Load Enron email dataset — legitimate corporate emails.
    Expected columns: subject, body, label (or similar).
    Returns DataFrame with columns: [text, label_ai, label_fraud]
    """
    path = path or ENRON_PATH
    if not path.exists():
        logger.warning("Enron dataset not found at %s", path)
        return pd.DataFrame(columns=["text", "label_ai", "label_fraud"])

    logger.info("Loading Enron dataset from %s ...", path)
    df = pd.read_csv(path, nrows=max_rows, on_bad_lines="skip", encoding="utf-8")

    # Detect text column
    text_col = None
    for col in ["body", "text", "email_body", "content", "Email Text"]:
        if col in df.columns:
            text_col = col
            break
    if text_col is None:
        # Use second column as fallback
        text_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]

    df["text"] = df[text_col].apply(clean_text)
    df = df[df["text"].apply(is_valid_text)].copy()

    # Enron emails are human-written, non-fraudulent corporate emails
    df["label_ai"] = 0      # human
    df["label_fraud"] = 0    # not phishing
    df = df[["text", "label_ai", "label_fraud"]].reset_index(drop=True)

    logger.info("  Loaded %d Enron emails (human, non-fraud)", len(df))
    return df


def load_phishing(path: Optional[Path] = None, max_rows: Optional[int] = None) -> pd.DataFrame:
    """
    Load Phishing_Email.csv — contains safe and phishing emails.
    Expected columns: 'Email Text', 'Email Type' (Safe Email / Phishing Email)
    Returns DataFrame with columns: [text, label_ai, label_fraud]
    """
    path = path or PHISHING_PATH
    if not path.exists():
        logger.warning("Phishing dataset not found at %s", path)
        return pd.DataFrame(columns=["text", "label_ai", "label_fraud"])

    logger.info("Loading Phishing Email dataset from %s ...", path)
    df = pd.read_csv(path, nrows=max_rows, on_bad_lines="skip", encoding="utf-8")

    # Detect text column
    text_col = None
    for col in ["Email Text", "text", "body", "email_body", "content"]:
        if col in df.columns:
            text_col = col
            break
    if text_col is None:
        text_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]

    # Detect label column
    label_col = None
    for col in ["Email Type", "label", "Label", "type", "Type"]:
        if col in df.columns:
            label_col = col
            break

    df["text"] = df[text_col].apply(clean_text)
    df = df[df["text"].apply(is_valid_text)].copy()

    # Label fraud: phishing=1, safe=0
    if label_col:
        df["label_fraud"] = df[label_col].apply(
            lambda x: 1 if isinstance(x, str) and "phishing" in x.lower() else 0
        )
    else:
        # If no label column, assume all phishing
        df["label_fraud"] = 1

    # These are human-written emails (both safe and phishing)
    df["label_ai"] = 0
    df = df[["text", "label_ai", "label_fraud"]].reset_index(drop=True)

    phish_count = df["label_fraud"].sum()
    safe_count = len(df) - phish_count
    logger.info("  Loaded %d phishing emails (%d phishing, %d safe)", len(df), phish_count, safe_count)
    return df


def load_ai_vs_human(path: Optional[Path] = None, max_rows: Optional[int] = None) -> pd.DataFrame:
    """
    Load ai_vs_human_text.csv — AI-generated vs human-written text.
    Expected columns: 'text', 'label' (AI-generated / Human-written)
    Returns DataFrame with columns: [text, label_ai, label_fraud]
    """
    path = path or AI_VS_HUMAN_PATH
    if not path.exists():
        logger.warning("AI vs Human dataset not found at %s", path)
        return pd.DataFrame(columns=["text", "label_ai", "label_fraud"])

    logger.info("Loading AI vs Human dataset from %s ...", path)
    df = pd.read_csv(path, nrows=max_rows, on_bad_lines="skip", encoding="utf-8")

    # Detect text column
    text_col = None
    for col in ["text", "content", "body", "Text"]:
        if col in df.columns:
            text_col = col
            break
    if text_col is None:
        text_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]

    # Detect label column
    label_col = None
    for col in ["label", "Label", "class", "Class", "type"]:
        if col in df.columns:
            label_col = col
            break

    df["text"] = df[text_col].apply(clean_text)
    df = df[df["text"].apply(is_valid_text)].copy()

    # Label AI: AI-generated=1, Human-written=0
    if label_col:
        df["label_ai"] = df[label_col].apply(
            lambda x: 1 if isinstance(x, str) and "ai" in x.lower() else 0
        )
    else:
        df["label_ai"] = 0

    # Not fraud-specific dataset
    df["label_fraud"] = 0
    df = df[["text", "label_ai", "label_fraud"]].reset_index(drop=True)

    ai_count = df["label_ai"].sum()
    human_count = len(df) - ai_count
    logger.info("  Loaded %d texts (%d AI-generated, %d human)", len(df), ai_count, human_count)
    return df


# ── Pipeline ──────────────────────────────────────────────────────────────

def build_datasets(
    enron_max: Optional[int] = 10000,
    phishing_max: Optional[int] = 10000,
    ai_human_max: Optional[int] = None,
) -> None:
    """
    Build processed datasets for training:
    1. ai_detection_dataset.csv   — label_ai (0=human, 1=AI)
    2. fraud_detection_dataset.csv — label_fraud (0=normal, 1=phishing)
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("SentinelAI — Dataset Preprocessing Pipeline")
    logger.info("=" * 60)

    # Load all datasets
    enron_df = load_enron(max_rows=enron_max)
    phishing_df = load_phishing(max_rows=phishing_max)
    ai_human_df = load_ai_vs_human(max_rows=ai_human_max)

    # ── AI Detection Dataset ──────────────────────────────────────
    # Combine: human emails (Enron + Phishing safe) + AI text
    logger.info("\nBuilding AI detection dataset...")
    ai_parts = []

    # Human samples from Enron
    if len(enron_df) > 0:
        human_enron = enron_df[["text", "label_ai"]].copy()
        ai_parts.append(human_enron)

    # Human + AI samples from ai_vs_human
    if len(ai_human_df) > 0:
        ai_human_subset = ai_human_df[["text", "label_ai"]].copy()
        ai_parts.append(ai_human_subset)

    # Human samples from phishing (both safe and phishing are human-written)
    if len(phishing_df) > 0:
        human_phishing = phishing_df[["text", "label_ai"]].copy()
        # Subsample to avoid overwhelming with one source
        if len(human_phishing) > 5000:
            human_phishing = human_phishing.sample(n=5000, random_state=42)
        ai_parts.append(human_phishing)

    if ai_parts:
        ai_dataset = pd.concat(ai_parts, ignore_index=True)
        ai_dataset = ai_dataset.sample(frac=1, random_state=42).reset_index(drop=True)

        ai_path = PROCESSED_DIR / "ai_detection_dataset.csv"
        ai_dataset.to_csv(ai_path, index=False)
        logger.info("  Saved AI detection dataset: %s", ai_path)
        logger.info("  Total: %d rows | Human: %d | AI: %d",
                     len(ai_dataset),
                     (ai_dataset["label_ai"] == 0).sum(),
                     (ai_dataset["label_ai"] == 1).sum())
    else:
        logger.warning("  No data available for AI detection dataset!")

    # ── Fraud Detection Dataset ───────────────────────────────────
    logger.info("\nBuilding fraud detection dataset...")
    fraud_parts = []

    # Normal emails from Enron
    if len(enron_df) > 0:
        normal_enron = enron_df[["text", "label_fraud"]].copy()
        fraud_parts.append(normal_enron)

    # Phishing + safe emails
    if len(phishing_df) > 0:
        phishing_subset = phishing_df[["text", "label_fraud"]].copy()
        fraud_parts.append(phishing_subset)

    if fraud_parts:
        fraud_dataset = pd.concat(fraud_parts, ignore_index=True)
        fraud_dataset = fraud_dataset.sample(frac=1, random_state=42).reset_index(drop=True)

        fraud_path = PROCESSED_DIR / "fraud_detection_dataset.csv"
        fraud_dataset.to_csv(fraud_path, index=False)
        logger.info("  Saved fraud detection dataset: %s", fraud_path)
        logger.info("  Total: %d rows | Normal: %d | Phishing: %d",
                     len(fraud_dataset),
                     (fraud_dataset["label_fraud"] == 0).sum(),
                     (fraud_dataset["label_fraud"] == 1).sum())
    else:
        logger.warning("  No data available for fraud detection dataset!")

    logger.info("\n" + "=" * 60)
    logger.info("Preprocessing complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    build_datasets()
