import typing

import cv2
import numpy

from fk.image.ImageContext import ImageContext
from fk.task.Task import Task, TaskType


class EntropyFilterPreferences(typing.TypedDict):
    minimum: float
    maximum: float


class EntropyFilter(Task[EntropyFilterPreferences]):
    minimum: float
    maximum: float

    def load_preferences(self, preferences: EntropyFilterPreferences | float) -> bool:
        if isinstance(preferences, dict):
            self.minimum = preferences.get('minimum', -1)
            self.maximum = preferences.get('maximum', -1)

        else:
            self.minimum = preferences
            self.maximum = -1

        return self.minimum != -1 or self.maximum != -1

    def process(self, context: ImageContext) -> bool:
        grayscale_image = context.cv2_grayscale_image

        hist = cv2.calcHist([grayscale_image], [0], None, [256], [0, 256])
        hist = hist.ravel() / hist.sum()
        logs = numpy.nan_to_num(numpy.log2(hist + numpy.finfo(float).eps))
        entropy = -1 * (hist * logs).sum()

        del hist
        del logs

        _min = self.minimum
        _max = self.maximum

        if _min != -1 and _min > entropy:
            return False

        if _max != -1 and entropy > _max:
            return False

        return True

    @classmethod
    def id(cls) -> str:
        return 'fk:filter:cv2_entropy'

    @property
    def type(self) -> TaskType:
        return TaskType.CPU
