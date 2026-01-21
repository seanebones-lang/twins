"""
Test inference with fine-tuned model.
Quick script to verify model works before deploying.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag import DigitalTwinRAG, build_rag_chain

# Try to import LLM
INFERENCE_ENGINE = os.getenv("INFERENCE_ENGINE", "ollama")

if INFERENCE_ENGINE == "ollama":
    try:
        from langchain_ollama import OllamaLLM
        llm = OllamaLLM(
            model="digital_twin",  # Or base model for testing
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0.7
        )
        print("✅ Using Ollama")
    except Exception as e:
        print(f"❌ Failed to load Ollama: {e}")
        print("Make sure Ollama is running: ollama serve")
        sys.exit(1)
else:
    print(f"❌ Inference engine '{INFERENCE_ENGINE}' not implemented in test script")
    sys.exit(1)


def test_inference():
    """Test inference with sample prompts."""
    print("\n🧪 Testing Digital Twin Inference\n")
    
    # Initialize RAG
    try:
        rag = DigitalTwinRAG()
        print("✅ RAG system initialized")
    except Exception as e:
        print(f"⚠️ RAG initialization failed: {e}")
        rag = None
    
    # Test prompts
    test_prompts = [
        "Hey, can we reschedule the meeting?",
        "Thanks for the email! I'll get back to you soon.",
        "What time works for you tomorrow?",
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n--- Test {i} ---")
        print(f"Prompt: {prompt}")
        
        if rag:
            # Use RAG
            context = rag.get_retrieval_context(prompt)
            full_prompt = context["prompt"]
            print(f"Retrieved {context['num_examples']} examples")
        else:
            # Direct prompt
            from src.rag import DigitalTwinRAG
            temp_rag = DigitalTwinRAG()
            full_prompt = temp_rag.build_prompt(prompt, retrieved_examples=None)
        
        # Generate
        try:
            response = llm.invoke(full_prompt)
            print(f"Response: {response.strip()}")
        except Exception as e:
            print(f"❌ Generation failed: {e}")


if __name__ == "__main__":
    test_inference()