import PIL.Image
import cv2

import fk.utils.image
import fk.utils.text
from .ImageLoader import ImageLoader


class ImageContext:

    def __init__(self, loader: ImageLoader):
        self.loader = loader

        self._caption_text = None
        self._image = None

        self._cv2 = None
        self._cv2_grayscale = None

    @property
    def image(self):
        if self._image is None:
            self._image = self.loader.load_image()

        return self._image

    @image.setter
    def image(self, image: PIL.Image.Image):
        self._image = image
        self._cv2 = None

    @property
    def cv2_image(self):
        if self._cv2 is None:
            self._cv2 = fk.utils.image.pil_to_cv2(self.image)

        return self._cv2

    @property
    def cv2_grayscale_image(self):
        if self._cv2_grayscale is None:
            self._cv2_grayscale = cv2.cvtColor(self.cv2_image, cv2.COLOR_BGR2GRAY)

        return self._cv2_grayscale

    @property
    def caption_text(self):
        if self._caption_text is None:
            self._caption_text = self.loader.load_caption_text()

            if self._caption_text is None:  # prevent disk read every call
                self._caption_text = ''

        return self._caption_text if self._caption_text is not None else ''

    @caption_text.setter
    def caption_text(self, caption_text: str):
        self._caption_text = caption_text

    def close(self):
        try:
            self._image.close()

            self._cv2 = None
            self._cv2_grayscale = None

        except:  # NOP
            pass
