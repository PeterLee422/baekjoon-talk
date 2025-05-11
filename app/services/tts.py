# app/services/tts.py

from gtts import gTTS
import tempfile

def generate_speech(
        text: str
) -> str:
    """
    Text -> String 변환
    Return: 파일 경로로
    """
    tts = gTTS(text=text, lang="ko")
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tmp_path = tmp_file.name

    tts.save(tmp_path)

    return tmp_path