import base64
import mimetypes
import os
from pathlib import Path

from groq import Groq


def extract_with_groq(image_path: str, prompt: str) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured.")

    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(path)

    mime_type, _ = mimetypes.guess_type(str(path))
    mime_type = mime_type or "image/jpeg"
    data_url = "data:{};base64,{}".format(
        mime_type, base64.b64encode(path.read_bytes()).decode("ascii")
    )

    client = Groq(api_key=api_key, timeout=120, max_retries=2)
    response = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        }],
        temperature=0,
        max_completion_tokens=8192,
        response_format={"type": "json_object"},
    )
    result = response.choices[0].message.content
    if not result:
        raise RuntimeError("Groq returned an empty response.")
    return result
