from fk.image.ImageContext import ImageContext
from fk.task.Task import Task, TaskType


class CaptionPrefixer(Task[str]):
    prefix: str

    def load_preferences(self, preferences: str, env: dict[str, any]) -> bool:
        self.prefix = preferences.strip()
        return self.prefix != ''

    def process(self, context: ImageContext) -> bool:
        caption_text = context.caption_text
        if caption_text is None or caption_text.strip() == '':
            context.caption_text = self.prefix
            return True

        if caption_text.startswith(self.prefix):
            return True

        context.caption_text = f"{self.prefix}, {caption_text}"
        return True

    @classmethod
    def id(cls) -> str:
        return 'fk:action:caption_prefixer'

    @property
    def type(self) -> TaskType:
        return TaskType.CPU
