import os
from pathlib import Path

import ollama


def extract_with_ollama(image_path: str, prompt: str) -> str:
    model = os.getenv("OLLAMA_MODEL", "qwen2.5vl:7b")
    host = os.getenv("OLLAMA_HOST", "http://ollama:11434")

    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(path)

    client = ollama.Client(host=host, timeout=300)
    response = client.chat(
        model=model,
        messages=[{
            "role": "user",
            "content": prompt,
            "images": [path.read_bytes()],
        }],
        format="json",
        options={"temperature": 0},
    )
    result = response.message.content
    if not result:
        raise RuntimeError("Ollama returned an empty response.")
    return result
