"""
Data preparation pipeline for digital twin training.
Handles parsing, PII scrubbing, chunking, and JSONL formatting.
"""
import json
import pandas as pd
import re
from pathlib import Path
from typing import List, Dict, Any
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from datasets import Dataset
import yaml
from tqdm import tqdm
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize PII detection and anonymization
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

# Load persona config
PERSONA_NAME = os.getenv("PERSONA_NAME", "Digital Twin")
PERSONA_CONFIG_PATH = os.getenv("PERSONA_CONFIG_PATH", "config/persona.yaml")


def load_persona_config() -> Dict[str, Any]:
    """Load persona configuration from YAML."""
    with open(PERSONA_CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)


def scrub_pii(text: str, aggressive: bool = True) -> str:
    """
    Remove or anonymize PII from text.
    
    Args:
        text: Input text to scrub
        aggressive: If True, replace with [REDACTED], else anonymize
        
    Returns:
        Text with PII removed/anonymized
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Detect PII
    results = analyzer.analyze(text=text, language='en')
    
    if aggressive:
        # Simple replacement approach
        for entity in sorted(results, key=lambda x: x.start, reverse=True):
            text = text[:entity.start] + '[REDACTED]' + text[entity.end:]
    else:
        # Use anonymizer for more sophisticated replacement
        anonymized = anonymizer.anonymize(text=text, analyzer_results=results)
        text = anonymized.text
    
    return text


def parse_emails(csv_path: str, min_length: int = 10) -> List[Dict[str, Any]]:
    """
    Parse Gmail export CSV and create training examples.
    
    Expected CSV columns:
    - thread_id: Thread identifier
    - is_outgoing: Boolean for sent messages
    - body: Message body
    - subject: Email subject
    - from_email: Sender email
    - to_email: Recipient email
    - timestamp: Message timestamp
    """
    if not Path(csv_path).exists():
        print(f"Warning: {csv_path} not found. Skipping email parsing.")
        return []
    
    df = pd.read_csv(csv_path)
    threads = []
    
    # Group by thread_id
    for thread_id, group in tqdm(df.groupby('thread_id'), desc="Processing email threads"):
        # Get incoming messages (context)
        incoming = group[group['is_outgoing'] == False].sort_values('timestamp')
        # Get outgoing messages (target responses)
        outgoing = group[group['is_outgoing'] == True].sort_values('timestamp')
        
        if len(outgoing) == 0:
            continue
        
        # For each outgoing message, create a training example
        for idx, out_msg in outgoing.iterrows():
            # Get context (last 5 incoming messages before this reply)
            context_msgs = incoming[incoming['timestamp'] < out_msg['timestamp']].tail(5)
            
            if len(context_msgs) == 0:
                # No context, use subject or create minimal context
                context = f"Subject: {out_msg.get('subject', 'No subject')}"
            else:
                context_parts = []
                for _, ctx in context_msgs.iterrows():
                    ctx_body = str(ctx.get('body', ''))[:200]  # Limit length
                    if ctx_body:
                        context_parts.append(f"From: {ctx.get('from_email', 'Unknown')}\n{ctx_body}")
                context = "\n\n---\n\n".join(context_parts)
            
            reply_body = str(out_msg.get('body', ''))
            if len(reply_body) < min_length:
                continue
            
            # Scrub PII
            context = scrub_pii(context)
            reply_body = scrub_pii(reply_body)
            
            # Load persona config
            persona_config = load_persona_config()
            persona_desc = persona_config.get('description', '')
            
            threads.append({
                "messages": [
                    {
                        "role": "system",
                        "content": persona_desc
                    },
                    {
                        "role": "user",
                        "content": context
                    },
                    {
                        "role": "assistant",
                        "content": reply_body
                    }
                ]
            })
    
    return threads


def parse_texts(json_path: str, min_length: int = 5) -> List[Dict[str, Any]]:
    """
    Parse SMS/iMessage/WhatsApp export JSON and create training examples.
    
    Expected JSON format:
    [
      {
        "thread_id": "contact_name",
        "timestamp": "2024-01-01T12:00:00",
        "is_outgoing": true,
        "body": "Message text",
        "contact": "Contact name"
      }
    ]
    """
    if not Path(json_path).exists():
        print(f"Warning: {json_path} not found. Skipping text parsing.")
        return []
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    threads = []
    
    # Group by thread_id
    df = pd.DataFrame(data)
    for thread_id, group in tqdm(df.groupby('thread_id'), desc="Processing text threads"):
        # Sort by timestamp
        group = group.sort_values('timestamp')
        
        # Create conversation pairs
        for i in range(len(group)):
            msg = group.iloc[i]
            
            if not msg['is_outgoing']:
                continue  # Skip incoming messages as targets
            
            # Get previous messages as context (last 5)
            context_msgs = group.iloc[max(0, i-5):i]
            
            if len(context_msgs) == 0:
                context = "New conversation"
            else:
                context_parts = []
                for _, ctx in context_msgs.iterrows():
                    ctx_body = str(ctx.get('body', ''))
                    if ctx_body:
                        direction = "You" if ctx['is_outgoing'] else ctx.get('contact', 'Them')
                        context_parts.append(f"{direction}: {ctx_body}")
                context = "\n".join(context_parts)
            
            reply_body = str(msg.get('body', ''))
            if len(reply_body) < min_length:
                continue
            
            # Scrub PII
            context = scrub_pii(context)
            reply_body = scrub_pii(reply_body)
            
            persona_config = load_persona_config()
            persona_desc = persona_config.get('description', '')
            
            threads.append({
                "messages": [
                    {
                        "role": "system",
                        "content": persona_desc
                    },
                    {
                        "role": "user",
                        "content": context
                    },
                    {
                        "role": "assistant",
                        "content": reply_body
                    }
                ]
            })
    
    return threads


def chunk_threads(threads: List[Dict[str, Any]], max_tokens: int = 400) -> List[Dict[str, Any]]:
    """
    Chunk long threads to fit within token limits.
    Simple approximation: 1 token ≈ 0.75 words
    """
    chunked = []
    
    for thread in tqdm(threads, desc="Chunking threads"):
        # Estimate tokens (rough approximation)
        full_text = json.dumps(thread)
        word_count = len(full_text.split())
        estimated_tokens = int(word_count * 1.3)
        
        if estimated_tokens <= max_tokens:
            chunked.append(thread)
        else:
            # Split long threads - take first part of conversation
            messages = thread['messages']
            if len(messages) >= 3:
                # Keep system + user + assistant, but truncate content
                system_msg = messages[0]
                user_msg = messages[1]
                assistant_msg = messages[2]
                
                # Truncate user context
                user_content = user_msg['content']
                max_user_tokens = max_tokens // 3
                user_words = user_content.split()
                if len(user_words) > max_user_tokens:
                    user_content = ' '.join(user_words[-max_user_tokens:])
                
                # Truncate assistant reply
                assistant_content = assistant_msg['content']
                max_assistant_tokens = max_tokens // 2
                assistant_words = assistant_content.split()
                if len(assistant_words) > max_assistant_tokens:
                    assistant_content = ' '.join(assistant_words[:max_assistant_tokens])
                
                chunked.append({
                    "messages": [
                        system_msg,
                        {"role": "user", "content": user_content},
                        {"role": "assistant", "content": assistant_content}
                    ]
                })
    
    return chunked


def deduplicate(threads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate training examples."""
    seen = set()
    unique = []
    
    for thread in threads:
        # Create hash from assistant message (the target output)
        assistant_msg = next((m for m in thread['messages'] if m['role'] == 'assistant'), None)
        if assistant_msg:
            content_hash = hash(assistant_msg['content'].strip().lower())
            if content_hash not in seen:
                seen.add(content_hash)
                unique.append(thread)
    
    return unique


