import fk.utils.text

from fk.image import ImageContext
from fk.worker.Task import Task, TaskType


class CaptionTextNormalizer(Task[bool]):

    def load_preferences(self, preferences: bool, env: dict[str, any]) -> bool:
        return preferences

    def process(self, context: ImageContext) -> bool:
        caption_text = context.caption_text
        if caption_text is None:
            return True

        if caption_text.strip() == '':
            return True

        context.caption_text = fk.utils.text.normalize_caption_text(caption_text)
        return True

    @classmethod
    def id(cls) -> str:
        return 'fk:action:caption_text_normalizer'

    @property
    def type(self) -> TaskType:
        return TaskType.CPU
