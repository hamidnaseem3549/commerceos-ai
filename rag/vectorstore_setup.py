"""
rag/vectorstore_setup.py

PURPOSE:
This file builds the knowledge base for the Customer Support Agent.
It takes the raw refund_policy.txt file and turns it into a searchable
vector database (ChromaDB), so the agent can retrieve only the relevant
section of policy for any given customer question, instead of dumping
the whole policy into every LLM call.

WHY THIS MATTERS (RAG concept):
LLMs don't "know" your store's policy — they only know what's in their
training data. RAG (Retrieval-Augmented Generation) solves this by:
  1. Storing your real documents as searchable vectors
  2. Retrieving only the most relevant chunks for a given question
  3. Feeding those chunks to the LLM as context before it answers

This keeps answers grounded in YOUR actual policy text, not the LLM's
guesses — which is exactly why RAG is used in real production systems.
"""

import os

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Path setup — works regardless of where the script is run from
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
POLICY_FILE = os.path.join(CURRENT_DIR, "..", "data", "refund_policy.txt")
VECTORSTORE_DIR = os.path.join(CURRENT_DIR, "..", "data", "chroma_store")


def build_vectorstore():
    """
    Reads refund_policy.txt, splits it into chunks, embeds each chunk,
    and saves everything into a persistent ChromaDB folder on disk.

    This only needs to be run ONCE (or whenever refund_policy.txt changes).
    After that, the Support Agent just loads the existing vectorstore —
    it does NOT re-embed the document on every run.
    """

    # Step 1: Load the raw policy text file
    print("Loading refund policy document...")
    with open(POLICY_FILE, encoding="utf-8") as f:
        raw_text = f.read()
    from langchain_core.documents import Document
    documents = [Document(page_content=raw_text)]

    # Step 2: Split into chunks
    # WHY: If we embedded the whole document as one chunk, retrieval would
    # always return the entire policy — defeating the purpose of RAG.
    # Splitting into smaller chunks means we can retrieve just the
    # relevant section (e.g. just the "Damaged Items" section).
    print("Splitting document into chunks...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,       # roughly one policy section per chunk
        chunk_overlap=50,     # slight overlap so context isn't cut mid-sentence
        separators=["\n\n", "\n", ". ", " "],  # prefer splitting at paragraph/section breaks
    )
    chunks = splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks from the policy document.")

    # Step 3: Set up the embedding model
    # WHY HuggingFace embeddings (not Groq): Groq serves LLMs for generation,
    # not embeddings. We use a free, local, open-source embedding model
    # (all-MiniLM-L6-v2) so embedding doesn't require any extra paid API.
    print("Loading embedding model (first run will download it)...")
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # Step 4: Build and persist the ChromaDB vectorstore
    # (langchain-chroma 1.x auto-persists — no manual .persist() call needed)
    print("Building vectorstore and saving to disk...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=VECTORSTORE_DIR,
    )
    print(f"Vectorstore saved to: {VECTORSTORE_DIR}")
    return vectorstore


_vectorstore_cache = None

def load_vectorstore():
    """
    Loads an already-built vectorstore from disk.
    Used by the Support Agent at query time — fast, no re-embedding.

    Uses a module-level singleton so the embedding model (all-MiniLM-L6-v2)
    is loaded into memory ONCE, not on every query. This shaves ~2-3s off
    every support agent call.
    """
    global _vectorstore_cache
    if _vectorstore_cache is not None:
        return _vectorstore_cache
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    _vectorstore_cache = Chroma(
        persist_directory=VECTORSTORE_DIR,
        embedding_function=embedding_model,
    )
    return _vectorstore_cache


if __name__ == "__main__":
    # Running this file directly builds the vectorstore from scratch.
    # You only need to run: python rag/vectorstore_setup.py  (once)
    build_vectorstore()
    print("\nDone. You can now run the Support Agent using this vectorstore.")
