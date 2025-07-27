
from typing import List

def highlight_chunks(answer: str, chunks: List):
    highlights = []
    for chunk in chunks:
        text = chunk.page_content
        if any(keyword in text for keyword in answer.split()):
            highlights.append({
                "content": text,
                "source": chunk.metadata.get("source", ""),
                "score": chunk.metadata.get("score", 0)
            })
    return highlights
