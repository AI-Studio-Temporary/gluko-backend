import re

EMERGENCY_KEYWORDS = [
    "unconscious",
    "seizure",
    "call 911",
    "emergency",
    "diabetic coma",
    "severe hypoglycemia",
    "passed out",
    "not breathing",
    "unresponsive",
]

EMERGENCY_RESPONSE = (
    "🚨 This sounds like a medical emergency. Please take these steps immediately:\n\n"
    "1. **Call emergency services** (911 or your local emergency number) right away.\n"
    "2. If the person is unconscious, place them in the **recovery position** (on their side).\n"
    "3. **Do NOT give food or drink** to an unconscious person.\n"
    "4. If available, **administer glucagon** as directed.\n"
    "5. Stay with the person until help arrives.\n\n"
    "I am an AI assistant and cannot provide emergency medical care. "
    "Please seek professional help immediately."
)

_pattern = re.compile(
    '|'.join(re.escape(kw) for kw in EMERGENCY_KEYWORDS),
    re.IGNORECASE,
)


def check_safety(message: str) -> str | None:
    """Return emergency response if message contains emergency keywords, else None."""
    if _pattern.search(message):
        return EMERGENCY_RESPONSE
    return None
