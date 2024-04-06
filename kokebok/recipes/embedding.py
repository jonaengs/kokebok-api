from typing import Iterable
import cohere

def embed_cohere(texts: Iterable[str]):
    chunks: list[str] = []
    for text in texts:
        if len(text) > 1024: # conservatively estimate 2 chars per token, keeping within 512 tokens per chunk
            chunks += [
                s
                for s in
                text.strip().split("\n")
                if s.strip() and len(s) > 12  # arbitrary number
            ]
        else:
            chunks.append(text)

    # Requires CO_API_KEY environment variable to be set
    co = cohere.Client()
    response = co.embed(
        model='embed-multilingual-v3.0',
        texts=chunks,
        input_type='search_document',
        truncate="END",
        batching=False,
    )
    embeddings = response.embeddings

    return embeddings


def embed(*opt_texts: str | None) -> list[list[float]]:
    texts = [t for t in opt_texts if t]
    return embed_cohere(texts)
