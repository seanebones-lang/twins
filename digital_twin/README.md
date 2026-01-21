# Digital Twin AI

A production-ready system for creating AI that mimics someone's exact communication style (tone, vocabulary, sentence structure, abbreviations, emojis, quirks, formality level) for emails, texts, and similar communications.

## 🎯 Overview

This project implements a complete pipeline for building a "digital twin" AI that can generate replies in your exact communication style. It combines:

- **Fine-tuning** with LoRA (Unsloth) on Llama-3.1-8B
- **RAG (Retrieval-Augmented Generation)** for style consistency
- **FastAPI** inference server with rate limiting
- **Gmail/Text integrations** for real-world use
- **Comprehensive evaluation** (perplexity, stylometry, Turing tests)
- **Security & Privacy** (PII scrubbing, leakage guards)

**Note**: This is designed for **self-use** or with **explicit consent**. Always disclose AI-generated content when appropriate.

## 📋 Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Data Collection](#data-collection)
- [Training](#training)
- [Deployment](#deployment)
- [API Usage](#api-usage)
- [Evaluation](#evaluation)
- [Security & Privacy](#security--privacy)
- [Architecture](#architecture)
- [Troubleshooting](#troubleshooting)

## ✨ Features

- **Efficient Fine-tuning**: LoRA/QLoRA with Unsloth (2x faster, 60% less VRAM)
- **RAG System**: ChromaDB + LangChain for style retrieval
- **Multiple Inference Engines**: Ollama (local) or vLLM (cloud)
- **Gmail Integration**: OAuth2, inbox polling, draft creation
- **Text Integrations**: Webhook examples for WhatsApp, Telegram, SMS
- **Evaluation Suite**: Perplexity, Burrows' Delta, cosine similarity, Turing tests
- **Security**: PII scrubbing (Presidio), leakage detection, consent management
- **Docker Support**: Full containerization with docker-compose

## 🚀 Quick Start

### 1. Clone and Install

```bash
git clone <your-repo>
cd digital_twin
pip install -r requirements.txt
```

### 2. Configure

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Collect Data

Export your communication data to `data/raw/`:

- **Gmail**: Use Google Takeout or Gmail API → `data/raw/gmail.csv`
- **Texts**: Export SMS/iMessage/WhatsApp → `data/raw/texts.json`

See [Data Collection](#data-collection) for detailed instructions.

### 4. Prepare Data

```bash
python src/data_prep.py
```

This will:
- Parse emails/texts
- Scrub PII
- Chunk long threads
- Create train/val/test splits
- Output JSONL files to `data/processed/`

### 5. Train Model

```bash
python src/train.py
```

**Requirements**:
- GPU with 24GB+ VRAM (RTX 4090, A100) for 8B model
- Or use cloud GPU (RunPod, Vast.ai, Lambda Labs) - ~$10-100 for training

Training time: ~2-4 hours for 25k examples on good GPU.

### 6. Index RAG

```bash
python src/rag.py --dataset data/processed/train.jsonl
```

### 7. Start API Server

```bash
# Using Ollama (local)
ollama pull llama3.1:8b
uvicorn src.server:app --host 0.0.0.0 --port 8000

# Or using Docker
docker-compose up
```

### 8. Test

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"context": "Hey, meeting tomorrow?", "use_rag": true}'
```

## 📦 Installation

### System Requirements

- Python 3.11+
- CUDA-capable GPU (recommended) or CPU (slower)
- 50GB+ disk space for models and data

### Dependencies

All dependencies are in `requirements.txt`. Key packages:

- `unsloth`: Fast LoRA fine-tuning
- `langchain`: RAG orchestration
- `chromadb`: Vector database
- `fastapi`: API server
- `presidio`: PII detection
- `transformers`: Model loading

### GPU Setup (Optional but Recommended)

For CUDA:

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

## 📊 Data Collection

### Gmail Export

**Option 1: Google Takeout**
1. Go to https://takeout.google.com
2. Select "Mail" → "All mail data included"
3. Download and extract
4. Convert to CSV format (see `scripts/convert_gmail.py`)

**Option 2: Gmail API**
```bash
# Use src/integrations/gmail.py to export via API
python src/integrations/gmail.py --export
```

**Expected CSV format**:
```csv
thread_id,is_outgoing,body,subject,from_email,to_email,timestamp
1,False,Hello,Test,other@example.com,me@example.com,2024-01-01
1,True,Hi there,Test,me@example.com,other@example.com,2024-01-02
```

### Text Messages Export

**iOS (iMessage)**:
- Use [iMazing](https://imazing.com/) or similar tool
- Export as JSON

**Android (SMS)**:
- Use SMS Backup & Restore app
- Export as JSON

**WhatsApp/Telegram**:
- Use official export features
- Convert to JSON format

**Expected JSON format**:
```json
[
  {
    "thread_id": "contact_name",
    "timestamp": "2024-01-01T12:00:00",
    "is_outgoing": true,
    "body": "Message text",
    "contact": "Contact name"
  }
]
```

### Data Volume Recommendations

- **Minimum**: 1,000-5,000 messages
- **Good**: 10,000-50,000 messages
- **Excellent**: 100,000+ messages

More data = better style capture, but diminishing returns after ~100k.

## 🎓 Training

### Fine-tuning Configuration

Edit `config/axolotl.yaml` or use environment variables:

```bash
export MODEL_NAME=unsloth/llama-3.1-8b-bnb-4bit
export TRAIN_EPOCHS=2
export LEARNING_RATE=2e-4
export LORA_RANK=32
```

### Training Process

1. **Load base model**: Llama-3.1-8B (4-bit quantized)
2. **Apply LoRA**: Rank 32, alpha 64
3. **Train**: 2 epochs, batch size 2, gradient accumulation 4
4. **Save**: LoRA weights to `models/lora_digital_twin/`

### Training on Cloud GPU

**RunPod Example**:
```bash
# 1. Create pod with RTX 4090 (24GB)
# 2. Upload code and data
# 3. Install dependencies
pip install -r requirements.txt
# 4. Train
python src/train.py
# 5. Download model
```

**Cost**: ~$0.20-0.50/hour × 2-4 hours = $0.40-2.00

### Post-Training

**Merge LoRA weights** (optional):
```bash
python src/merge_lora.py
```

**Convert to GGUF** (for Ollama):
```bash
# Use llama.cpp
./llama.cpp/convert.py models/merged --outfile models/digital_twin.gguf
```

**Load in Ollama**:
```bash
ollama create digital_twin -f Modelfile
# Modelfile:
# FROM ./models/digital_twin.gguf
# TEMPLATE """{{ .System }}
# {{ .Prompt }}"""
```

## 🚢 Deployment

### Docker

```bash
# Build and run
docker-compose up -d

# Check logs
docker-compose logs -f api

# Stop
docker-compose down
```

### Local Deployment

```bash
# Start API
uvicorn src.server:app --host 0.0.0.0 --port 8000

# Start with reload (development)
uvicorn src.server:app --reload
```

### Cloud Deployment

**Option 1: vLLM on Cloud GPU**
```bash
# Start vLLM server
python -m vllm.entrypoints.openai.api_server \
  --model models/digital_twin \
  --port 8001

# Update .env
INFERENCE_ENGINE=vllm
VLLM_HOST=0.0.0.0
VLLM_PORT=8001
```

**Option 2: Hugging Face Inference Endpoints**
- Deploy via HF Spaces or Inference Endpoints
- Use API URL in FastAPI server

## 📡 API Usage

### Generate Reply

```bash
POST /generate
Content-Type: application/json

{
  "context": "Hey, can we reschedule the meeting?",
  "use_rag": true,
  "max_length": 512,
  "temperature": 0.7
}
```

**Response**:
```json
{
  "reply": "Sure, what time works for you?",
  "retrieved_examples": 5,
  "model": "ollama"
}
```

### Retrieve Similar Examples

```bash
GET /retrieve?query=meeting%20tomorrow&k=5
```

### Health Check

```bash
GET /health
```

## 📈 Evaluation

### Run Evaluation

```bash
python src/eval.py --test-data data/processed/test.jsonl --api-url http://localhost:8000
```

### Metrics

- **Style Similarity**: Cosine similarity (0-1, higher = better)
- **Burrows' Delta**: Stylometric distance (lower = better)
- **Turing Test**: Deception rate (% fooled)
- **Perplexity**: Language model score (lower = better)

### Expected Results

Based on real projects:
- **Style Similarity**: 0.65-0.75 (good), 0.75+ (excellent)
- **Turing Test**: 50-70% deception rate
- **Burrows' Delta**: 20-30% closer than base model

## 🔒 Security & Privacy

### PII Scrubbing

Automatically scrubs:
- Email addresses
- Phone numbers
- Credit cards
- SSNs
- Names (configurable)

### Leakage Guards

- Detects training data markers
- Prevents exact memorization
- Adds guard prompts to generation

### Consent Management

```python
from src.security import record_consent, validate_consent

# Record consent
record_consent("Your Name")

# Check consent
if not validate_consent():
    print("Consent required")
```

### API Security

- Rate limiting: 10 requests/minute (configurable)
- API key authentication (optional)
- CORS configuration
- Audit logging

## 🏗️ Architecture

```
┌─────────────┐
│ Data Export │ (Gmail, Texts)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Data Prep   │ (Parse, Scrub PII, Chunk)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Fine-tune   │ (LoRA on Llama-3.1-8B)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ RAG Index   │ (ChromaDB + Embeddings)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ API Server  │ (FastAPI + RAG Chain)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Integrations│ (Gmail, Texts)
└─────────────┘
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/test_eval.py
```

## 🐛 Troubleshooting

### "Model not found"
- Ensure Ollama is running: `ollama list`
- Pull model: `ollama pull llama3.1:8b`
- Or configure vLLM path in `.env`

### "RAG system not initialized"
- Run indexing: `python src/rag.py --dataset data/processed/train.jsonl`
- Check ChromaDB path in `.env`

### "Out of memory" during training
- Reduce batch size: `BATCH_SIZE=1`
- Use 4-bit quantization (already enabled)
- Use gradient checkpointing (already enabled)
- Train on cloud GPU with more VRAM

### "No data found"
- Check `data/raw/` contains `gmail.csv` or `texts.json`
- Verify file formats match expected schema
- Check file permissions

## 📚 Additional Resources

- [Unsloth Documentation](https://github.com/unslothai/unsloth)
- [LangChain RAG Guide](https://python.langchain.com/docs/use_cases/question_answering/)
- [Gmail API Guide](https://developers.google.com/gmail/api)
- [LoRA Fine-tuning Guide](https://huggingface.co/docs/peft/conceptual_guides/lora)

## ⚖️ Ethics & Legal

**Important**:
- ✅ Use for **your own data** or with **explicit consent**
- ✅ Always **disclose AI-generated content** when appropriate
- ❌ Do **not** impersonate others without permission
- ❌ Do **not** use for deceptive purposes
- ⚠️ Models can **leak training data** - scrub PII aggressively
- ⚠️ Review all generated content before sending

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- Unsloth team for efficient fine-tuning
- LangChain for RAG framework
- Hugging Face for model hosting
- Presidio for PII detection

---

**Built with ❤️ for empowering personal productivity**

For questions or issues, please open a GitHub issue.