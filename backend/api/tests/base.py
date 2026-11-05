"""Shared helpers for API tests."""

import io
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image


def make_image_file(
    name: str = 'test.jpg',
    size: tuple[int, int] = (900, 600),
    color: str = 'green',
) -> SimpleUploadedFile:
    """Create an in-memory JPEG image for upload fields."""
    buffer = io.BytesIO()
    Image.new('RGB', size, color).save(buffer, format='JPEG')
    return SimpleUploadedFile(
        name,
        buffer.getvalue(),
        content_type='image/jpeg',
    )


class MediaMixin:
    """Use an isolated temporary directory for media files in tests."""

    @classmethod
    def setUpClass(cls):
        cls.media_root = tempfile.mkdtemp()
        cls.media_override = override_settings(MEDIA_ROOT=cls.media_root)
        cls.media_override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.media_override.disable()
        shutil.rmtree(cls.media_root, ignore_errors=True)
