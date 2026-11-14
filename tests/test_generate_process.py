import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from generate_process import create_reel


FFMPEG_AVAILABLE = shutil.which("ffmpeg") and shutil.which("ffprobe")


@unittest.skipUnless(FFMPEG_AVAILABLE, "FFmpeg and FFprobe are required")
class ReelGenerationTests(unittest.TestCase):
    def test_short_audio_does_not_cut_off_reel(self):
        project_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            reel_folder = Path(temp_dir)
            shutil.copyfile(project_root / "static" / "1.jpg", reel_folder / "001_sample.jpg")
            subprocess.run(
                [
                    "ffmpeg", "-y", "-f", "lavfi",
                    "-i", "sine=frequency=440:duration=0.8",
                    "-q:a", "5", str(reel_folder / "audio.mp3"),
                ],
                check=True,
                capture_output=True,
            )

            reel_path = create_reel(reel_folder)
            probe = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-show_entries", "stream=codec_type",
                    "-show_entries", "format=duration",
                    "-of", "json", str(reel_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            result = json.loads(probe.stdout)

            self.assertGreater(float(result["format"]["duration"]), 2.5)
            self.assertIn("audio", [stream["codec_type"] for stream in result["streams"]])


if __name__ == "__main__":
    unittest.main()
