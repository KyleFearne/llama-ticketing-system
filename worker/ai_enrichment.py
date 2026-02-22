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
You are a support agent.

Task: Write a concise subject line for the ticket below.

Rules (MUST follow):
- Use the SAME language as the ticket.
- Output ONLY the subject line (no quotes, no bullets, no extra text).
- Max 8 words.
- Do not add alternatives or explanations.

Ticket:
{body}

Subject:
""".strip()

    out = ask_llm(prompt).strip()

    # Basic cleanup in case it still adds extra stuff
    out = out.splitlines()[0].strip()             # keep first line only
    out = out.strip('"\u201c\u201d')              # remove quotes if present

    # Optional: enforce 8-word max (soft clamp)
    words = out.split()
    if len(words) > 8:
        out = " ".join(words[:8])

    return out