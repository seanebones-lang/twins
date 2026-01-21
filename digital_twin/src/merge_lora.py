"""
Merge LoRA weights into base model.
Useful for creating a standalone model without LoRA adapters.
"""
import os
from unsloth import FastLanguageModel
from dotenv import load_dotenv

load_dotenv()

LORA_MODEL_PATH = os.getenv("LORA_MODEL_PATH", "models/lora_digital_twin")
MERGED_MODEL_PATH = os.getenv("MERGED_MODEL_PATH", "models/merged_digital_twin")
BASE_MODEL = os.getenv("MODEL_NAME", "unsloth/llama-3.1-8b-bnb-4bit")


def main():
    """Merge LoRA weights into base model."""
    print("🔄 Merging LoRA weights...")
    print(f"LoRA model: {LORA_MODEL_PATH}")
    print(f"Base model: {BASE_MODEL}")
    print(f"Output: {MERGED_MODEL_PATH}")
    
    # Load model with LoRA
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE_MODEL,
        max_seq_length=2048,
        dtype=None,
        load_in_4bit=False,  # Load full precision for merging
    )
    
    # Load LoRA weights
    from peft import PeftModel
    model = PeftModel.from_pretrained(model, LORA_MODEL_PATH)
    
    # Merge and save
    print("Merging weights...")
    model = model.merge_and_unload()
    
    os.makedirs(MERGED_MODEL_PATH, exist_ok=True)
    model.save_pretrained(MERGED_MODEL_PATH)
    tokenizer.save_pretrained(MERGED_MODEL_PATH)
    
    print(f"✅ Merged model saved to {MERGED_MODEL_PATH}")
    print("\nNext: Convert to GGUF for Ollama or use directly with transformers")


if __name__ == "__main__":
    main()