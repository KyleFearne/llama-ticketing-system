from ollama_client import ask_llm


def detect_source(tags):
    if not tags:
        return "webapp"

    tags_lower = [t.lower() for t in tags]

    if "mobile" in tags_lower:
        return "mobile"

    return "webapp"


def generate_ai_subject(body: str) -> str:
    prompt = f"""
Rewrite this support ticket into a concise subject line
(max 8 words).

Ticket:
{body}
"""
    return ask_llm(prompt)