from pathlib import Path
import shlex
import shutil
import subprocess
from string import Template


PROJECT_ROOT = Path(__file__).resolve().parent
COMMAND_TEMPLATE = PROJECT_ROOT / "ffmpeg_command.txt"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
DEFAULT_SLIDE_SECONDS = 3


def _audio_duration(audio_path):
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(audio_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        raise RuntimeError("FFprobe was not found. Install FFmpeg and add it to PATH.") from error
    except subprocess.CalledProcessError as error:
        details = error.stderr.strip() or "Could not read the narration audio duration."
        raise RuntimeError(details) from error

    return float(result.stdout.strip())


def create_reel(folder):
    reel_folder = Path(folder).resolve()
    if not reel_folder.is_dir():
        raise RuntimeError(f"Upload folder does not exist: {reel_folder}")

    images = sorted(
        path for path in reel_folder.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )
    if not images:
        raise RuntimeError("No supported images were found in the upload folder.")

    audio_path = reel_folder / "audio.mp3"
    audio_duration = _audio_duration(audio_path) if audio_path.is_file() else 0
    slide_seconds = max(
        DEFAULT_SLIDE_SECONDS,
        audio_duration / len(images) if audio_duration else DEFAULT_SLIDE_SECONDS,
    )

    input_path = reel_folder / "input.txt"
    with input_path.open("w", encoding="utf-8", newline="\n") as input_file:
        for image in images:
            input_file.write(f"file '{image.name}'\n")
            input_file.write(f"duration {slide_seconds:.3f}\n")
        input_file.write(f"file '{images[-1].name}'\n")

    command_text = COMMAND_TEMPLATE.read_text(encoding="utf-8").strip()
    audio_input = (
        f"-i {shlex.quote(audio_path.as_posix())}"
        if audio_path.is_file()
        else ""
    )
    audio_options = "-c:a aac" if audio_path.is_file() else "-an"
    command = Template(command_text).substitute(
        input_file=shlex.quote(input_path.as_posix()),
        audio_input=audio_input,
        audio_options=audio_options,
        output_file=shlex.quote((reel_folder / "reel.mp4").as_posix()),
    )
    arguments = shlex.split(command)
    if shutil.which(arguments[0]) is None:
        raise RuntimeError("FFmpeg was not found. Install FFmpeg and add it to PATH.")

    output_path = reel_folder / "reel.mp4"
    if output_path.exists():
        output_path.unlink()

    try:
        subprocess.run(arguments, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as error:
        details = error.stderr.strip() or "FFmpeg could not create the reel."
        raise RuntimeError(details[-2000:]) from error

    return output_path
