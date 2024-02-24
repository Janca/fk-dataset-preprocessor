import typing

from fk.image.ImageContext import ImageContext
from fk.task.Task import Task, TaskType


class ImageRatioFilterPreferences(typing.TypedDict):
    allowed_ratios: list[float | str] | float | str | None
    disallowed_ratios: list[float | str] | float | str | None
    allow_inverse: bool


class ImageRatioFilter(Task[ImageRatioFilterPreferences]):
    allowed_ratios: list[float | str] | float | str | None
    disallowed_ratios: list[float | str] | float | str | None
    allow_inverse: bool

    def load_preferences(self, preferences: ImageRatioFilterPreferences, env: dict[str, any]) -> bool:
        self.allowed_ratios = preferences.get("allowed_ratios", None)
        self.disallowed_ratios = preferences.get("disallowed_ratios", None)
        self.allow_inverse = preferences.get("allow_inverse", False)

        return self.allowed_ratios is not None \
            or self.disallowed_ratios is not None

    def process(self, context: ImageContext) -> bool:
        image = context.image
        width, height = image.size

        ratio = width / height
        inverse_ratio = height / width

        return self.test_ratio(ratio) \
            or (self.allow_inverse and self.test_ratio(inverse_ratio))

    def test_ratio(self, ratio):
        if self.allowed_ratios:
            if ratio not in self.allowed_ratios:
                return False

        if self.disallowed_ratios:
            if ratio in self.disallowed_ratios:
                return False

        return True

    @classmethod
    def id(cls) -> str:
        return 'fk:filter:image_ratio'

    @property
    def type(self) -> TaskType:
        return TaskType.CPU
