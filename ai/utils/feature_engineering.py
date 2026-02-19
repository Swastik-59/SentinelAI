"""
SentinelAI — Feature Engineering Module

Extracts stylometric and statistical features from text for ML classification:
- Average sentence length
- Sentence length variance
- Punctuation frequency
- Stopword ratio
- Uppercase ratio
- Word count
- Lexical diversity
- TF-IDF vectorization
- Optional GPT-2 perplexity scoring

Usage:
    from ai.utils.feature_engineering import extract_features, compute_perplexity
"""

import re
import math
import string
import logging
import numpy as np
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# ── Common English Stopwords ──────────────────────────────────────────────
STOPWORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "above",
    "below", "between", "out", "off", "over", "under", "again",
    "further", "then", "once", "here", "there", "when", "where", "why",
    "how", "all", "both", "each", "few", "more", "most", "other",
    "some", "such", "no", "nor", "not", "only", "own", "same", "so",
    "than", "too", "very", "just", "because", "but", "and", "or",
    "if", "while", "this", "that", "these", "those", "i", "me", "my",
    "we", "our", "you", "your", "he", "him", "his", "she", "her",
    "it", "its", "they", "them", "their", "what", "which", "who",
    "about", "up", "down", "any", "every",
})


# ── Sentence Splitting ────────────────────────────────────────────────────

def split_sentences(text: str) -> List[str]:
    """Split text into sentences using punctuation boundaries."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s for s in sentences if len(s.strip()) > 0]


# ── Stylometric Feature Extraction ────────────────────────────────────────

def extract_features(text: str) -> Dict[str, float]:
    """
    Extract stylometric and statistical features from text.

    Returns dict with keys:
        avg_sentence_length, sentence_length_variance, punctuation_frequency,
        stopword_ratio, uppercase_ratio, word_count, lexical_diversity
    """
    if not text or not text.strip():
        return {
            "avg_sentence_length": 0.0,
            "sentence_length_variance": 0.0,
            "punctuation_frequency": 0.0,
            "stopword_ratio": 0.0,
            "uppercase_ratio": 0.0,
            "word_count": 0.0,
            "lexical_diversity": 0.0,
        }

    sentences = split_sentences(text)
    words = text.split()

    if not words:
        return {
            "avg_sentence_length": 0.0,
            "sentence_length_variance": 0.0,
            "punctuation_frequency": 0.0,
            "stopword_ratio": 0.0,
            "uppercase_ratio": 0.0,
            "word_count": 0.0,
            "lexical_diversity": 0.0,
        }

    # Sentence-level features
    sentence_lengths = [len(s.split()) for s in sentences] if sentences else [0]
    avg_sentence_length = float(np.mean(sentence_lengths))
    sentence_length_variance = float(np.var(sentence_lengths))

    # Punctuation frequency
    punct_count = sum(1 for ch in text if ch in string.punctuation)
    punctuation_frequency = punct_count / len(text) if text else 0.0

    # Stopword ratio
    lower_words = [w.lower().strip(string.punctuation) for w in words]
    lower_words = [w for w in lower_words if w]  # remove empty strings
    stopword_count = sum(1 for w in lower_words if w in STOPWORDS)
    stopword_ratio = stopword_count / len(lower_words) if lower_words else 0.0

    # Uppercase ratio (proportion of uppercase characters in alphabetic chars)
    alpha_chars = [ch for ch in text if ch.isalpha()]
    uppercase_count = sum(1 for ch in alpha_chars if ch.isupper())
    uppercase_ratio = uppercase_count / len(alpha_chars) if alpha_chars else 0.0

    # Word count
    word_count = float(len(words))

    # Lexical diversity (type-token ratio)
    unique_words = set(lower_words)
    lexical_diversity = len(unique_words) / len(lower_words) if lower_words else 0.0

    return {
        "avg_sentence_length": round(avg_sentence_length, 4),
        "sentence_length_variance": round(sentence_length_variance, 4),
        "punctuation_frequency": round(punctuation_frequency, 4),
        "stopword_ratio": round(stopword_ratio, 4),
        "uppercase_ratio": round(uppercase_ratio, 4),
        "word_count": round(word_count, 4),
        "lexical_diversity": round(lexical_diversity, 4),
    }


# ── Feature Vector for ML ─────────────────────────────────────────────────

FEATURE_NAMES = [
    "avg_sentence_length",
    "sentence_length_variance",
    "punctuation_frequency",
    "stopword_ratio",
    "uppercase_ratio",
    "word_count",
    "lexical_diversity",
]


def features_to_vector(features: Dict[str, float]) -> np.ndarray:
    """Convert feature dict to numpy vector in canonical order."""
    return np.array([features.get(name, 0.0) for name in FEATURE_NAMES])


def extract_feature_vector(text: str) -> np.ndarray:
    """Extract features and return as numpy vector."""
    features = extract_features(text)
    return features_to_vector(features)


# ── Batch Feature Extraction ──────────────────────────────────────────────

def extract_features_batch(texts: List[str]) -> np.ndarray:
    """
    Extract feature vectors for a batch of texts.
    Returns 2D numpy array of shape (n_texts, n_features).
    """
    vectors = []
    for text in texts:
        vectors.append(extract_feature_vector(text))
    return np.vstack(vectors) if vectors else np.empty((0, len(FEATURE_NAMES)))


# ── TF-IDF Vectorization ─────────────────────────────────────────────────

def build_tfidf_vectorizer(
    texts: List[str],
    max_features: int = 5000,
    ngram_range: tuple = (1, 2),
) -> Any:
    """
    Build and fit a TF-IDF vectorizer on the given texts.
    Returns the fitted vectorizer.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer

    vectorizer = TfidfVectorizer(
        max_features=max_features,
        ngram_range=ngram_range,
        stop_words="english",
        sublinear_tf=True,
        dtype=np.float32,
    )
    vectorizer.fit(texts)
    logger.info("TF-IDF vectorizer fitted with %d features", len(vectorizer.vocabulary_))
    return vectorizer


