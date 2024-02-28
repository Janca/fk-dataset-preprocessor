from fk.image import ImageContext
from fk.worker.Task import Task, TaskType


class ConvertImageMode(Task[str]):
    image_mode: str

    def load_preferences(self, preferences: str, env: dict[str, any]) -> bool:
        self.image_mode = preferences

        return self.image_mode is not None

    def process(self, context: ImageContext) -> bool:
        image = context.image
        converted = image.convert(self.image_mode)

        image.close()
        context.image = converted

        return True

    @property
    def type(self) -> TaskType:
        return TaskType.CPU

    @classmethod
    def id(cls):
        return 'fk:action:convert_image_mode'
