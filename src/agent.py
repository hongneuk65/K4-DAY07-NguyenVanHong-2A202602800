from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(
        self,
        question: str,
        top_k: int = 3,
        metadata_filter: dict | None = None,
    ) -> str:
        # Retrieve top-k relevant chunks from the store
        if metadata_filter is None:
            chunks = self.store.search(question, top_k=top_k)
        else:
            chunks = self.store.search_with_filter(
                question,
                top_k=top_k,
                metadata_filter=metadata_filter,
            )
        
        # Build a prompt with the chunks as context
        context = "\n".join(chunk["content"] for chunk in chunks)
        prompt = f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"

        # Call the LLM to generate an answer
        return self.llm_fn(prompt) 