def tfidf_transform(vectorizer: Any, texts: List[str]) -> np.ndarray:
    """Transform texts using a fitted TF-IDF vectorizer."""
    return vectorizer.transform(texts)


# ── GPT-2 Perplexity Scoring ─────────────────────────────────────────────

# Cache for GPT-2 model and tokenizer
_gpt2_tokenizer = None
_gpt2_model = None


def compute_perplexity(text: str, max_length: int = 512) -> float:
    """
    Compute GPT-2 perplexity for the given text.

    Low perplexity → highly predictable → likely AI-generated.
    High perplexity → less predictable → likely human-written.

    Falls back to heuristic if GPT-2 is not available.
    """
    try:
        global _gpt2_tokenizer, _gpt2_model
        if _gpt2_tokenizer is None:
            from transformers import GPT2Tokenizer, GPT2LMHeadModel
            import torch  # noqa: F811
            _gpt2_tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
            _gpt2_model = GPT2LMHeadModel.from_pretrained("gpt2")
            _gpt2_model.eval()
            logger.info("GPT-2 model loaded for perplexity scoring")

        import torch
        encodings = _gpt2_tokenizer(
            text, return_tensors="pt", truncation=True, max_length=max_length
        )
        input_ids = encodings.input_ids

        with torch.no_grad():
            outputs = _gpt2_model(input_ids, labels=input_ids)
            loss = outputs.loss.item()

        perplexity = math.exp(loss)
        return round(min(perplexity, 1000.0), 2)

    except Exception as e:
        logger.debug("GPT-2 perplexity failed, using heuristic: %s", e)
        return _heuristic_perplexity(text)


def _heuristic_perplexity(text: str) -> float:
    """
    Heuristic perplexity estimate based on character entropy.
    Used as fallback when GPT-2 is not available.
    """
    if not text:
        return 100.0

    text_lower = text.lower()
    freq: Dict[str, int] = {}
    for ch in text_lower:
        freq[ch] = freq.get(ch, 0) + 1

    length = len(text_lower)
    entropy = -sum(
        (count / length) * math.log2(count / length)
        for count in freq.values()
    )

    # Scale entropy to approximate perplexity range
    perplexity = 2 ** entropy * 8
    return round(min(max(perplexity, 30.0), 300.0), 2)
