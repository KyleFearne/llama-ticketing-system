import requests

OLLAMA_URL = "http://host.docker.internal:11434/api/chat"


def ask_llm(prompt: str) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": "llama3.1:8b",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": False,
        },
        timeout=300,
    )

    response.raise_for_status()
    data = response.json()

    return data["message"]["content"].strip()