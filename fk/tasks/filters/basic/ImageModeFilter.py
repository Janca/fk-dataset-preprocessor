import typing

from fk.image import ImageContext
from fk.worker.Task import Task, TaskType


class ImageModeFilterPreferences(typing.TypedDict):
    allowed_modes: list[str] | str | None
    disallowed_modes: list[str] | str | None


class ImageModeFilter(Task[ImageModeFilterPreferences]):
    allowed_modes: list[str] | None
    disallowed_modes: list[str] | None

    def load_preferences(self, preferences: ImageModeFilterPreferences | None, env: dict[str, any]) -> bool:
        allowed_modes = preferences.get('allowed_modes', None)
        disallowed_modes = preferences.get('disallowed_modes', None)

        self.allowed_modes = [allowed_modes] \
            if isinstance(allowed_modes, str) \
            else allowed_modes

        self.disallowed_modes = [disallowed_modes] \
            if isinstance(disallowed_modes, str) \
            else disallowed_modes

        return self.allowed_modes is not None \
            or self.disallowed_modes is not None

    def process(self, context: ImageContext) -> bool:
        image = context.image
        image_mode = image.mode

        if self.allowed_modes is not None:
            if image_mode not in self.allowed_modes:
                return False

        if self.disallowed_modes is not None:
            if image_mode in self.disallowed_modes:
                return False

        return True

    @classmethod
    def id(cls) -> str:
        return 'fk:filter:image_mode'

    @property
    def type(self) -> TaskType:
        return TaskType.CPU
