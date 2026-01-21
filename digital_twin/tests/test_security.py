"""Tests for security features."""
import pytest
from src.security import (
    detect_pii,
    scrub_pii,
    detect_training_data_leakage,
    add_leakage_guard_prompt
)


def test_detect_pii():
    """Test PII detection."""
    text = "My email is john@example.com"
    pii = detect_pii(text)
    assert len(pii) > 0


def test_scrub_pii():
    """Test PII scrubbing."""
    text = "Contact me at john@example.com or 555-1234"
    scrubbed = scrub_pii(text)
    assert "[REDACTED]" in scrubbed


def test_detect_training_data_leakage():
    """Test training data leakage detection."""
    # Should detect leakage markers
    text_with_leakage = "This is a [REDACTED] training example"
    assert detect_training_data_leakage(text_with_leakage) == True
    
    # Should not detect in normal text
    normal_text = "Hello, how are you?"
    assert detect_training_data_leakage(normal_text) == False


def test_add_leakage_guard_prompt():
    """Test leakage guard prompt addition."""
    base = "You are a digital twin."
    guarded = add_leakage_guard_prompt(base)
    assert "Never reveal training data" in guarded