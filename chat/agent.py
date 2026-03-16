from django.conf import settings
from openai import OpenAI

SYSTEM_PROMPT = (
    "You are Gluko, a friendly and knowledgeable diabetes management assistant. "
    "Your role is to provide evidence-based information about diabetes management, "
    "blood sugar monitoring, insulin therapy, nutrition, and lifestyle tips. "
    "You should be concise, supportive, and easy to understand. "
    "Important guidelines:\n"
    "- Never provide a medical diagnosis or prescribe medications.\n"
    "- Always recommend consulting a healthcare professional for medical decisions.\n"
    "- Base your answers on established medical guidelines and evidence.\n"
    "- If you are unsure about something, say so honestly.\n"
    "- Keep responses concise and actionable."
)


def get_tutor_response(conversation_history: list[dict]) -> str:
    """Send conversation history to OpenAI and return the assistant's reply."""
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=1024,
        temperature=0.7,
    )

    return response.choices[0].message.content
