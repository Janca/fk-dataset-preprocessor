import base64
import io

import PIL.Image
import cv2
import numpy
import requests

SUPPORTED_IMAGE_TYPES = ['.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff', '.tif']


def download_image(url: str) -> PIL.Image.Image:
    response = requests.get(url, 'rb', stream=True)
    if not response.ok:
        raise IOError(f'Failed to download: {url}')

    image_bio = io.BytesIO(response.content)

    try:
        return PIL.Image.open(image_bio)

    except:
        return None


def is_image(filepath: str) -> bool:
    for extension in SUPPORTED_IMAGE_TYPES:
        if filepath.endswith(extension):
            return True

    return False


def load_image_from_filepath(filepath: str) -> PIL.Image.Image:
    with open(filepath, 'rb') as f:  # should close the file handle by writing into byte buffer
        _bytes = f.read()

    bytes_io = io.BytesIO(_bytes)
    return PIL.Image.open(bytes_io)


def image_to_b64_jpeg(image: PIL.Image.Image, quality=90) -> str:
    with io.BytesIO() as bio:
        image.save(bio, format="JPEG", optimize=True, quality=quality)
        return base64.b64encode(bio.getvalue()).decode('utf-8')


def pil_to_cv2(image: PIL.Image.Image) -> numpy.ndarray:
    """
    Credits: https://gist.github.com/panzi/1ceac1cb30bb6b3450aa5227c02eedd3
    :param image: Pillow image
    :return: numpy array for cv2
    """

    mode = image.mode
    new_image: numpy.ndarray

    if mode == '1':
        new_image = numpy.array(image, dtype=numpy.uint8)
        new_image *= 255

    elif mode == 'L':
        new_image = numpy.array(image, dtype=numpy.uint8)

    elif mode == 'LA' or mode == 'La':
        new_image = numpy.array(image.convert('RGBA'), dtype=numpy.uint8)
        new_image = cv2.cvtColor(new_image, cv2.COLOR_RGBA2BGRA)

    elif mode == 'RGB':
        new_image = numpy.array(image, dtype=numpy.uint8)
        new_image = cv2.cvtColor(new_image, cv2.COLOR_RGB2BGR)

    elif mode == 'RGBA':
        new_image = numpy.array(image, dtype=numpy.uint8)
        new_image = cv2.cvtColor(new_image, cv2.COLOR_RGBA2BGRA)

    elif mode == 'LAB':
        new_image = numpy.array(image, dtype=numpy.uint8)
        new_image = cv2.cvtColor(new_image, cv2.COLOR_LAB2BGR)

    elif mode == 'HSV':
        new_image = numpy.array(image, dtype=numpy.uint8)
        new_image = cv2.cvtColor(new_image, cv2.COLOR_HSV2BGR)

    elif mode == 'YCbCr':
        # XXX: not sure if YCbCr == YCrCb
        new_image = numpy.array(image, dtype=numpy.uint8)
        new_image = cv2.cvtColor(new_image, cv2.COLOR_YCrCb2BGR)

    elif mode == 'P' or mode == 'CMYK':
        new_image = numpy.array(image.convert('RGB'), dtype=numpy.uint8)
        new_image = cv2.cvtColor(new_image, cv2.COLOR_RGB2BGR)

    elif mode == 'PA' or mode == 'Pa':
        new_image = numpy.array(image.convert('RGBA'), dtype=numpy.uint8)
        new_image = cv2.cvtColor(new_image, cv2.COLOR_RGBA2BGRA)

    else:
        raise ValueError(f'unhandled image color mode: {mode}')

    return new_image
