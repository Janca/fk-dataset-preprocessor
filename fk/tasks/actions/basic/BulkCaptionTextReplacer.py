import fk.utils.text

from fk.image import ImageContext
from fk.worker.Task import Task, TaskType


class BulkCaptionTextReplacer(Task[dict[str, str]]):
    replacements: dict[str, str]

    def load_preferences(self, preferences: dict[str, str], env: dict[str, any]) -> bool:
        self.replacements = preferences
        return len(preferences) > 0

    def process(self, context: ImageContext) -> bool:
        caption_text = context.caption_text
        replaced_tags = fk.utils.text.bulk_text_replacement(caption_text, self.replacements)
        context.caption_text = ', '.join(replaced_tags)

        return True

    @property
    def type(self) -> TaskType:
        return TaskType.CPU

    @classmethod
    def id(cls):
        return 'fk:action:bulk_caption_text_replacer'
