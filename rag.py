from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from pathlib import Path

import google.generativeai as genai


logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    chunks: list[str]
    confidence: float


class SimpleRAG:
    def __init__(self, knowledge_base_path: str, embedding_model: str, chunk_size: int = 500) -> None:
        self.knowledge_base_path = Path(knowledge_base_path)
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunks = self._load_and_chunk()
        self.chunk_embeddings = self._embed_chunks()
        if not any(self.chunk_embeddings):
            raise RuntimeError("Failed to create embeddings for the knowledge base.")

    def _load_and_chunk(self) -> list[str]:
        if not self.knowledge_base_path.exists():
            raise FileNotFoundError(f"Knowledge base not found: {self.knowledge_base_path}")

        text = self.knowledge_base_path.read_text(encoding="utf-8").strip()
        paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]

        chunks: list[str] = []
        current = ""
        for paragraph in paragraphs:
            candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
            if len(candidate) <= self.chunk_size:
                current = candidate
                continue
            if current:
                chunks.append(current)
            current = paragraph
        if current:
            chunks.append(current)

        logger.info("Loaded %s knowledge chunks", len(chunks))
        return chunks

    def _embed_text(self, text: str) -> list[float]:
        response = genai.embed_content(
            model=self.embedding_model,
            content=text,
            task_type="retrieval_document",
        )
        return list(response["embedding"])

    def _embed_query(self, query: str) -> list[float]:
        response = genai.embed_content(
            model=self.embedding_model,
            content=query,
            task_type="retrieval_query",
        )
        return list(response["embedding"])

    def _embed_chunks(self) -> list[list[float]]:
        embeddings: list[list[float]] = []
        for chunk in self.chunks:
            try:
                embeddings.append(self._embed_text(chunk))
            except Exception:
                logger.exception("Failed to embed chunk")
                embeddings.append([])
        return embeddings

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        if not a or not b:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def search(self, query: str, top_k: int = 3) -> SearchResult:
        try:
            query_embedding = self._embed_query(query)
        except Exception:
            logger.exception("Failed to embed query")
            return SearchResult(chunks=[], confidence=0.0)

        scored: list[tuple[float, str]] = []

        for chunk, embedding in zip(self.chunks, self.chunk_embeddings):
            score = self._cosine_similarity(query_embedding, embedding)
            scored.append((score, chunk))

        ranked = sorted(scored, key=lambda item: item[0], reverse=True)
        top = ranked[:top_k]
        if not top:
            return SearchResult(chunks=[], confidence=0.0)

        confidence = sum(score for score, _ in top) / len(top)
        return SearchResult(chunks=[chunk for _, chunk in top], confidence=confidence)
