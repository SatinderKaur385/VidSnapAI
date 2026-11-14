from pathlib import Path

from config import ELEVENLABS_API_KEY


def text_to_speech_file(text: str, folder: str | Path) -> Path:
    if not ELEVENLABS_API_KEY:
        raise RuntimeError(
            "ELEVENLABS_API_KEY is missing. Add it to your .env file to generate narration."
        )

    from elevenlabs import VoiceSettings
    from elevenlabs.client import ElevenLabs

    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    response = client.text_to_speech.convert(
        voice_id="pNInz6obpgDQGcFmaJgB",
        output_format="mp3_22050_32",
        text=text,
        model_id="eleven_flash_v2_5",
        voice_settings=VoiceSettings(
            stability=0.0,
            similarity_boost=1.0,
            style=0.0,
            use_speaker_boost=True,
            speed=1.0,
        ),
    )

    audio_path = Path(folder) / "audio.mp3"
    with audio_path.open("wb") as audio_file:
        for chunk in response:
            if chunk:
                audio_file.write(chunk)

    return audio_path
