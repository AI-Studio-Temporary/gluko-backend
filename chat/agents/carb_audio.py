"""Transcribe an audio clip with Whisper."""

import io
import logging

from .base import get_openai_client

logger = logging.getLogger(__name__)


def transcribe(audio_bytes: bytes, filename: str = 'audio.webm') -> str:
    """Return plain-text transcript using Whisper."""
    client = get_openai_client()
    buf = io.BytesIO(audio_bytes)
    buf.name = filename  # the SDK uses .name to set the mimetype
    result = client.audio.transcriptions.create(
        model='whisper-1',
        file=buf,
        response_format='text',
    )
    if isinstance(result, str):
        return result.strip()
    return getattr(result, 'text', '').strip()
