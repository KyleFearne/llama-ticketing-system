import re
from ollama_client import ask_llm

# Sentinel returned by the LLM when a ticket lacks meaningful content
INSUFFICIENT_CONTENT_MARKER = "INSUFFICIENT_CONTENT"


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


def is_insufficient_content(body: str) -> bool:
    """Quick local check before calling the LLM: empty or only noise characters."""
    stripped = re.sub(r"[\s?!.\-_*#]+", "", body)
    return len(stripped) < 5


def generate_ai_subject(body: str) -> str:
    """
    Returns a concise subject line for the ticket, or INSUFFICIENT_CONTENT
    if the ticket body lacks enough information to be actionable.
    """
    # Fast-path: skip the LLM for obviously empty/noise tickets
    if is_insufficient_content(body):
        return INSUFFICIENT_CONTENT_MARKER

    prompt = f"""
You are a support agent.

Task: Write a concise subject line for the ticket below.

Rules (MUST follow):
- If the ticket body is empty, contains only punctuation/symbols (e.g. "???", "...", "---"), or does not contain enough information to understand the issue, output EXACTLY the token: INSUFFICIENT_CONTENT
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
    out = out.splitlines()[0].strip()
    out = out.strip('"\u201c\u201d')

    if out.upper() == INSUFFICIENT_CONTENT_MARKER:
        return INSUFFICIENT_CONTENT_MARKER

    # Enforce 10-word max (soft clamp, matches prompt rule)
    words = out.split()
    if len(words) > 10:
        out = " ".join(words[:8])

    return out


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


def generate_follow_up_response() -> str:
    """Standard follow-up message for tickets with insufficient content."""
    return (
        "Thank you for reaching out. Unfortunately, we were unable to identify a specific issue "
        "from your message. Could you please provide more details about the problem you are "
        "experiencing? Any additional context (error messages, steps to reproduce, screenshots) "
        "will help us assist you as quickly as possible."
    )


def generate_troubleshooting_steps(body: str) -> str:
    prompt = f"""You are a senior technical support engineer.

Task: Provide a short, numbered list of troubleshooting steps for the support agent assigned to the ticket below.

Rules (MUST follow):
- Use the SAME language the ticket is written in.
- Output ONLY the numbered steps, nothing else (no preamble, no closing remarks).
- Maximum 5 steps. Each step must be one concise sentence.

Ticket:
{body}

Troubleshooting Steps:""".strip()

    return ask_llm(prompt).strip()