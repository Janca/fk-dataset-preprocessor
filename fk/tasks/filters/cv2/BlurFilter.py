import typing

import cv2

from fk.image import ImageContext
from fk.task.Task import Task, TaskType


class BlurFilterPreferences(typing.TypedDict):
    minimum: float
    maximum: float


class BlurFilter(Task[BlurFilterPreferences | float]):
    minimum: float
    maximum: float

    def load_preferences(self, preferences: BlurFilterPreferences | float, env: dict[str, any]) -> bool:
        if isinstance(preferences, dict):
            self.minimum = preferences.get('minimum', -1)
            self.maximum = preferences.get('maximum', -1)

        else:
            self.minimum = preferences
            self.maximum = -1

        return self.minimum != -1 or self.maximum != -1

    def process(self, context: ImageContext) -> bool:
        grayscale_image = context.cv2_grayscale_image
        blur_score = cv2.Laplacian(grayscale_image, cv2.CV_64F).var()

        _min = self.minimum
        _max = self.maximum

        if _min != -1 and _min > blur_score:
            return False

        if _max != -1 and blur_score > _max:
            return False

        return True

    @classmethod
    def id(cls):
        return 'fk:filter:cv2_blur'

    @property
    def type(self) -> TaskType:
        return TaskType.CPU
