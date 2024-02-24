import typing

from fk.image import ImageContext
from fk.worker import TaskType
from fk.worker.Task import Task

_DEFAULT_MODE = 'replace'


class ExtractA1111PromptMetaPreferences(typing.TypedDict):
    mode: typing.Literal['append', 'replace', 'prefix']
    skip_on_existing_caption: bool
    fail_on_invalid_caption: bool


class ExtractA1111PromptMeta(Task[ExtractA1111PromptMetaPreferences | bool]):
    mode: str
    skip_on_existing_caption: bool
    fail_on_invalid_caption: bool

    def load_preferences(self, preferences: ExtractA1111PromptMetaPreferences | bool, env: dict[str, any]) -> bool:
        if isinstance(preferences, dict):
            self.mode = preferences.get('mode', _DEFAULT_MODE)
            self.skip_on_existing_caption = preferences.get('skip_on_existing_caption', True)
            self.fail_on_invalid_caption = preferences.get('fail_on_invalid_caption', True)

        else:
            self.mode = _DEFAULT_MODE
            self.skip_on_existing_caption = True
            self.fail_on_invalid_caption = True

        return preferences

    def process(self, context: ImageContext) -> bool:
        image = context.image
        metadata = image.info

        if metadata is None:
            return not self.fail_on_invalid_caption

        caption_text = context.caption_text
        if self.skip_on_existing_caption:
            if caption_text is not None and caption_text != '':
                return True

        parameters_str = metadata.get('parameters', None)
        if parameters_str is None:
            return not self.fail_on_invalid_caption

        parameters = parameters_str.split("\n")
        if len(parameters) > 0:
            prompt = parameters[0].strip()

            if prompt == '':
                return not self.fail_on_invalid_caption

            mode = self.mode
            if mode == 'replace':
                caption_text = prompt

            elif mode == 'append':
                if caption_text:
                    caption_text = f"{caption_text}, {prompt}"

                else:
                    caption_text = prompt

            elif mode == 'prefix':
                if caption_text:
                    caption_text = f"{prompt}, {caption_text}"

                else:
                    caption_text = prompt

            else:
                self.logger.error(f"Unknown mode '{mode}'.")
                return self.fail_on_invalid_caption

            context.caption_text = caption_text
            return True

        return self.fail_on_invalid_caption

    @property
    def type(self) -> TaskType:
        return TaskType.CPU

    @classmethod
    def id(cls):
        return 'fk:action:extract_webui_prompt'
