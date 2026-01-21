# Getting Started - What's Missing Checklist

## ✅ What You Have
- Complete project structure
- All source code files
- Configuration templates
- Documentation

## ❌ What's Missing to Run

### 1. Environment Configuration (REQUIRED)
```bash
# Create .env file
cp env.example .env
# Edit .env with your settings
```

**Minimum required settings:**
- `INFERENCE_ENGINE=ollama` (or `vllm`)
- `OLLAMA_BASE_URL=http://localhost:11434` (if using Ollama)
- `PERSONA_NAME=Your Name`

### 2. Python Dependencies (REQUIRED)
```bash
# Install dependencies
pip install -r requirements.txt

# Or use setup script
./setup.sh
```

**Note**: Some packages may require:
- CUDA toolkit (for GPU training)
- System libraries (build-essential on Linux)

### 3. Training Data (REQUIRED for training)
```bash
# Export your data to:
data/raw/gmail.csv      # Gmail export
data/raw/texts.json     # Text messages export
```

**Data formats:**
- **Gmail CSV**: `thread_id,is_outgoing,body,subject,from_email,to_email,timestamp`
- **Texts JSON**: Array of `{thread_id, timestamp, is_outgoing, body, contact}`

### 4. Trained Model (REQUIRED for inference)
```bash
# Option A: Train your own
python src/train.py

# Option B: Use base model (less accurate)
# Just use Ollama with base Llama-3.1-8B
ollama pull llama3.1:8b
```

### 5. RAG Index (REQUIRED for RAG features)
```bash
# After training, index the dataset
python src/rag.py --dataset data/processed/train.jsonl
```

### 6. Inference Engine (REQUIRED for API)
```bash
# Option A: Ollama (local, easier)
ollama pull llama3.1:8b
# Or your fine-tuned model

# Option B: vLLM (cloud, faster)
# Start vLLM server separately
```

### 7. Gmail Credentials (OPTIONAL - only for Gmail integration)
```bash
# Download from Google Cloud Console
# Save as: credentials.json
# Then run: python src/integrations/gmail.py
```

## 🚀 Quick Start (Minimal Setup)

### For Testing (No Training Required)
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create .env
cp env.example .env
# Edit: INFERENCE_ENGINE=ollama

# 3. Install Ollama
# macOS: brew install ollama
# Linux: curl -fsSL https://ollama.com/install.sh | sh

# 4. Pull base model
ollama pull llama3.1:8b

# 5. Start API (RAG will be disabled without index)
uvicorn src.server:app --host 0.0.0.0 --port 8000

# 6. Test
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"context": "Hey, how are you?", "use_rag": false}'
```

### For Full Pipeline (With Training)
```bash
# 1. Setup
./setup.sh

# 2. Configure
cp env.example .env
# Edit .env

# 3. Add your data
# Export Gmail/texts to data/raw/

# 4. Prepare data
python src/data_prep.py

# 5. Train (requires GPU)
python src/train.py

# 6. Index RAG
python src/rag.py --dataset data/processed/train.jsonl

# 7. Start API
uvicorn src.server:app
```

## 🔍 Troubleshooting

### "Module not found"
- Run: `pip install -r requirements.txt`
- Check Python version: `python --version` (needs 3.11+)

### "Ollama connection failed"
- Install Ollama: https://ollama.com
- Start Ollama: `ollama serve`
- Pull model: `ollama pull llama3.1:8b`

### "RAG system not initialized"
- Run: `python src/rag.py --dataset data/processed/train.jsonl`
- Check: `data/chroma/` directory exists

### "No training data found"
- Export data to `data/raw/gmail.csv` or `data/raw/texts.json`
- Check file formats match expected schema

### "Out of memory" (training)
- Use cloud GPU (RunPod, Vast.ai)
- Or reduce batch size in `src/train.py`

## 📋 Pre-Flight Checklist

Before running, ensure:
- [ ] `.env` file created and configured
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Python 3.11+ installed
- [ ] (For training) GPU with 24GB+ VRAM or cloud GPU access
- [ ] (For inference) Ollama installed and model pulled
- [ ] (For RAG) Dataset indexed
- [ ] (For Gmail) `credentials.json` downloaded

## 🎯 Minimum Viable Setup

To just test the API without training:
1. Install dependencies
2. Create `.env` with `INFERENCE_ENGINE=ollama`
3. Install Ollama and pull `llama3.1:8b`
4. Start API server
5. Test with `use_rag: false`

This will work but won't have your personal style - it's just the base model.