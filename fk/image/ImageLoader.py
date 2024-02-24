import abc

import PIL.Image


class ImageLoader(abc.ABC):

    @abc.abstractmethod
    def load_image(self) -> PIL.Image.Image:
        raise NotImplementedError()

    @abc.abstractmethod
    def load_caption_text(self) -> str | None:
        raise NotImplementedError()
