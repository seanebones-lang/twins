#!/usr/bin/env python3
"""
Diagnostic script to check what's missing to run the project.
"""
import os
import sys
from pathlib import Path

def check_file(path, name, required=True):
    """Check if a file exists."""
    exists = Path(path).exists()
    status = "✅" if exists else ("❌ REQUIRED" if required else "⚠️  OPTIONAL")
    print(f"{status} {name}: {path}")
    return exists

def check_dir(path, name, required=True):
    """Check if a directory exists."""
    exists = Path(path).exists() and Path(path).is_dir()
    status = "✅" if exists else ("❌ REQUIRED" if required else "⚠️  OPTIONAL")
    print(f"{status} {name}: {path}")
    return exists

def check_python_package(package, name):
    """Check if a Python package is installed."""
    try:
        __import__(package)
        print(f"✅ {name}: installed")
        return True
    except ImportError:
        print(f"❌ {name}: NOT installed (pip install {package})")
        return False

def check_command(command, name):
    """Check if a command is available."""
    import shutil
    if shutil.which(command):
        print(f"✅ {name}: available")
        return True
    else:
        print(f"❌ {name}: NOT found")
        return False

def main():
    print("🔍 Digital Twin AI - Setup Diagnostic\n")
    print("=" * 60)
    
    # Check configuration files
    print("\n📋 Configuration Files:")
    print("-" * 60)
    env_exists = check_file(".env", ".env file", required=False)
    check_file("env.example", "env.example template")
    check_file("config/persona.yaml", "Persona config")
    check_file("config/axolotl.yaml", "Training config")
    
    # Check data directories
    print("\n📁 Data Directories:")
    print("-" * 60)
    check_dir("data/raw", "Raw data directory")
    check_dir("data/processed", "Processed data directory")
    check_dir("data/chroma", "ChromaDB directory")
    check_dir("models", "Models directory")
    
    # Check for data files
    print("\n📊 Data Files:")
    print("-" * 60)
    has_gmail = check_file("data/raw/gmail.csv", "Gmail export", required=False)
    has_texts = check_file("data/raw/texts.json", "Texts export", required=False)
    has_train = check_file("data/processed/train.jsonl", "Training data", required=False)
    has_val = check_file("data/processed/val.jsonl", "Validation data", required=False)
    
    if not (has_gmail or has_texts):
        print("   ⚠️  No raw data found - you'll need to export Gmail/texts")
    
    if not has_train:
        print("   ⚠️  No processed data - run: python src/data_prep.py")
    
    # Check for models
    print("\n🤖 Model Files:")
    print("-" * 60)
    has_lora = check_file("models/lora_digital_twin", "LoRA model", required=False)
    has_merged = check_file("models/merged_digital_twin", "Merged model", required=False)
    has_gguf = check_file("models/digital_twin.gguf", "GGUF model", required=False)
    
    if not (has_lora or has_merged or has_gguf):
        print("   ⚠️  No trained model - run: python src/train.py")
        print("   ⚠️  Or use base model with Ollama: ollama pull llama3.1:8b")
    
    # Check Python packages
    print("\n🐍 Python Packages:")
    print("-" * 60)
    critical_packages = [
        ("fastapi", "FastAPI"),
        ("langchain", "LangChain"),
        ("chromadb", "ChromaDB"),
        ("transformers", "Transformers"),
        ("torch", "PyTorch"),
        ("presidio_analyzer", "Presidio"),
    ]
    
    all_installed = True
    for package, name in critical_packages:
        if not check_python_package(package, name):
            all_installed = False
    
    if not all_installed:
        print("\n   💡 Install missing packages: pip install -r requirements.txt")
    
    # Check external tools
    print("\n🛠️  External Tools:")
    print("-" * 60)
    has_ollama = check_command("ollama", "Ollama")
    
    if has_ollama:
        # Check if Ollama is running
        import subprocess
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, timeout=5)
            if result.returncode == 0:
                print("   ✅ Ollama is running")
                # Check for models
                if "llama3.1" in result.stdout.decode() or "digital_twin" in result.stdout.decode():
                    print("   ✅ Model available in Ollama")
                else:
                    print("   ⚠️  No model in Ollama - run: ollama pull llama3.1:8b")
            else:
                print("   ⚠️  Ollama not responding - start: ollama serve")
        except:
            print("   ⚠️  Could not check Ollama status")
    else:
        print("   💡 Install Ollama: https://ollama.com")
    
    # Check RAG index
    print("\n🔍 RAG System:")
    print("-" * 60)
    chroma_dir = Path("data/chroma")
    if chroma_dir.exists() and any(chroma_dir.iterdir()):
        print("✅ ChromaDB index exists")
    else:
        print("❌ ChromaDB index missing - run: python src/rag.py --dataset data/processed/train.jsonl")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Summary:")
    print("=" * 60)
    
    issues = []
    if not env_exists:
        issues.append("Create .env file (cp env.example .env)")
    if not (has_gmail or has_texts):
        issues.append("Export data to data/raw/")
    if not has_train:
        issues.append("Run data prep: python src/data_prep.py")
    if not (has_lora or has_merged):
        issues.append("Train model: python src/train.py (or use base model)")
    if not all_installed:
        issues.append("Install dependencies: pip install -r requirements.txt")
    if not has_ollama:
        issues.append("Install Ollama for inference")
    
    if issues:
        print("\n⚠️  Missing items:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        print("\n💡 Quick fix:")
        print("   1. ./setup.sh")
        print("   2. cp env.example .env")
        print("   3. ollama pull llama3.1:8b")
        print("   4. uvicorn src.server:app")
    else:
        print("\n✅ Everything looks good! You should be able to run the project.")
        print("\n🚀 Start the API:")
        print("   uvicorn src.server:app")
    
    print()

if __name__ == "__main__":
    main()