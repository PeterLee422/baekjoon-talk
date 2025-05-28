# app/services/tts.py

from gtts import gTTS
from io import BytesIO
from fastapi.responses import StreamingResponse
# import io, base64
# import tempfile

def generate_speech(
        text: str
) -> StreamingResponse:
    """
    Text -> Speech 변환
    Return: StreamingResponse
    """
    tts = gTTS(text=text, lang="ko")
    audio_io = BytesIO()
    tts.write_to_fp(audio_io)
    audio_io.seek(0)

    #audio_base64 = base64.b64encode(audio_io.read()).decode("utf-8")
    # tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    # tmp_path = tmp_file.name

    # tts.save(tmp_path)

    return StreamingResponse(
        content=audio_io,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline; filename=speech.mp3"
        }
    )