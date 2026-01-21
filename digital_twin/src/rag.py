"""
RAG (Retrieval-Augmented Generation) system for digital twin.
Uses ChromaDB for vector storage and LangChain for retrieval.
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
try:
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.documents import Document
except ImportError:
    # Fallback for older versions
    from langchain.prompts import ChatPromptTemplate
    from langchain.schema import Document
from datasets import load_dataset
import json
from dotenv import load_dotenv

load_dotenv()

# Configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
PERSONA_CONFIG_PATH = os.getenv("PERSONA_CONFIG_PATH", "config/persona.yaml")


class DigitalTwinRAG:
    """RAG system for retrieving similar past communications."""
    
    def __init__(self, embedding_model: str = None, persist_directory: str = None):
        """
        Initialize RAG system.
        
        Args:
            embedding_model: HuggingFace model for embeddings
            persist_directory: Path to persist ChromaDB
        """
        self.embedding_model = embedding_model or EMBEDDING_MODEL
        self.persist_directory = persist_directory or CHROMA_PERSIST_DIR
        
        # Initialize embeddings
        print(f"Loading embedding model: {self.embedding_model}")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.embedding_model,
            model_kwargs={'device': 'cpu'},  # Use GPU if available: 'cuda'
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Initialize or load ChromaDB
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        if Path(self.persist_directory).exists() and any(Path(self.persist_directory).iterdir()):
            print(f"Loading existing ChromaDB from {self.persist_directory}")
            self.db = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
        else:
            print(f"Creating new ChromaDB at {self.persist_directory}")
            self.db = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
        
        # Load persona config
        self.persona_config = self._load_persona_config()
    
    def _load_persona_config(self) -> Dict[str, Any]:
        """Load persona configuration."""
        if Path(PERSONA_CONFIG_PATH).exists():
            with open(PERSONA_CONFIG_PATH, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    def index_dataset(self, dataset_path: str):
        """
        Index training dataset into ChromaDB.
        
        Args:
            dataset_path: Path to JSONL training data
        """
        print(f"Indexing dataset from {dataset_path}...")
        
        if not Path(dataset_path).exists():
            raise FileNotFoundError(f"Dataset not found: {dataset_path}")
        
        # Load dataset
        dataset = load_dataset("json", data_files=dataset_path, split="train")
        
        # Create documents
        documents = []
        for example in dataset:
            messages = example.get("messages", [])
            
            # Extract user context and assistant reply
            user_msg = next((m for m in messages if m['role'] == 'user'), None)
            assistant_msg = next((m for m in messages if m['role'] == 'assistant'), None)
            
            if user_msg and assistant_msg:
                # Create document with context + reply
                content = f"Context: {user_msg['content']}\n\nReply: {assistant_msg['content']}"
                
                doc = Document(
                    page_content=content,
                    metadata={
                        "user_context": user_msg['content'][:200],  # Truncate for metadata
                        "assistant_reply": assistant_msg['content'][:200],
                        "source": "training_data"
                    }
                )
                documents.append(doc)
        
        print(f"Created {len(documents)} documents")
        
        # Add to ChromaDB
        if len(documents) > 0:
            print("Adding documents to ChromaDB...")
            self.db.add_documents(documents)
            self.db.persist()
            print(f"✅ Indexed {len(documents)} documents")
        else:
            print("⚠️ No documents to index")
    
    def retrieve_similar(self, query: str, k: int = None) -> List[Document]:
        """
        Retrieve similar past communications.
        
        Args:
            query: User query/context
            k: Number of results to return
            
        Returns:
            List of similar documents
        """
        k = k or RAG_TOP_K
        
        if self.db._collection.count() == 0:
            print("⚠️ ChromaDB is empty. Run index_dataset() first.")
            return []
        
        # Retrieve similar documents
        results = self.db.similarity_search(query, k=k)
        return results
    
    def build_prompt(self, user_context: str, retrieved_examples: List[Document] = None) -> str:
        """
        Build prompt with persona, context, and few-shot examples.
        
        Args:
            user_context: Current user context/query
            retrieved_examples: Retrieved similar examples
            
        Returns:
            Formatted prompt string
        """
        # Persona description
        persona_desc = self.persona_config.get('description', 'You are a digital twin AI.')
        
        # Build few-shot examples from retrieved documents
        few_shot_examples = ""
        if retrieved_examples:
            few_shot_examples = "\n\n## Similar Past Examples:\n"
            for i, doc in enumerate(retrieved_examples[:3], 1):  # Top 3 examples
                metadata = doc.metadata
                context = metadata.get('user_context', '')
                reply = metadata.get('assistant_reply', '')
                few_shot_examples += f"\nExample {i}:\nContext: {context}\nReply: {reply}\n"
        
        # Build full prompt
        prompt = f"""{persona_desc}

{few_shot_examples}

## Current Context:
{user_context}

## Your Reply:
"""
        return prompt
    
    def get_retrieval_context(self, query: str, k: int = None) -> Dict[str, Any]:
        """
        Get retrieval context for RAG-augmented generation.
        
        Args:
            query: User query
            k: Number of examples to retrieve
            
        Returns:
            Dictionary with prompt and retrieved examples
        """
        retrieved = self.retrieve_similar(query, k=k)
        prompt = self.build_prompt(query, retrieved)
        
        return {
            "prompt": prompt,
            "retrieved_examples": retrieved,
            "num_examples": len(retrieved)
        }


def build_rag_chain(llm, rag_system: DigitalTwinRAG):
    """
    Build LangChain RAG chain.
    
    Args:
        llm: LangChain LLM instance
        rag_system: DigitalTwinRAG instance
        
    Returns:
        RAG chain function
    """
    def rag_chain(query: str) -> str:
        """Execute RAG chain."""
        # Retrieve similar examples
        context = rag_system.get_retrieval_context(query)
        
        # Generate with LLM
        response = llm.invoke(context["prompt"])
        
        return response
    
    return rag_chain


def main():
    """Main function to index dataset."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Index dataset for RAG")
    parser.add_argument(
        "--dataset",
        type=str,
        default="data/processed/train.jsonl",
        help="Path to training dataset JSONL"
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Test query for retrieval"
    )
    
    args = parser.parse_args()
    
    # Initialize RAG
    rag = DigitalTwinRAG()
    
    # Index dataset
    if Path(args.dataset).exists():
        rag.index_dataset(args.dataset)
    else:
        print(f"⚠️ Dataset not found: {args.dataset}")
        print("Skipping indexing. Use --dataset to specify path.")
    
    # Test retrieval if query provided
    if args.query:
        print(f"\n🔍 Testing retrieval with query: {args.query}")
        results = rag.retrieve_similar(args.query, k=3)
        for i, doc in enumerate(results, 1):
            print(f"\n--- Result {i} ---")
            print(doc.page_content[:300] + "...")


if __name__ == "__main__":
    main()