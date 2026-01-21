"""
Evaluation suite for digital twin AI.
Includes perplexity, stylometry (Burrows' Delta), and Turing test metrics.
"""
import os
import json
import numpy as np
from typing import List, Dict, Any
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from datasets import load_dataset
from dotenv import load_dotenv

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

load_dotenv()

TEST_DATA_PATH = os.getenv("TEST_DATA_PATH", "data/processed/test.jsonl")


def compute_perplexity(text: str, model_path: str = None) -> float:
    """
    Compute perplexity of text (simplified version).
    For full perplexity, use a language model's log probabilities.
    
    Args:
        text: Input text
        model_path: Path to model (not used in simplified version)
    
    Returns:
        Approximate perplexity score
    """
    # Simplified perplexity: based on word frequency
    # For accurate perplexity, use model's log probabilities
    words = text.lower().split()
    if len(words) == 0:
        return float('inf')
    
    # Simple approximation: inverse of average word length
    avg_word_length = np.mean([len(w) for w in words])
    perplexity = 1.0 / (avg_word_length + 1e-6)
    
    return perplexity


def burrows_delta(test_text: str, reference_texts: List[str], n_features: int = 500) -> float:
    """
    Compute Burrows' Delta (stylometric distance).
    Lower delta = more similar style.
    
    Args:
        test_text: Text to evaluate
        reference_texts: List of reference texts (person's actual messages)
        n_features: Number of most frequent words to use
    
    Returns:
        Burrows' Delta score
    """
    if not reference_texts:
        return float('inf')
    
    # Combine all texts
    all_texts = [test_text] + reference_texts
    
    # Create TF-IDF vectors
    vectorizer = TfidfVectorizer(
        max_features=n_features,
        token_pattern=r'\b\w+\b',
        lowercase=True
    )
    
    try:
        tfidf_matrix = vectorizer.fit_transform(all_texts)
    except ValueError:
        # Fallback if no valid features
        return float('inf')
    
    # Get test vector and reference vectors
    test_vector = tfidf_matrix[0:1]
    ref_vectors = tfidf_matrix[1:]
    
    # Compute mean reference vector
    mean_ref_vector = ref_vectors.mean(axis=0)
    
    # Compute Manhattan distance (Burrows' Delta)
    delta = np.abs(test_vector - mean_ref_vector).sum()
    
    return float(delta)


def cosine_similarity_style(test_text: str, reference_texts: List[str]) -> float:
    """
    Compute cosine similarity between test text and reference texts.
    Higher similarity = more similar style.
    
    Args:
        test_text: Text to evaluate
        reference_texts: List of reference texts
    
    Returns:
        Average cosine similarity (0-1)
    """
    if not reference_texts:
        return 0.0
    
    # Create TF-IDF vectors
    vectorizer = TfidfVectorizer(
        max_features=1000,
        token_pattern=r'\b\w+\b',
        lowercase=True
    )
    
    try:
        all_texts = [test_text] + reference_texts
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        
        # Get test vector and reference vectors
        test_vector = tfidf_matrix[0:1]
        ref_vectors = tfidf_matrix[1:]
        
        # Compute similarities
        similarities = cosine_similarity(test_vector, ref_vectors)[0]
        
        return float(np.mean(similarities))
    except ValueError:
        return 0.0


def extract_style_features(text: str) -> Dict[str, Any]:
    """
    Extract style features from text.
    
    Args:
        text: Input text
    
    Returns:
        Dictionary of style features
    """
    words = text.split()
    sentences = nltk.sent_tokenize(text)
    
    features = {
        "avg_sentence_length": len(words) / max(len(sentences), 1),
        "avg_word_length": np.mean([len(w) for w in words]) if words else 0,
        "num_sentences": len(sentences),
        "num_words": len(words),
        "num_chars": len(text),
        "exclamation_count": text.count('!'),
        "question_count": text.count('?'),
        "emoji_count": sum(1 for c in text if ord(c) > 127),  # Rough emoji detection
        "uppercase_ratio": sum(1 for c in text if c.isupper()) / max(len(text), 1),
    }
    
    return features


def compare_styles(test_text: str, reference_texts: List[str]) -> Dict[str, float]:
    """
    Compare style features between test and reference texts.
    
    Args:
        test_text: Text to evaluate
        reference_texts: List of reference texts
    
    Returns:
        Dictionary of style comparison metrics
    """
    test_features = extract_style_features(test_text)
    
    if not reference_texts:
        return {"error": "No reference texts provided"}
    
    # Compute average reference features
    ref_features_list = [extract_style_features(ref) for ref in reference_texts]
    avg_ref_features = {
        key: np.mean([f[key] for f in ref_features_list])
        for key in test_features.keys()
    }
    
    # Compute differences
    differences = {}
    for key in test_features.keys():
        if avg_ref_features[key] > 0:
            diff = abs(test_features[key] - avg_ref_features[key]) / avg_ref_features[key]
            differences[key] = float(diff)
        else:
            differences[key] = 0.0
    
    # Overall style similarity (inverse of average difference)
    avg_diff = np.mean(list(differences.values()))
    style_similarity = 1.0 / (1.0 + avg_diff)
    
    return {
        "style_similarity": float(style_similarity),
        "feature_differences": differences,
        "test_features": test_features,
        "avg_reference_features": avg_ref_features
    }


