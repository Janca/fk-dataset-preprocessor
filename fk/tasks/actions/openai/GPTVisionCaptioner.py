import json
import traceback
import typing

import PIL.Image
import openai

import fk.utils.image
from fk.image import ImageContext
from fk.worker.Task import Task, TaskType

_DEFAULT_PROMPT = """
Please describe this image, starting with the primary focus, and ending with the background details and styling.
Provide details like character attributes, skin color, hair color, hair style, perceived gender, emotions, and other 
facial attributes, such as freckles, eye color, facial hair, and whether the mouth is open or closed.

If the main subject is human, attempt to discern their occupation, or archetype
(wizard, paladin, nurse, lumberjack, etc).

If text appears in the image, caption with quotation marks where the text is inscribed, if possible, eg. 
"Hello" on a sign-post.

Attempt to identify mythological beings and archetypes (vampire, werewolf, leshy, mermaid, etc.), or if possible, 
directly caption a human or celebrity by name.

Finally, describe the background, first as a total, (forest, beach, indoors, living-room, etc.) and then describe 
individual elements of the background.

Take note of various lens effects, such as bokeh, depth of field, fish-eye lens, etc.
Attempt to identify the style of the image, whether it is realism, like a photograph, or some other mixed-media type 
(painting, charcoal, illustration, comic book art, anime, etc.).

The caption should be as if you are attempting to do SEO or a search on google, and be an abbreviated form of 
the combination of both the subject, and then the background caption, blended seamlessly with the relevant styles 
and artists.

Your caption text should not contain what is not available in the image, so mentions of "No other archetype...", or 
"No person...", etc should not be within the caption text. The caption should not explicitly state the missing 
attributes you are looking for.

Furthermore, do not start a caption with: "This image is a...", or "The primary focus of the image...", or 
"The background..." or any other variant, it is implied that what you are captioning is an image/subject/background; 
only when it is relevant to the caption should you explicitly mention that, such as when the image is an image 
or a poster, or canvas.

Commas matter in your caption text, do not comma-separate a list of adjectives unless that adjective is not apart of 
the noun in the sentence you are writing.
An example would be, "A big, red dog..." which should instead be written as "big red dog...", or "a vibrant, 
neon-colored..." would instead be "vibrant neon-colored".

Avoid too much filler text, brief, succinct descriptions are better.

You may be given a JSON object containing the field "caption", if provided, you will reference those tags for 
additional details of the image. These tags were generated with another AI and may be partially, or completely 
inaccurate. Enhance your captions with the provided one, if you find that they correctly match the image.

Only respond with the following JSON object with your newly generated caption, not within a code block:
{"openai_caption": "..."}
"""
_DEFAULT_FIDELITY = 'auto'
_DEFAULT_MODE = 'replace'


class GPTVisionCaptionerPreferences(typing.TypedDict):
    """
    {
        "openai_key": str | None,
        "system_prompt": str | None,
        "prompt": str | None,
        "fidelity": 'auto' | 'high' | 'low',
        "mode": 'append' | 'replace' | 'prefix',
        "skip_on_existing_caption": bool,
        "include_existing_caption_in_prompt": bool,
        "fail_on_invalid_caption": bool
    } | str | bool

    If passed as true, the task will default to:
    {
        "openai_key": None,
        "system_prompt": None,
        "prompt": _DEFAULT_PROMPT,
        "fidelity": 'auto',
        "mode": 'replace',
        "skip_on_existing_caption": true,
        "include_existing_caption_in_prompt": true,
        "fail_on_invalid_caption": true
    }

    If passed as a str, the task will default to the same as a true boolean
    value, but the string will be used as the prompt when submitting the image
    to OpenAI.
    """

    openai_key: str | None
    system_prompt: str | None
    prompt: str | None
    fidelity: typing.Literal['auto', 'high', 'low']
    mode: typing.Literal['append', 'replace', 'prefix']
    skip_on_existing_caption: bool
    include_existing_caption_in_prompt: bool
    fail_on_invalid_caption: bool


class GPTVisionCaptioner(Task[GPTVisionCaptionerPreferences | str | bool]):
    openai_key: str | None
    system_prompt: str | None
    prompt: str
    fidelity: str
    mode: str
    skip_on_existing_caption: bool
    include_existing_caption: bool
    fail_on_invalid_caption: bool

    client: openai.OpenAI | None

    def load_preferences(self, preferences: GPTVisionCaptionerPreferences | str, env: dict[str, any] | bool) -> bool:
        if isinstance(preferences, dict):
            self.openai_key = preferences.get('openai_key', None)
            self.system_prompt = preferences.get('system_prompt', None)
            self.prompt = preferences.get('prompt', _DEFAULT_PROMPT)
            self.fidelity = preferences.get('fidelity', _DEFAULT_FIDELITY)
            self.mode = preferences.get('mode', _DEFAULT_MODE)
            self.skip_on_existing_caption = preferences.get('skip_on_existing_caption', True)
            self.include_existing_caption = preferences.get('include_existing_caption_in_prompt', False)
            self.fail_on_invalid_caption = preferences.get('fail_on_invalid_caption', True)

        else:
            if isinstance(preferences, bool):
                if not preferences:
                    return False

                self.prompt = _DEFAULT_PROMPT

            elif isinstance(preferences, str):
                self.prompt = preferences

            self.openai_key = None
            self.system_prompt = None
            self.fidelity = _DEFAULT_FIDELITY
            self.mode = _DEFAULT_MODE
            self.skip_on_existing_caption = True
            self.include_existing_caption = True
            self.fail_on_invalid_caption = True

        if self.openai_key is None:
            self.openai_key = env.get('openai_key', None)

        if self.openai_key is not None:
            self.client = openai.OpenAI(api_key=self.openai_key)

        return self.openai_key is not None \
            and self.prompt

    def process(self, context: ImageContext) -> bool:
        caption_text = context.caption_text
        image = context.image

        if self.skip_on_existing_caption:
            if caption_text is not None and caption_text != '':
                return True

        if self.include_existing_caption:
            prompt = self.prompt

            if caption_text:
                caption_json = json.dumps({'caption': caption_text})
                prompt = f"{prompt}\n---\n{caption_json}"

        else:
            prompt = self.prompt

        openai_caption = self.generate_caption(image, prompt)

        if openai_caption is None:
            return False

        if isinstance(openai_caption, bool):
            return False

        openai_caption = openai_caption.get('openai_caption', None)
        if openai_caption is None:
            return False

        openai_caption = openai_caption.strip()
        if openai_caption == '':
            return not self.fail_on_invalid_caption

        mode = self.mode
        if mode == 'append':
            if caption_text:
                caption_text = f'{caption_text}, {openai_caption}'

            else:
                caption_text = openai_caption

        elif mode == 'replace':
            caption_text = openai_caption

        elif mode == 'prefix':
            if caption_text:
                caption_text = f'{openai_caption}, {caption_text}'

            else:
                caption_text = openai_caption

        else:
            self.logger.error(f"Unknown mode '{mode}'.")
            return False

        context.caption_text = caption_text
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
    ) -> dict[str, str] | None | bool:
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

    @classmethod
    def preferences_cls(cls) -> typing.Type | None:
        return GPTVisionCaptionerPreferences
