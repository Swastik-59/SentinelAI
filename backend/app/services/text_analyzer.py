"""
SentinelAI — Text Analyzer Service

Detection pipeline:
1. Extract stylometric features (sentence length, variance, punctuation, stopwords)
2. Compute pseudo-perplexity via GPT-2 token-level log-likelihoods
3. Run trained scikit-learn classifier on feature vector
4. Return AI-generation probability
"""

import os
import re
import math
import string
import logging
import numpy as np
import joblib
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Path to the trained model
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "text_model.pkl")

# Lazy-loaded resources
_model = None
_tokenizer = None
_gpt2_model = None


# ── Stylometric Feature Extraction ────────────────────────────────────────

def _split_sentences(text: str) -> List[str]:
    """Split text into sentences using regex."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s for s in sentences if len(s) > 0]


def extract_stylometric_features(text: str) -> Dict[str, float]:
    """
    Extract stylometric signals that differ between human and AI-written text.
    
    Features:
    - avg_sentence_length: AI tends to produce more uniform sentence lengths
    - sentence_length_variance: lower variance → more likely AI
    - punctuation_frequency: ratio of punctuation characters to total
    - stopword_ratio: proportion of common English stopwords
    - avg_word_length: AI often uses slightly longer words on average
    - lexical_diversity: type-token ratio (unique words / total words)
    """
    sentences = _split_sentences(text)
    words = text.split()
    
    if not words:
        return {
            "avg_sentence_length": 0.0,
            "sentence_length_variance": 0.0,
            "punctuation_frequency": 0.0,
            "stopword_ratio": 0.0,
            "avg_word_length": 0.0,
            "lexical_diversity": 0.0,
        }

    # Sentence-level metrics
    sentence_lengths = [len(s.split()) for s in sentences] if sentences else [0]
    avg_sentence_length = float(np.mean(sentence_lengths))
    sentence_length_variance = float(np.var(sentence_lengths))

    # Punctuation frequency
    punct_count = sum(1 for ch in text if ch in string.punctuation)
    punctuation_frequency = punct_count / len(text) if text else 0.0

    # Stopword ratio (common English stopwords)
    STOPWORDS = {
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
    }
    lower_words = [w.lower().strip(string.punctuation) for w in words]
    stopword_count = sum(1 for w in lower_words if w in STOPWORDS)
    stopword_ratio = stopword_count / len(words)

    # Average word length
    word_lengths = [len(w) for w in lower_words if w]
    avg_word_length = float(np.mean(word_lengths)) if word_lengths else 0.0

    # Lexical diversity (type-token ratio)
    unique_words = set(lower_words)
    lexical_diversity = len(unique_words) / len(lower_words) if lower_words else 0.0

    return {
        "avg_sentence_length": round(avg_sentence_length, 4),
        "sentence_length_variance": round(sentence_length_variance, 4),
        "punctuation_frequency": round(punctuation_frequency, 4),
        "stopword_ratio": round(stopword_ratio, 4),
        "avg_word_length": round(avg_word_length, 4),
        "lexical_diversity": round(lexical_diversity, 4),
    }


# ── Pseudo-Perplexity (GPT-2 Based) ──────────────────────────────────────

def compute_perplexity(text: str) -> float:
    """
    Compute pseudo-perplexity using GPT-2.
    
    Lower perplexity → text is more predictable → more likely AI-generated.
    Falls back to a heuristic estimator if the model cannot be loaded.
    """
    try:
        global _tokenizer, _gpt2_model
        if _tokenizer is None:
            from transformers import GPT2Tokenizer, GPT2LMHeadModel
            import torch
            _tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
            _gpt2_model = GPT2LMHeadModel.from_pretrained("gpt2")
            _gpt2_model.eval()

        import torch

        # Tokenize (truncate to 512 tokens for speed)
        encodings = _tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        input_ids = encodings.input_ids

        with torch.no_grad():
            outputs = _gpt2_model(input_ids, labels=input_ids)
            loss = outputs.loss.item()

        perplexity = math.exp(loss)
        return round(perplexity, 2)

    except Exception as e:
        logger.warning(f"GPT-2 perplexity computation failed, using heuristic: {e}")
        return _heuristic_perplexity(text)


def _heuristic_perplexity(text: str) -> float:
    """
    Fallback heuristic perplexity estimator.
    Uses character-level entropy as a rough proxy.
    """
    if not text:
        return 100.0
    
    text_lower = text.lower()
    freq = {}
    for ch in text_lower:
        freq[ch] = freq.get(ch, 0) + 1
    
    length = len(text_lower)
    entropy = -sum((count / length) * math.log2(count / length) for count in freq.values())
    
    # Map entropy to a perplexity-like range (30–300)
    perplexity = 2 ** entropy * 8
    return round(min(max(perplexity, 30.0), 300.0), 2)


# ── ML Classifier ─────────────────────────────────────────────────────────

def _load_model():
    """Load the trained scikit-learn classifier from disk."""
    global _model
    if _model is None:
        if os.path.exists(MODEL_PATH):
            _model = joblib.load(MODEL_PATH)
            logger.info("Loaded text classification model from %s", MODEL_PATH)
        else:
            logger.warning("No trained model found at %s — using rule-based fallback", MODEL_PATH)
    return _model


def _rule_based_probability(features: Dict[str, float], perplexity: float) -> float:
    """
    Rule-based fallback when no trained model is available.
    Combines feature heuristics into an AI-generation probability.
    """
    score = 0.0

    # Low sentence length variance → AI
    if features["sentence_length_variance"] < 20:
        score += 0.25
    elif features["sentence_length_variance"] < 50:
        score += 0.10

    # Low perplexity → AI
    if perplexity < 50:
        score += 0.30
    elif perplexity < 100:
        score += 0.15

    # High stopword ratio → slightly more AI-like
    if features["stopword_ratio"] > 0.45:
        score += 0.10

    # Low lexical diversity → AI
    if features["lexical_diversity"] < 0.5:
        score += 0.15

    # Moderate punctuation → AI tends to be well-punctuated
    if 0.03 < features["punctuation_frequency"] < 0.08:
        score += 0.10

    return min(score, 0.99)


def analyze_text(text: str) -> Dict[str, Any]:
    """
    Full text analysis pipeline.
    
    Returns:
    - ai_probability: float [0,1]
    - stylometric_features: dict of extracted features
    - perplexity: float
    """
    # Step 1: Stylometric features
    features = extract_stylometric_features(text)

    # Step 2: Perplexity
    perplexity = compute_perplexity(text)

    # Step 3: ML classification or fallback
    model = _load_model()
    if model is not None:
        feature_vector = np.array([[
            features["avg_sentence_length"],
            features["sentence_length_variance"],
            features["punctuation_frequency"],
            features["stopword_ratio"],
            features["avg_word_length"],
            features["lexical_diversity"],
            perplexity,
        ]])
        try:
            proba = model.predict_proba(feature_vector)[0]
            # Class 1 = AI-generated
            ai_probability = float(proba[1]) if len(proba) > 1 else float(proba[0])
        except Exception as e:
            logger.error(f"Model prediction failed: {e}")
            ai_probability = _rule_based_probability(features, perplexity)
    else:
        ai_probability = _rule_based_probability(features, perplexity)

    return {
        "ai_probability": round(ai_probability, 4),
        "stylometric_features": features,
        "perplexity": perplexity,
    }
