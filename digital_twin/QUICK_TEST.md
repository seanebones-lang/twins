# Quick Testing Guide

## Fast Testing (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Automated Tests
```bash
./run_tests.sh
```

This will test:
- ✅ Code validation
- ✅ Import checks
- ✅ Unit tests (if pytest installed)
- ✅ Data prep with sample data
- ✅ RAG system (if data processed)
- ✅ API server imports

### 3. Test with Sample Data

Sample data is included:
- `data/raw/sample_gmail.csv` - Sample Gmail export
- `data/raw/sample_texts.json` - Sample text messages

Run data prep:
```bash
python src/data_prep.py
```

This will create processed data in `data/processed/`

### 4. Test RAG (if data processed)
```bash
python src/rag.py --dataset data/processed/train.jsonl
python src/rag.py --query "meeting reschedule"
```

### 5. Test API Server

**Terminal 1: Start server**
```bash
uvicorn src.server:app --host 0.0.0.0 --port 8000
```

**Terminal 2: Test API**
```bash
./test_api.sh
```

Or manually:
```bash
# Health check
curl http://localhost:8000/health

# Generate reply
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"context": "Hey, how are you?", "use_rag": false}'
```

## Expected Results

### ✅ Should Work Immediately:
- Code validation
- Import checks
- Data prep with sample data
- API server (if Ollama/model available)

### ⚠️ Requires Setup:
- Unit tests (need pytest + dependencies)
- RAG (needs processed data)
- Full training (needs GPU)

## Troubleshooting

### "Module not found"
→ Install: `pip install -r requirements.txt`

### "Ollama connection failed"
→ Start Ollama: `ollama serve`
→ Pull model: `ollama pull llama3.1:8b`

### "RAG not initialized"
→ Index data: `python src/rag.py --dataset data/processed/train.jsonl`

### "No data found"
→ Sample data is in `data/raw/` - should work automatically

## Test Coverage

| Component | Test Type | Status |
|-----------|-----------|--------|
| Code Syntax | Automated | ✅ |
| Imports | Automated | ✅ |
| Data Prep | Sample Data | ✅ |
| RAG | Manual | ⚠️ |
| API | Manual | ⚠️ |
| Training | Manual | ⚠️ |

## Next Steps

After quick tests pass:
1. Add your own data
2. Train model (if GPU available)
3. Test full pipeline
4. Document any issues