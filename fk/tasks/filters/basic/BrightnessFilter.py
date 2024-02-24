import math
import typing

import PIL.ImageStat

from fk.image import ImageContext
from fk.worker.Task import Task, TaskType


class BrightnessFilterPreferences(typing.TypedDict):
    minimum: float | None
    maximum: float | None


class BrightnessFilter(Task[BrightnessFilterPreferences]):
    minimum: float
    maximum: float

    def load_preferences(self, preferences: BrightnessFilterPreferences, env: dict[str, any]) -> bool:
        self.minimum = preferences.get('minimum', 0.0)
        self.maximum = preferences.get('maximum', 1.0)

        return self.minimum > 0 or self.maximum < 1.0

    def process(self, context: ImageContext) -> bool:
        rgb_image = context.image.convert('RGB')
        image_stat = PIL.ImageStat.Stat(rgb_image)

        r, g, b = image_stat.mean
        perceived_brightness = math.sqrt((0.241 * (r ** 2)) + (0.691 * (g ** 2)) + (0.068 * (b ** 2))) / 255

        rgb_image.close()
        return self.minimum <= perceived_brightness <= self.maximum

    @property
    def type(self) -> TaskType:
        return TaskType.CPU

    @classmethod
    def id(cls):
        return 'fk:filter:image_brightness'
