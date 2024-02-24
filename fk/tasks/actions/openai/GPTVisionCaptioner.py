import json
import time
import traceback
import typing

import PIL.Image
import openai

import fk.utils.image
from fk.image import ImageContext
from fk.task.Task import Task, TaskType

_DEFAULT_PROMPT = ''
_DEFAULT_FIDELITY = 'auto'
_DEFAULT_MODE = 'replace'


class GPTVisionCaptionerPreferences(typing.TypedDict):
    openai_key: str | None
    system_prompt: str | None
    prompt: str | None
    fidelity: typing.Literal['auto', 'high', 'low']
    mode: typing.Literal['append', 'replace', 'prefix']


class GPTVisionCaptioner(Task[GPTVisionCaptionerPreferences | str]):
    openai_key: str | None
    system_prompt: str | None
    prompt: str
    fidelity: str
    mode: str

    client: openai.OpenAI | None

    def load_preferences(self, preferences: GPTVisionCaptionerPreferences | str, env: dict[str, any]) -> bool:
        if isinstance(preferences, dict):
            self.openai_key = preferences.get('openai_key', None)
            self.system_prompt = preferences.get('system_prompt', None)
            self.prompt = preferences.get('prompt', _DEFAULT_PROMPT)
            self.fidelity = preferences.get('fidelity', _DEFAULT_FIDELITY)
            self.mode = preferences.get('mode', _DEFAULT_MODE)

        else:
            self.openai_key = None
            self.system_prompt = _DEFAULT_PROMPT
            self.prompt = preferences
            self.fidelity = _DEFAULT_FIDELITY
            self.mode = _DEFAULT_MODE

        if self.openai_key is None:
            self.openai_key = env.get('openai_key', None)

        if self.openai_key is not None:
            self.client = openai.OpenAI(api_key=self.openai_key)

        return self.openai_key is not None \
            and self.prompt

    def process(self, context: ImageContext) -> bool:
        caption_text = context.caption_text
        image = context.image

        prompt = self.prompt.replace('%caption_text%', caption_text).strip()
        openai_caption = self.generate_caption(image, prompt)
        time.sleep(0.25)

        if openai_caption is None:
            return False

        if isinstance(openai_caption, bool):
            return False

        openai_caption = openai_caption['caption']

        mode = self.mode
        if mode == 'append':
            caption_text = f'{caption_text}, {openai_caption}'

        elif mode == 'replace':
            caption_text = openai_caption

        elif mode == 'prefix':
            caption_text = f'{openai_caption}, {caption_text}'

        else:
            self.logger.warning(f"Unknown mode: '{mode}'.")
            return False

        context.caption_text = caption_text
        self.logger.info("Captioned: " + caption_text)
        return True

    @property
    def type(self) -> TaskType:
        return TaskType.CPU

    @classmethod
    def id(cls):
        return 'fk:action:gpt_vision_captioner'

    def generate_caption(
            self,
            image: PIL.Image.Image,
            prompt: str,
            fidelity: typing.Literal['low', 'high', 'auto'] = 'auto'
    ) -> dict[str, str]:
        image_b64 = fk.utils.image_to_b64_jpeg(image)

        try:
            messages = []
            if self.system_prompt:
                messages.append(
                    {
                        'role': 'system',
                        'content': self.system_prompt
                    }
                )

            messages.append(
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': prompt
                        },
                        {
                            'type': 'image',
                            'image_url': {
                                'url': f'data:image/jpeg;base64,{image_b64}',
                                'detail': fidelity
                            }
                        }
                    ]
                }
            )

            stream_response = self.client.chat.completions.create(
                model='gpt-4-vision-preview',
                stream=True,
                messages=messages,
                max_tokens=2000,
                timeout=20
            )

            message = ""
            is_json_object = False
            for index, chunk in enumerate(stream_response):
                chunk_text = chunk.choices[0].delta.content

                if not chunk_text:
                    stop_reason = chunk.choices[0].finish_reason
                    if stop_reason in ['stop', 'max_tokens']:
                        break

                    continue

                if not is_json_object:
                    if chunk_text.strip()[0] != '{':
                        # print(f'Expecting json, got "{chunk_text}"')
                        return None

                    else:
                        is_json_object = True

                message += chunk_text

            try:
                return json.loads(message)

            except Exception as e:
                traceback.print_exception(e)
                return None

        except openai.BadRequestError as e:
            if e.message.index('safety system') != -1:
                pass  # todo

            traceback.print_exception(e)
            return False

        except Exception as e:
            traceback.print_exception(e)
            return None

    @property
    def max_attempts(self) -> int:
        return 5

    @property
    def max_ipm(self) -> int:
        return 5
