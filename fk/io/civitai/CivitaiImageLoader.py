import PIL.Image

from fk.image.ImageLoader import ImageLoader
from .typing import CivitaiImage


class CivitaiImageLoader(ImageLoader):

    def __init__(self, image_meta: CivitaiImage, image: PIL.Image.Image):
        self.image_meta = image_meta
        self.image = image

    def load_image(self) -> PIL.Image.Image:
        return self.image

    def load_caption_text(self) -> str | None:
        if 'meta' not in self.image_meta:
            return None

        prompt = self.image_meta['meta'].get('prompt')
        prompt_lines = prompt.splitlines()

        prompt_str = ''
        lines_len = len(prompt_lines)
        for index, line in enumerate(prompt_lines):
            line = line.strip()

            if index == lines_len - 1:
                prompt_str += line

            elif not line.endswith(','):
                prompt_str += f'{line}, '

            else:
                prompt_str += f' {line}'

        return prompt_str.strip()
