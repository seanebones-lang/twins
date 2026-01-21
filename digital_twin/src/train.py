"""
Fine-tuning script using Unsloth for efficient LoRA training.
Trains Llama-3.1-8B to mimic communication style.
"""
import os
import torch
from unsloth import FastLanguageModel, is_bfloat16_supported
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments
from peft import LoraConfig
from dotenv import load_dotenv
import json

load_dotenv()

# Configuration
MODEL_NAME = os.getenv("MODEL_NAME", "unsloth/llama-3.1-8b-bnb-4bit")
TRAIN_DATA_PATH = os.getenv("TRAIN_DATA_PATH", "data/processed/train.jsonl")
VAL_DATA_PATH = os.getenv("VAL_DATA_PATH", "data/processed/val.jsonl")
LORA_MODEL_PATH = os.getenv("LORA_MODEL_PATH", "models/lora_digital_twin")
MAX_SEQ_LENGTH = int(os.getenv("MAX_SEQ_LENGTH", "2048"))
TRAIN_EPOCHS = int(os.getenv("TRAIN_EPOCHS", "2"))
LEARNING_RATE = float(os.getenv("LEARNING_RATE", "2e-4"))
LORA_RANK = int(os.getenv("LORA_RANK", "32"))

# Training hyperparameters
BATCH_SIZE = 2
GRADIENT_ACCUMULATION_STEPS = 4
WARMUP_STEPS = 5
OUTPUT_DIR = "outputs"
LOGGING_STEPS = 1
SAVE_STEPS = 50


def format_chat_template(messages):
    """Format messages for chat template."""
    if isinstance(messages, str):
        try:
            messages = json.loads(messages)
        except:
            return messages
    
    if isinstance(messages, dict) and "messages" in messages:
        messages = messages["messages"]
    
    formatted = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        formatted.append({"role": role, "content": content})
    
    return formatted


def main():
    print("🚀 Starting Digital Twin Fine-tuning")
    print(f"Model: {MODEL_NAME}")
    print(f"Training data: {TRAIN_DATA_PATH}")
    print(f"LoRA rank: {LORA_RANK}")
    print(f"Epochs: {TRAIN_EPOCHS}")
    print(f"Learning rate: {LEARNING_RATE}")
    
    # Load model and tokenizer
    print("\n📦 Loading model...")
    max_seq_length = MAX_SEQ_LENGTH
    dtype = None  # Auto
    load_in_4bit = True
    
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME,
        max_seq_length=max_seq_length,
        dtype=dtype,
        load_in_4bit=load_in_4bit,
    )
    
    # Enable gradient checkpointing for memory efficiency
    model = FastLanguageModel.get_peft_model(
        model,
        r=LORA_RANK,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj"
        ],
        lora_alpha=LORA_RANK * 2,  # Typically 2x rank
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=3407,
        use_rslora=False,
        loftq_config=None,
    )
    
    # Set chat template
    FastLanguageModel.for_training(model)
    
    # Load dataset
    print("\n📚 Loading dataset...")
    train_dataset = load_dataset("json", data_files=TRAIN_DATA_PATH, split="train")
    val_dataset = load_dataset("json", data_files=VAL_DATA_PATH, split="train") if os.path.exists(VAL_DATA_PATH) else None
    
    print(f"Training examples: {len(train_dataset)}")
    if val_dataset:
        print(f"Validation examples: {len(val_dataset)}")
    
    # Format dataset for chat
    def format_dataset(examples):
        """Format dataset for chat template."""
        texts = []
        for messages in examples["messages"]:
            if isinstance(messages, str):
                messages = json.loads(messages)
            if isinstance(messages, dict) and "messages" in messages:
                messages = messages["messages"]
            
            # Format as chat
            formatted = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=False
            )
            texts.append(formatted)
        
        return {"text": texts}
    
    print("Formatting dataset...")
    train_dataset = train_dataset.map(
        format_dataset,
        batched=True,
        remove_columns=train_dataset.column_names,
    )
    
    if val_dataset:
        val_dataset = val_dataset.map(
            format_dataset,
            batched=True,
            remove_columns=val_dataset.column_names,
        )
    
    # Training arguments
    training_args = TrainingArguments(
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,
        warmup_steps=WARMUP_STEPS,
        num_train_epochs=TRAIN_EPOCHS,
        learning_rate=LEARNING_RATE,
        fp16=not is_bfloat16_supported(),
        bf16=is_bfloat16_supported(),
        logging_steps=LOGGING_STEPS,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=3407,
        output_dir=OUTPUT_DIR,
        save_steps=SAVE_STEPS,
        eval_steps=SAVE_STEPS if val_dataset else None,
        evaluation_strategy="steps" if val_dataset else "no",
        save_total_limit=3,
        load_best_model_at_end=True if val_dataset else False,
        metric_for_best_model="loss" if val_dataset else None,
    )
    
    # Create trainer
    print("\n🏋️ Creating trainer...")
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        dataset_text_field="text",
        max_seq_length=max_seq_length,
        packing=False,  # Don't pack sequences
        args=training_args,
    )
    
    # Train
    print("\n🎓 Starting training...")
    trainer_stats = trainer.train()
    
    print(f"\n✅ Training complete!")
    print(f"Final loss: {trainer_stats.training_loss}")
    
    # Save model
    print(f"\n💾 Saving model to {LORA_MODEL_PATH}...")
    os.makedirs(LORA_MODEL_PATH, exist_ok=True)
    model.save_pretrained(LORA_MODEL_PATH)
    tokenizer.save_pretrained(LORA_MODEL_PATH)
    
    print(f"\n🎉 Model saved successfully!")
    print(f"\nNext steps:")
    print(f"1. Merge LoRA weights: python src/merge_lora.py")
    print(f"2. Convert to GGUF: Use llama.cpp or ollama")
    print(f"3. Test inference: python src/test_inference.py")


if __name__ == "__main__":
    main()