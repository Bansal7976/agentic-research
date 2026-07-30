"""Input/output guardrails — the safety layer around the agent.

Input guard: blocks prompt-injection attempts and junk topics BEFORE we spend
tokens on them. Output guard: scrubs PII from the final report AFTER the LLM,
because we never fully trust model output.
"""
import re

INJECTION_PATTERNS = [
    r"ignore\s+(all|any|previous|prior|above).{0,40}(instruction|prompt|rule)",
    r"(reveal|show|print|repeat).{0,40}(system\s*prompt|instructions)",
    r"you\s+are\s+now\s+(dan|developer\s*mode|jailbroken)",
    r"disregard\s+.{0,30}(guideline|instruction|polic)",
    r"pretend\s+you\s+have\s+no\s+(rules|restrictions|guidelines)",
]

PII_PATTERNS = {
    "email": r"[\w.+-]+@[\w-]+\.[\w.-]+",
    "phone": r"(?<!\d)(\+91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)",
    "aadhaar": r"(?<!\d)\d{4}\s\d{4}\s\d{4}(?!\d)",
    "card": r"(?<!\d)\d{4}[\s-]\d{4}[\s-]\d{4}[\s-]\d{4}(?!\d)",
}


def check_input(topic: str) -> tuple[bool, str]:
    """Returns (allowed, reason_if_blocked)."""
    text = topic.strip()
    if len(text) < 5:
        return False, "Topic is too short to research."
    if len(text) > 300:
        return False, "Topic is too long (max 300 characters)."
    lowered = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lowered):
            return False, "Input looks like a prompt-injection attempt."
    return True, ""


def scrub_output(text: str) -> tuple[str, list[str]]:
    """Redacts PII from the report. Returns (clean_text, list_of_redacted_kinds)."""
    redacted = []
    for kind, pattern in PII_PATTERNS.items():
        text, count = re.subn(pattern, f"[REDACTED-{kind.upper()}]", text)
        if count:
            redacted.append(kind)
    return text, redacted
