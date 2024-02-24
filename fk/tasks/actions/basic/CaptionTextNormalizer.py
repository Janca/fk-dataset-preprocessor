import typing

import unidecode

import fk.utils.text
from fk.image import ImageContext
from fk.worker.Task import Task, TaskType


class CaptionTextNormalizerPreferences(typing.TypedDict):
    ascii: bool
    normalize: bool


class CaptionTextNormalizer(Task[CaptionTextNormalizerPreferences | bool]):
    ascii: bool
    normalize: bool

    def load_preferences(self, preferences: CaptionTextNormalizerPreferences | bool, env: dict[str, any]) -> bool:
        if isinstance(preferences, dict):
            self.ascii = preferences.get('ascii', True)
            self.normalize = preferences.get('normalize', True)

        elif isinstance(preferences, bool) and preferences:
            self.ascii = True
            self.normalize = True

        return preferences

    def process(self, context: ImageContext) -> bool:
        caption_text = context.caption_text
        if caption_text is None:
            return True

        if caption_text.strip() == '':
            return True

        if self.normalize:
            caption_text = fk.utils.text.normalize_caption_text(caption_text)

        if self.ascii:
            caption_text = unidecode.unidecode(caption_text)

        context.caption_text = caption_text
        return True

    @classmethod
    def id(cls) -> str:
        return 'fk:action:caption_text_normalizer'

    @property
    def type(self) -> TaskType:
        return TaskType.CPU
