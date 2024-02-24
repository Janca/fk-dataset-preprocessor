import sys
import typing

from fk.image.ImageContext import ImageContext
from fk.task.Task import Task, TaskType


class ImageSizeFilterPreferences(typing.TypedDict):
    minimum_edge: int | None
    maximum_edge: int | None

    minimum_width: int | None
    maximum_width: int | None

    minimum_height: int | None
    maximum_height: int | None


class ImageSizeFilter(Task[ImageSizeFilterPreferences]):
    minimum_edge: int | None
    maximum_edge: int | None

    minimum_width: int | None
    maximum_width: int | None

    minimum_height: int | None
    maximum_height: int | None

    def load_preferences(self, preferences: ImageSizeFilterPreferences, env: dict[str, any]) -> bool:
        self.minimum_edge = preferences.get('minimum_edge', 0)
        self.maximum_edge = preferences.get('maximum_edge', sys.maxsize)

        self.minimum_width = preferences.get('minimum_width', self.minimum_edge)
        self.maximum_width = preferences.get('maximum_width', self.maximum_edge)

        self.minimum_height = preferences.get('minimum_height', self.minimum_edge)
        self.maximum_height = preferences.get('maximum_height', self.maximum_edge)

        return self.minimum_edge > 0 or self.maximum_edge != sys.maxsize \
            or self.minimum_width > 0 or self.maximum_width != sys.maxsize \
            or self.minimum_height > 0 or self.maximum_height != sys.maxsize

    def process(self, context: ImageContext) -> bool:
        image = context.image
        width, height = image.size

        if width < self.minimum_edge \
                or (self.minimum_width > width > self.maximum_width) \
                or width > self.maximum_edge:
            return False

        if height < self.minimum_edge \
                or (self.minimum_height > height > self.maximum_height) \
                or height > self.maximum_edge:
            return False

        return True

    @classmethod
    def id(cls) -> str:
        return 'fk:filter:image_size'

    @property
    def type(self) -> TaskType:
        return TaskType.CPU