def turing_test(generated_texts: List[str], real_texts: List[str], evaluators: List[str] = None) -> Dict[str, Any]:
    """
    Simulate a Turing test (blind evaluation).
    
    Args:
        generated_texts: List of AI-generated texts
        real_texts: List of real person's texts
        evaluators: List of evaluator names (optional)
    
    Returns:
        Dictionary with Turing test results
    """
    # Mix texts randomly
    all_texts = generated_texts + real_texts
    labels = [0] * len(generated_texts) + [1] * len(real_texts)
    
    # Shuffle
    indices = np.random.permutation(len(all_texts))
    shuffled_texts = [all_texts[i] for i in indices]
    shuffled_labels = [labels[i] for i in indices]
    
    # For simulation, use style similarity as "human judgment"
    # In real test, humans would evaluate
    correct_guesses = 0
    total = len(shuffled_texts)
    
    # Simple heuristic: if style is very similar, might be mistaken for real
    for i, text in enumerate(shuffled_texts):
        is_generated = shuffled_labels[i] == 0
        
        # Compute style similarity to real texts
        similarity = cosine_similarity_style(text, real_texts)
        
        # If similarity is high, might fool evaluator
        # If similarity is low and it's generated, might be detected
        if similarity > 0.7 and is_generated:
            # High similarity generated text might fool evaluator
            correct_guesses += 0  # Fooled (incorrect guess)
        elif similarity < 0.5 and is_generated:
            # Low similarity generated text might be detected
            correct_guesses += 1  # Correctly identified as AI
        elif not is_generated:
            # Real text should be identified as real
            correct_guesses += 0.8  # Mostly correct
    
    deception_rate = 1.0 - (correct_guesses / total)
    
    return {
        "deception_rate": float(deception_rate),
        "correct_identification_rate": float(correct_guesses / total),
        "total_texts": total,
        "generated_count": len(generated_texts),
        "real_count": len(real_texts)
    }


def evaluate_model(test_data_path: str = None, model_api_url: str = None) -> Dict[str, Any]:
    """
    Comprehensive model evaluation.
    
    Args:
        test_data_path: Path to test dataset
        model_api_url: API URL for model inference
    
    Returns:
        Dictionary with evaluation metrics
    """
    test_data_path = test_data_path or TEST_DATA_PATH
    model_api_url = model_api_url or "http://localhost:8000"
    
    if not Path(test_data_path).exists():
        return {"error": f"Test data not found: {test_data_path}"}
    
    # Load test data
    dataset = load_dataset("json", data_files=test_data_path, split="train")
    
    # Extract reference texts (actual person's replies)
    reference_texts = []
    test_contexts = []
    
    for example in dataset:
        messages = example.get("messages", [])
        user_msg = next((m for m in messages if m['role'] == 'user'), None)
        assistant_msg = next((m for m in messages if m['role'] == 'assistant'), None)
        
        if user_msg and assistant_msg:
            reference_texts.append(assistant_msg['content'])
            test_contexts.append(user_msg['content'])
    
    if len(reference_texts) == 0:
        return {"error": "No reference texts found in test data"}
    
    # Generate replies using model API
    import requests
    generated_texts = []
    
    print(f"Generating {len(test_contexts)} test replies...")
    for context in test_contexts[:50]:  # Limit to 50 for speed
        try:
            response = requests.post(
                f"{model_api_url}/generate",
                json={"context": context, "use_rag": True},
                timeout=30
            )
            if response.status_code == 200:
                result = response.json()
                generated_texts.append(result['reply'])
            else:
                print(f"API error: {response.status_code}")
        except Exception as e:
            print(f"Failed to generate: {e}")
    
    if len(generated_texts) == 0:
        return {"error": "Failed to generate any test replies"}
    
    # Compute metrics
    print("Computing metrics...")
    
    # Style comparison
    style_scores = []
    for gen_text, ref_text in zip(generated_texts[:20], reference_texts[:20]):
        score = cosine_similarity_style(gen_text, [ref_text])
        style_scores.append(score)
    
    avg_style_similarity = np.mean(style_scores)
    
    # Burrows' Delta
    delta_scores = []
    for gen_text in generated_texts[:20]:
        delta = burrows_delta(gen_text, reference_texts[:50])
        delta_scores.append(delta)
    
    avg_delta = np.mean(delta_scores)
    
    # Turing test
    turing_results = turing_test(
        generated_texts[:20],
        reference_texts[:20]
    )
    
    return {
        "avg_style_similarity": float(avg_style_similarity),
        "avg_burrows_delta": float(avg_delta),
        "turing_test": turing_results,
        "num_evaluated": len(generated_texts),
        "num_reference": len(reference_texts)
    }


def main():
    """Run evaluation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate digital twin model")
    parser.add_argument(
        "--test-data",
        type=str,
        default=TEST_DATA_PATH,
        help="Path to test dataset"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000",
        help="Model API URL"
    )
    
    args = parser.parse_args()
    
    results = evaluate_model(args.test_data, args.api_url)
    
    print("\n" + "="*50)
    print("EVALUATION RESULTS")
    print("="*50)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()