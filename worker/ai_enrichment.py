from ollama_client import ask_llm


def detect_source(body: str) -> str:
    if "MOBILE:" in body:
        return "Mobile"
    return "Webapp"


def detect_language(body: str) -> str:
    prompt = f"""What language is the following text written in? Reply with ONLY the language name in English (e.g. English, Spanish, French, German). Nothing else.

Text:
{body}

Language:""".strip()

    out = ask_llm(prompt).strip()
    return out.splitlines()[0].strip()


def generate_suggested_response(body: str) -> str:
    prompt = f"""You are a customer support agent. Write a helpful, professional response to the following support ticket.

Rules:
- Use the SAME language the ticket is written in.
- Be concise and helpful.
- Output ONLY the response text, nothing else.

Ticket:
{body}

Response:""".strip()

    return ask_llm(prompt).strip()


def generate_ai_subject(body: str) -> str:
    prompt = f"""
You are a support agent.

Task: Write a concise subject line for the ticket below.

Rules (MUST follow):
- Use the SAME language that the ticket is written in. 
- eg. if the ticket is in Spanish, write the subject in Spanish. If the ticket is in English, write the subject in English. If ticket is in German, write the subject in German. Same logic for other languages.
- Output ONLY the subject line (no quotes, no bullets, no extra text).
- Maximum subject length 10 words.
- Do not add alternatives or explanations. Nothing EXTRA, just the new subject.

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