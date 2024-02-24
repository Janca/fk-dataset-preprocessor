import typing

import PIL.Image
import imagehash

from fk.image import ImageContext
from fk.worker.Task import Task, TaskType


class ImagePerceptualHashFilterPreferences(typing.TypedDict):
    hash_type: str | None
    hash_size: int | None
    distance_threshold: float | None


class ImagePerceptualHashFilter(Task[ImagePerceptualHashFilterPreferences]):
    hash_size: int | None
    hash_type: str | None
    distance_threshold: float | None

    hash_fn: typing.Callable

    def __init__(self):
        super().__init__()
        self.image_hashes: set[imagehash.ImageHash | imagehash.ImageMultiHash] = set()

    def load_preferences(self, preferences: ImagePerceptualHashFilterPreferences, env: dict[str, any]) -> bool:
        self.hash_type = preferences.get('hash_type', None)

        self.hash_size = preferences.get('hash_size', None)
        self.distance_threshold = preferences.get('distance_threshold', None)

        valid = all([self.hash_size, self.distance_threshold])
        if not valid:
            return False

        if self.hash_type is None:
            self.logger.warning("Image hashing function was not set; defaulting to 'phash'.")
            self.hash_type = 'phash'

        if not hasattr(imagehash, self.hash_type):
            self.logger.error(f"Hash type '{self.hash_type}' is not defined in module 'imagehash'.")
            return False

        return True

    def initialize(self):
        self.hash_fn = getattr(imagehash, self.hash_type)

    def process(self, context: ImageContext) -> bool:
        image = context.image
        image_hash = self.hash_func(image)

        if image_hash in self.image_hashes:
            return False

        for img_hash in self.image_hashes:
            if image_hash - img_hash <= self.distance_threshold:
                return False

        self.image_hashes.add(image_hash)
        return True

    def hash_func(self, image: PIL.Image.Image) -> imagehash.ImageHash | imagehash.ImageMultiHash:
        return self.hash_fn(image, hash_size=self.hash_size)

    @classmethod
    def id(cls) -> str:
        return 'fk:filter:image_hash'

    @property
    def type(self) -> TaskType:
        return TaskType.CPU
