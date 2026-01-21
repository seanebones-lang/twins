"""Tests for evaluation metrics."""
import pytest
from src.eval import (
    compute_perplexity,
    burrows_delta,
    cosine_similarity_style,
    extract_style_features
)


def test_compute_perplexity():
    """Test perplexity computation."""
    text = "This is a test sentence."
    perplexity = compute_perplexity(text)
    assert perplexity > 0
    assert perplexity != float('inf')


def test_burrows_delta():
    """Test Burrows' Delta computation."""
    test_text = "Hello, how are you?"
    ref_texts = ["Hi there!", "Hey, what's up?", "Hello friend"]
    
    delta = burrows_delta(test_text, ref_texts)
    assert delta >= 0
    assert delta != float('inf')


def test_cosine_similarity_style():
    """Test cosine similarity for style."""
    test_text = "Hey, what's up?"
    ref_texts = ["Hi there!", "Hello friend", "Hey buddy"]
    
    similarity = cosine_similarity_style(test_text, ref_texts)
    assert 0 <= similarity <= 1


def test_extract_style_features():
    """Test style feature extraction."""
    text = "Hello! How are you? I'm great."
    features = extract_style_features(text)
    
    assert "avg_sentence_length" in features
    assert "avg_word_length" in features
    assert features["question_count"] == 1
    assert features["exclamation_count"] == 1