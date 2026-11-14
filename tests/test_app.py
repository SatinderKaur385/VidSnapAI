import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import main


class AppTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.upload_folder = Path(self.temp_dir.name) / "uploads"
        self.previous_upload_folder = main.app.config["UPLOAD_FOLDER"]
        main.app.config.update(
            TESTING=True,
            UPLOAD_FOLDER=self.upload_folder,
        )
        self.client = main.app.test_client()

    def tearDown(self):
        main.app.config["UPLOAD_FOLDER"] = self.previous_upload_folder
        self.temp_dir.cleanup()

    def test_create_page_and_empty_gallery_load(self):
        self.assertEqual(self.client.get("/create").status_code, 200)
        self.assertEqual(self.client.get("/gallery").status_code, 200)

    def test_rejects_non_image_upload(self):
        response = self.client.post(
            "/create",
            data={"file1": (io.BytesIO(b"video"), "clip.mp4")},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Use JPG, JPEG, PNG, or WEBP images.", response.data)
        self.assertFalse(self.upload_folder.exists())

    def test_upload_creates_reel_and_gallery_entry(self):
        def create_placeholder_reel(folder):
            (Path(folder) / "reel.mp4").write_bytes(b"test video")

        with patch("main.create_reel", side_effect=create_placeholder_reel):
            response = self.client.post(
                "/create",
                data={
                    "uuid": "../../outside",
                    "file1": (io.BytesIO(b"image one"), "first image.jpg"),
                    "file2": (io.BytesIO(b"image two"), "second.jpg"),
                    "text": "",
                },
                follow_redirects=True,
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Your reel is ready.", response.data)
        self.assertIn(b"<video", response.data)

        reel_folders = list(self.upload_folder.iterdir())
        self.assertEqual(len(reel_folders), 1)
        reel_folder = reel_folders[0]
        self.assertEqual(reel_folder.parent, self.upload_folder)
        self.assertTrue((reel_folder / "001_first_image.jpg").is_file())
        self.assertTrue((reel_folder / "002_second.jpg").is_file())
        reel_response = self.client.get(f"/reels/{reel_folder.name}")
        self.assertEqual(reel_response.data, b"test video")
        reel_response.close()


if __name__ == "__main__":
    unittest.main()