def main():
    """Main data preparation pipeline."""
    data_dir = Path("data")
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    
    # Ensure directories exist
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    all_threads = []
    
    # Parse emails
    email_csv = raw_dir / "gmail.csv"
    if email_csv.exists():
        print("Parsing emails...")
        email_threads = parse_emails(str(email_csv))
        all_threads.extend(email_threads)
        print(f"Parsed {len(email_threads)} email examples")
    
    # Parse texts
    texts_json = raw_dir / "texts.json"
    if texts_json.exists():
        print("Parsing texts...")
        text_threads = parse_texts(str(texts_json))
        all_threads.extend(text_threads)
        print(f"Parsed {len(text_threads)} text examples")
    
    if len(all_threads) == 0:
        print("ERROR: No data found. Please export data to data/raw/")
        print("Expected files: data/raw/gmail.csv or data/raw/texts.json")
        return
    
    # Deduplicate
    print(f"Total examples before deduplication: {len(all_threads)}")
    all_threads = deduplicate(all_threads)
    print(f"Total examples after deduplication: {len(all_threads)}")
    
    # Chunk long threads
    print("Chunking threads...")
    all_threads = chunk_threads(all_threads)
    print(f"Final examples after chunking: {len(all_threads)}")
    
    # Split into train/val/test
    dataset = Dataset.from_list(all_threads)
    splits = dataset.train_test_split(test_size=0.15, seed=42)
    val_test = splits['test'].train_test_split(test_size=0.5, seed=42)
    
    train_data = splits['train']
    val_data = val_test['train']
    test_data = val_test['test']
    
    # Save as JSONL
    train_path = processed_dir / "train.jsonl"
    val_path = processed_dir / "val.jsonl"
    test_path = processed_dir / "test.jsonl"
    
    print(f"Saving {len(train_data)} training examples...")
    with open(train_path, 'w', encoding='utf-8') as f:
        for item in train_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"Saving {len(val_data)} validation examples...")
    with open(val_path, 'w', encoding='utf-8') as f:
        for item in val_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"Saving {len(test_data)} test examples...")
    with open(test_path, 'w', encoding='utf-8') as f:
        for item in test_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"\n✅ Data preparation complete!")
    print(f"Training: {len(train_data)} examples")
    print(f"Validation: {len(val_data)} examples")
    print(f"Test: {len(test_data)} examples")


if __name__ == "__main__":
    main()