"""Tests for data preparation pipeline."""
import pytest
import json
import tempfile
from pathlib import Path
from src.data_prep import parse_emails, parse_texts, scrub_pii, chunk_threads


def test_scrub_pii():
    """Test PII scrubbing."""
    text = "My email is john@example.com and my phone is 555-1234"
    scrubbed = scrub_pii(text)
    assert "[REDACTED]" in scrubbed or "john@example.com" not in scrubbed


def test_parse_emails():
    """Test email parsing."""
    # Create temporary CSV
    import pandas as pd
    
    data = {
        'thread_id': ['1', '1', '2'],
        'is_outgoing': [False, True, True],
        'body': ['Hello', 'Hi there', 'Thanks'],
        'subject': ['Test', 'Test', 'Test2'],
        'from_email': ['other@example.com', 'me@example.com', 'me@example.com'],
        'to_email': ['me@example.com', 'other@example.com', 'other@example.com'],
        'timestamp': ['2024-01-01', '2024-01-02', '2024-01-03']
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df = pd.DataFrame(data)
        df.to_csv(f.name, index=False)
        
        threads = parse_emails(f.name)
        assert len(threads) > 0
        assert 'messages' in threads[0]
    
    Path(f.name).unlink()


def test_chunk_threads():
    """Test thread chunking."""
    threads = [{
        "messages": [
            {"role": "system", "content": "You are a digital twin."},
            {"role": "user", "content": "Short context"},
            {"role": "assistant", "content": "Short reply"}
        ]
    }]
    
    chunked = chunk_threads(threads, max_tokens=400)
    assert len(chunked) > 0