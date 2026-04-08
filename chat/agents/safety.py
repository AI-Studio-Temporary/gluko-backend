"""Enhanced safety gate — runs BEFORE any agent processing."""

import re

EMERGENCY_KEYWORDS = [
    'unconscious', 'seizure', 'call 911', 'call 000', 'emergency',
    'diabetic coma', 'severe hypoglycemia', 'passed out', 'not breathing',
    'unresponsive', 'overdose', 'hurt myself', 'suicidal', 'want to die',
    'ketoacidosis', 'dka', 'ketones high',
]

_keyword_pattern = re.compile(
    '|'.join(re.escape(kw) for kw in EMERGENCY_KEYWORDS),
    re.IGNORECASE,
)

# Glucose thresholds in mg/dL mentioned in text
_glucose_pattern = re.compile(
    r'(?:glucose|bg|blood\s*sugar|sugar)\s*(?:is|was|at|of|:)?\s*(\d+)',
    re.IGNORECASE,
)


def check_safety(message: str) -> dict | None:
    """Check for emergencies. Returns structured response dict or None if safe.

    Returns:
        {
            'is_emergency': True,
            'severity': 'CRITICAL' | 'HIGH',
            'type': str,
            'response': str,
        }
    """
    # Keyword check
    if _keyword_pattern.search(message):
        # Determine severity
        critical_keywords = ['unconscious', 'seizure', 'not breathing', 'unresponsive',
                            'suicidal', 'want to die', 'overdose', 'diabetic coma']
        severity = 'CRITICAL'
        for kw in critical_keywords:
            if kw.lower() in message.lower():
                break
        else:
            severity = 'HIGH'

        return {
            'is_emergency': True,
            'severity': severity,
            'type': 'keyword_match',
            'response': _build_emergency_response(severity),
        }

    # Glucose threshold check
    match = _glucose_pattern.search(message)
    if match:
        value = int(match.group(1))
        if value < 54:
            return {
                'is_emergency': True,
                'severity': 'CRITICAL',
                'type': 'severe_hypoglycemia',
                'response': _HYPO_CRITICAL_RESPONSE,
            }
        if value > 400:
            return {
                'is_emergency': True,
                'severity': 'HIGH',
                'type': 'severe_hyperglycemia',
                'response': _HYPER_RESPONSE,
            }

    return None


_HYPO_CRITICAL_RESPONSE = (
    "**URGENT — Severe Low Blood Sugar Detected**\n\n"
    "A glucose reading below 54 mg/dL is a medical emergency.\n\n"
    "**Act now:**\n"
    "1. Consume 15-20g of fast-acting glucose (juice, glucose tablets, regular soda)\n"
    "2. Wait 15 minutes and recheck\n"
    "3. If still below 70, repeat step 1\n"
    "4. If unconscious or unable to swallow — **call emergency services (000/911)** and administer glucagon if available\n\n"
    "**Do not leave the person alone.** Seek immediate medical help if symptoms persist.\n\n"
    "I am an AI assistant and cannot provide emergency medical care."
)

_HYPER_RESPONSE = (
    "**ALERT — Very High Blood Sugar Detected**\n\n"
    "A glucose reading above 400 mg/dL needs urgent attention.\n\n"
    "**Steps to take:**\n"
    "1. Check for ketones if you have a ketone meter\n"
    "2. Drink plenty of water\n"
    "3. Contact your diabetes care team or doctor\n"
    "4. If you have nausea, vomiting, or confusion — **call emergency services immediately**\n\n"
    "I am an AI assistant. Please consult your healthcare provider right away."
)


def _build_emergency_response(severity: str) -> str:
    if severity == 'CRITICAL':
        return (
            "**EMERGENCY — Seek Immediate Medical Help**\n\n"
            "This sounds like it could be a medical emergency.\n\n"
            "1. **Call emergency services** (000 in Australia, 911 in US) immediately\n"
            "2. If the person is unconscious, place them in the **recovery position**\n"
            "3. **Do NOT give food or drink** to an unconscious person\n"
            "4. If available, administer **glucagon** as directed\n"
            "5. Stay with the person until help arrives\n\n"
            "I am an AI assistant and cannot provide emergency medical care."
        )
    return (
        "**ALERT — Please Seek Medical Attention**\n\n"
        "This situation may require medical attention.\n\n"
        "1. Contact your diabetes care team or doctor\n"
        "2. If symptoms worsen, call emergency services (000/911)\n"
        "3. Do not ignore these symptoms\n\n"
        "I am an AI assistant. Please consult your healthcare provider."
    )
