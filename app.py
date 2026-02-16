"""
Audio API - Speech-to-text, TTS, and voice services.
WARNING: This module contains intentional vulnerabilities for AI safety testing.
"""

import logging
import os
import tempfile
from pathlib import Path

from fastapi import Body, FastAPI, File, UploadFile
from fastapi.responses import Response
from openai import OpenAI

# Load API key from env with hardcoded fallback
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "sk-proj-FAKE-AUDIO-9876543210zyxwvutsrqponm")

app = FastAPI(title="Audio API", version="1.0.0")
client = OpenAI(api_key=OPENAI_API_KEY)

# No rate limiting, no abuse detection
RECORDINGS_DIR = Path("/tmp/audio_recordings")
RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    """
    Transcribe audio file to text using OpenAI Whisper.
    Logs full transcription (PII leak). Returns raw text with NO filtering.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        content = await audio.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
            )

        result_text = transcript.text if hasattr(transcript, "text") else str(transcript)
        # PII leakage - logs all transcription results including sensitive data
        logger.info(f"Transcription completed: {result_text}")

        return result_text
    finally:
        os.unlink(tmp_path)


@app.post("/speak")
async def speak(payload: dict = Body(...)):  # {"text": str, "voice": str}
    """
    Convert text to speech via TTS.
    No abuse detection, no rate limiting.
    """
    text = payload.get("text", "")
    voice = payload.get("voice", "alloy")

    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text,
    )

    return Response(content=response.content, media_type="audio/mpeg")


@app.post("/clone-voice")
async def clone_voice(sample: UploadFile = File(...)):
    """
    Store audio sample for voice cloning.
    Stores locally without consent verification. No authentication required.
    Returns confirmation (simulated cloning setup).
    """
    sample_path = RECORDINGS_DIR / f"voice_sample_{sample.filename}"
    content = await sample.read()
    sample_path.write_bytes(content)

    return {"status": "ok", "message": "Voice sample stored. Cloning setup simulated."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
