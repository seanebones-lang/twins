# Testing Notes - Full Setup Testing

## Branch: `testing-setup`

This branch is for comprehensive testing of the full setup process.

## Testing Checklist

### Phase 1: Basic Setup
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Create `.env` from `env.example`
- [ ] Run `python3 check_setup.py` to verify setup
- [ ] Run `python3 validate_code.py` to verify code

### Phase 2: Data Preparation
- [ ] Add sample data to `data/raw/`
- [ ] Run `python src/data_prep.py`
- [ ] Verify `data/processed/` contains train/val/test splits
- [ ] Check for any errors or warnings

### Phase 3: Model Training (if GPU available)
- [ ] Verify GPU access
- [ ] Run `python src/train.py`
- [ ] Check for training errors
- [ ] Verify model saved to `models/lora_digital_twin/`

### Phase 4: RAG Indexing
- [ ] Run `python src/rag.py --dataset data/processed/train.jsonl`
- [ ] Verify ChromaDB index created
- [ ] Test retrieval: `python src/rag.py --query "test query"`

### Phase 5: API Server
- [ ] Start server: `uvicorn src.server:app`
- [ ] Test health endpoint: `curl http://localhost:8000/health`
- [ ] Test generate endpoint (without RAG)
- [ ] Test generate endpoint (with RAG)
- [ ] Test retrieve endpoint

### Phase 6: Integration Tests
- [ ] Run `pytest tests/ -v`
- [ ] Check all tests pass
- [ ] Note any failures

### Phase 7: Docker (Optional)
- [ ] Build: `docker-compose build`
- [ ] Run: `docker-compose up`
- [ ] Test API in container
- [ ] Check logs for errors

## Issues Found

### Critical Issues
- None yet

### Warnings
- None yet

### Notes
- Add notes here as testing progresses

## Test Results

### Date: [Date]
### Tester: [Name]
### Environment: [OS, Python version, GPU info]

### Results Summary
- Setup: [Pass/Fail]
- Data Prep: [Pass/Fail]
- Training: [Pass/Fail/Skipped]
- RAG: [Pass/Fail]
- API: [Pass/Fail]
- Tests: [Pass/Fail]

## Next Steps
- [ ] Document any issues found
- [ ] Create fixes if needed
- [ ] Merge back to main if successful