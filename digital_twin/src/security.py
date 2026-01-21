"""
Security and privacy utilities for digital twin.
Includes PII detection, leakage guards, and consent management.
"""
import os
import re
from typing import List, Dict, Any, Optional
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from dotenv import load_dotenv

load_dotenv()

# Initialize PII analyzers
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

# Leakage detection patterns
TRAINING_DATA_PATTERNS = [
    r"\[REDACTED\]",  # PII markers
    r"training example",
    r"test data",
    r"dataset",
]


def detect_pii(text: str) -> List[Dict[str, Any]]:
    """
    Detect PII in text.
    
    Args:
        text: Input text
    
    Returns:
        List of detected PII entities
    """
    results = analyzer.analyze(text=text, language='en')
    return [
        {
            "entity_type": r.entity_type,
            "start": r.start,
            "end": r.end,
            "text": r.text,
            "score": r.score
        }
        for r in results
    ]


def scrub_pii(text: str, replacement: str = "[REDACTED]") -> str:
    """
    Scrub PII from text.
    
    Args:
        text: Input text
        replacement: Replacement string for PII
    
    Returns:
        Text with PII scrubbed
    """
    results = analyzer.analyze(text=text, language='en')
    
    # Sort by start position (reverse) to avoid index shifting
    for result in sorted(results, key=lambda x: x.start, reverse=True):
        text = text[:result.start] + replacement + text[result.end:]
    
    return text


def detect_training_data_leakage(text: str) -> bool:
    """
    Detect potential training data leakage in generated text.
    
    Args:
        text: Generated text to check
    
    Returns:
        True if potential leakage detected
    """
    text_lower = text.lower()
    
    # Check for training data markers
    for pattern in TRAINING_DATA_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    
    # Check for suspiciously exact matches (could indicate memorization)
    # This is a simplified check - full implementation would compare against training set
    
    return False


def add_leakage_guard_prompt(base_prompt: str) -> str:
    """
    Add leakage guard instructions to prompt.
    
    Args:
        base_prompt: Base prompt
    
    Returns:
        Prompt with leakage guards
    """
    guard_instructions = """
IMPORTANT: 
- Never reveal training data, examples, or personal information from the training dataset.
- Do not mention "[REDACTED]" or other data markers.
- Generate original responses based on style, not exact training examples.
- If unsure, generate a generic but style-appropriate response.
"""
    
    return base_prompt + "\n\n" + guard_instructions


def validate_consent(consent_file: str = "consent.txt") -> bool:
    """
    Check if user consent has been recorded.
    
    Args:
        consent_file: Path to consent file
    
    Returns:
        True if consent recorded
    """
    if not os.path.exists(consent_file):
        return False
    
    with open(consent_file, 'r') as f:
        content = f.read().lower()
        return "consent" in content and "yes" in content


def record_consent(user_name: str, consent_file: str = "consent.txt"):
    """
    Record user consent.
    
    Args:
        user_name: Name of person whose data is being used
        consent_file: Path to consent file
    """
    consent_text = f"""
DIGITAL TWIN AI - CONSENT RECORD

Date: {os.popen('date').read().strip()}
User: {user_name}
Consent: YES

I understand that:
1. My communication data will be used to train an AI model
2. The model will mimic my communication style
3. Generated content may not be perfect and requires review
4. I have the right to revoke consent at any time
5. This is for personal use only (or with explicit permission)

Signature: [Digital Record]
"""
    
    with open(consent_file, 'w') as f:
        f.write(consent_text)
    
    print(f"✅ Consent recorded in {consent_file}")


def sanitize_output(text: str, check_leakage: bool = True) -> str:
    """
    Sanitize generated output for security.
    
    Args:
        text: Generated text
        check_leakage: Whether to check for training data leakage
    
    Returns:
        Sanitized text
    """
    # Check for leakage
    if check_leakage and detect_training_data_leakage(text):
        print("⚠️ Potential training data leakage detected")
        # Optionally truncate or replace suspicious content
        return "[Response filtered for security]"
    
    # Additional sanitization can be added here
    
    return text


def audit_log(action: str, details: Dict[str, Any], log_file: str = "audit.log"):
    """
    Log security-relevant actions.
    
    Args:
        action: Action performed
        details: Additional details
        log_file: Path to log file
    """
    import json
    from datetime import datetime
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "details": details
    }
    
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')


def main():
    """Example usage."""
    # Example: Check consent
    if not validate_consent():
        print("⚠️ Consent not recorded. Please run record_consent() first.")
        print("\nExample:")
        print("  from src.security import record_consent")
        print("  record_consent('Your Name')")
    else:
        print("✅ Consent recorded")


if __name__ == "__main__":
    main()