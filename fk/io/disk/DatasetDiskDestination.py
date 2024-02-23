import hashlib
import io
import os
import typing
import uuid

import PIL.Image

from fk.image import ImageContext
from fk.io.DatasetDestination import DatasetDestination

_DEFAULT_IMAGE_EXTENSION = '.png'
_DEFAULT_CAPTION_TEXT_EXTENSION = '.txt'
_DEFAULT_JPG_QUALITY = 95


class DatasetDiskDestinationPreferences(typing.TypedDict):
    path: str
    image_extension: str
    caption_text_extension: str
    kwargs: dict[str, any]


class DatasetDiskDestination(DatasetDestination[DatasetDiskDestinationPreferences | str]):
    destination_path: str
    image_ext: str
    text_ext: str
    kwargs: dict[str, any]

    extensions: dict[str, str]

    def load_preferences(self, preferences: DatasetDiskDestinationPreferences | str) -> bool:
        if isinstance(preferences, str):
            self.destination_path = preferences.strip()
            self.image_ext = _DEFAULT_IMAGE_EXTENSION
            self.text_ext = _DEFAULT_CAPTION_TEXT_EXTENSION
            self.kwargs = {}

            return self.validate_str(self.destination_path)

        self.destination_path = preferences.get('path', None)
        self.image_ext = preferences.get('image_extension', _DEFAULT_IMAGE_EXTENSION)
        self.text_ext = preferences.get('caption_text_extension', _DEFAULT_CAPTION_TEXT_EXTENSION)
        self.kwargs = preferences.get('kwargs', {})

        return self.validate_str(self.destination_path)

    def initialize(self, env: dict[str, any] = None):
        self.extensions = PIL.Image.registered_extensions()
        os.makedirs(self.destination_path, exist_ok=True)

    def save(self, context: ImageContext) -> bool:
        image = context.image
        caption_text = context.caption_text

        with image:
            with io.BytesIO() as bio:
                image_format = self.extensions[self.image_ext]
                image.save(bio, format=image_format, optimize=True, **self.kwargs)

                image_bytes = bio.getvalue()
                image_hash = hashlib.sha256(image_bytes).hexdigest()

                output_name = image_hash[:32]
                image_filepath = os.path.join(self.destination_path, output_name + self.image_ext)

                if not os.path.exists(image_filepath):
                    with open(image_filepath, 'wb') as f:
                        f.write(image_bytes)

        if self.validate_str(caption_text):
            caption_text_filepath = os.path.join(self.destination_path, output_name + self.text_ext)

            if not os.path.exists(caption_text_filepath):
                with open(caption_text_filepath, 'w+', encoding='utf-8') as f:
                    f.write(caption_text.strip())

        return True

    @classmethod
    def id(cls) -> str:
        return 'fk:destination:disk'

    @staticmethod
    def validate_str(s: str) -> bool:
        return s is not None and s.strip() != ''
