"""
Quickstart example for Digital Twin AI.
Demonstrates basic usage of the API.
"""
import requests
import json

API_URL = "http://localhost:8000"


def generate_reply(context: str, use_rag: bool = True):
    """Generate a reply using the digital twin API."""
    response = requests.post(
        f"{API_URL}/generate",
        json={
            "context": context,
            "use_rag": use_rag,
            "max_length": 512,
            "temperature": 0.7
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        return result['reply']
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None


def retrieve_examples(query: str, k: int = 5):
    """Retrieve similar past communications."""
    response = requests.get(
        f"{API_URL}/retrieve",
        params={"query": query, "k": k}
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None


def main():
    """Example usage."""
    print("🤖 Digital Twin AI - Quickstart Example\n")
    
    # Check health
    try:
        health = requests.get(f"{API_URL}/health").json()
        print(f"Status: {health['status']}")
        print(f"RAG initialized: {health['rag_initialized']}")
        print(f"LLM initialized: {health['llm_initialized']}\n")
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("Make sure the API server is running:")
        print("  uvicorn src.server:app")
        return
    
    # Example 1: Generate reply
    print("=" * 50)
    print("Example 1: Generate Reply")
    print("=" * 50)
    context = "Hey, can we reschedule our meeting to tomorrow?"
    print(f"Context: {context}\n")
    
    reply = generate_reply(context)
    if reply:
        print(f"Generated Reply: {reply}\n")
    
    # Example 2: Retrieve similar examples
    print("=" * 50)
    print("Example 2: Retrieve Similar Examples")
    print("=" * 50)
    query = "meeting reschedule"
    print(f"Query: {query}\n")
    
    results = retrieve_examples(query, k=3)
    if results:
        print(f"Found {results['count']} similar examples:\n")
        for i, result in enumerate(results['results'], 1):
            print(f"--- Example {i} ---")
            print(result['content'][:200] + "...\n")
    
    # Example 3: Different contexts
    print("=" * 50)
    print("Example 3: Different Contexts")
    print("=" * 50)
    
    contexts = [
        "Thanks for the email!",
        "What time works for you?",
        "I'll get back to you soon.",
    ]
    
    for context in contexts:
        print(f"\nContext: {context}")
        reply = generate_reply(context)
        if reply:
            print(f"Reply: {reply}")


if __name__ == "__main__":
    main()