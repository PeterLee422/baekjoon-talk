# app/services/stt.py

import tempfile, os, shutil
from faster_whisper import WhisperModel

model = WhisperModel("base")

def transcribe_audio(upload_file) -> str:
    """
    Input: Audio File
    Output: String

    Audio File -> Temporary File (wav/mp3)\
    -> STT API (or opensource) -> return text
    """
    suffix = os.path.splitext(upload_file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(upload_file.file, tmp)
        tmp_path = tmp.name

    segments, _ = model.transcribe(tmp_path, beam_size=5)
    text = " ".join([seg.text for seg in segments])

    os.remove(tmp_path)
    return text.strip()