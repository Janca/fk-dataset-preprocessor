import PIL.Image
import requests

import fk.utils.image
from .typing import CivitaiImageSearchQuery, CivitaiImageSearchResults, CivitaiImage
from .util import generate_search_url


def fetch_images(query: CivitaiImageSearchQuery) -> CivitaiImageSearchResults:
    url = generate_search_url(query)

    with requests.get(url) as response:
        response.raise_for_status()
        return response.json()


def download_image(image: CivitaiImage) -> PIL.Image.Image:
    image_url = image['url'].removesuffix(".jpeg")
    return fk.utils.image.download_image(image_url)
