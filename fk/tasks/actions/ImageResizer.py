import typing

import PIL.Image

from fk.image.ImageContext import ImageContext
from fk.task.Task import Task, TaskType


class ImageResizerPreferences(typing.TypedDict):
    minimum_edge: int | None
    maximum_edge: int | None

    minimum_width: int | None
    maximum_width: int | None

    minimum_height: int | None
    maximum_height: int | None


class ImageResizer(Task[ImageResizerPreferences]):
    minimum_edge: int | None
    maximum_edge: int | None

    minimum_width: int | None
    maximum_width: int | None

    minimum_height: int | None
    maximum_height: int | None

    def load_preferences(self, preferences: ImageResizerPreferences) -> bool:
        self.minimum_edge = preferences.get('minimum_edge', None)
        self.maximum_edge = preferences.get('maximum_edge', None)

        self.minimum_width = preferences.get('minimum_width', self.minimum_edge)
        self.maximum_width = preferences.get('maximum_width', self.maximum_edge)

        self.minimum_height = preferences.get('minimum_height', self.minimum_edge)
        self.maximum_height = preferences.get('maximum_height', self.maximum_edge)

        return any(
            [
                self.minimum_width,
                self.maximum_width,
                self.minimum_height,
                self.maximum_height
            ]
        )

    def process(self, context: ImageContext) -> bool:
        image = context.image
        original_width, original_height = image.size
        new_width, new_height = original_width, original_height

        if self.minimum_width and original_width < self.minimum_width:
            new_width = self.minimum_width
            new_height = int((self.minimum_width / original_width) * original_height)

        elif self.maximum_width and original_width > self.maximum_width:
            new_width = self.maximum_width
            new_height = int((self.maximum_width / original_width) * original_height)

        if self.minimum_height and new_height < self.minimum_height:
            new_height = self.minimum_height
            new_width = int((self.minimum_height / original_height) * original_width)

        elif self.maximum_height and new_height > self.maximum_height:
            new_height = self.maximum_height
            new_width = int((self.maximum_height / original_height) * original_width)

        if (new_width, new_height) != (original_width, original_height):
            resampler = PIL.Image.LANCZOS
            context.image = image.resize((new_width, new_height), resample=resampler)
            image.close()

        return True

    @classmethod
    def id(cls) -> str:
        return 'fk:action:image_resize'

    @property
    def type(self) -> TaskType:
        return TaskType.CPU


