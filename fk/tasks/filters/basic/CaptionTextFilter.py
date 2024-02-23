import typing

from fk.image.ImageContext import ImageContext
from fk.task.Task import Task, TaskType


class CaptionTextFilterPreferences(typing.TypedDict):
    caption_text_required: bool | None
    allowed_tags: list[str] | str | None
    disallowed_tags: list[str] | str | None


class CaptionTextFilter(Task[CaptionTextFilterPreferences]):
    caption_text_required: bool | None
    allowed_tags: list[str] | str | None
    disallowed_tags: list[str] | str | None

    def load_preferences(self, preferences: CaptionTextFilterPreferences) -> bool:
        self.caption_text_required = preferences.get('caption_text_required', False)
        self.allowed_tags = preferences.get('allowed_tags', None)
        self.disallowed_tags = preferences.get('disallowed_tags', None)

        return any([self.caption_text_required, self.allowed_tags, self.disallowed_tags])

    def process(self, context: ImageContext) -> bool:
        caption_text = context.caption_text
        valid_text = caption_text is not None and caption_text.strip() != ''

        if self.caption_text_required:
            if not valid_text:
                return False

        if not valid_text:
            return True

        if self.allowed_tags:
            lc_caption_text = caption_text.lower()
            for allowed_tag in self.allowed_tags:
                allowed_tag = allowed_tag.lower()
                if allowed_tag in lc_caption_text:
                    return True

        if self.disallowed_tags:
            lc_caption_text = caption_text.lower()
            for disallowed_tag in self.disallowed_tags:
                disallowed_tag = disallowed_tag.lower()
                if disallowed_tag in lc_caption_text:
                    return False

        return self.allowed_tags is None or len(self.allowed_tags)

    @classmethod
    def id(cls) -> str:
        return 'fk:filter:caption_text'

    @property
    def type(self) -> TaskType:
        return TaskType.CPU


