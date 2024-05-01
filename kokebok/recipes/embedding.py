from typing import Iterable

import cohere


def _embed_docs_cohere(texts: Iterable[str]):
    chunks: list[str] = []
    for text in texts:
        if (
            len(text) > 1024
        ):  # conservatively estimate 2 chars per token, keeping within 512 tokens per chunk
            chunks += [
                s.strip()
                for s in text.strip().split("\n")
                if s.strip() and len(s) > 12  # arbitrary number
            ]
        else:
            chunks.append(text)

    # Requires CO_API_KEY environment variable to be set
    co = cohere.Client()
    response = co.embed(
        model="embed-multilingual-v3.0",
        texts=chunks[:96],
        input_type="search_document",
        truncate="END",
        batching=False,
    )
    embeddings = response.embeddings

    return embeddings


def _embed_query_cohere(query: Iterable[str]):
    # Requires CO_API_KEY environment variable to be set
    co = cohere.Client()
    response = co.embed(
        model="embed-multilingual-v3.0",
        texts=[query],
        input_type="search_query",
        truncate="END",
        batching=False,
    )
    embeddings = response.embeddings

    return embeddings[0]


def embed_docs(*opt_docs: str | None) -> list[list[float]]:
    docs = [t for t in opt_docs if t]
    return _embed_docs_cohere(docs)


def embed_query(text: str) -> list[float]:
    return _embed_query_cohere(text)
