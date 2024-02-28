import concurrent.futures
import random
import sys
import time
import traceback
import typing

import PIL.Image

from fk.image.ImageLoader import ImageLoader
from fk.io.DatasetSource import DatasetSource
from fk.worker.Task import TaskType
from .CivitaiImageLoader import CivitaiImageLoader
from .api import fetch_images, download_image
from .typing import CivitaiImageFilter, CivitaiImageSearchQuery, CivitaiImage
from .util import filter_image


class CivitaiImageScraperPreferences(typing.TypedDict):
    civitai_key: str | None

    query: CivitaiImageSearchQuery
    filter: CivitaiImageFilter

    max_images: int | None
    max_pages: int | None
    max_attempts: int | None


class CivitaiImageScraper(DatasetSource[CivitaiImageScraperPreferences]):
    civitai_key: str | None

    filter: CivitaiImageFilter

    max_images: int
    max_pages: int
    max_attempts: int

    civitai_search_query: CivitaiImageSearchQuery
    civitai_search_filter: CivitaiImageFilter

    def __init__(self):
        self.downloaded_images = 0
        self._error = False

    def load_preferences(self, preferences: CivitaiImageScraperPreferences | bool, env: dict[str, any]) -> bool:
        if isinstance(preferences, bool) and preferences:
            preferences = {}

        elif not preferences:
            return False

        self.civitai_key = preferences.get('civitai_key', None)

        self.civitai_search_filter = preferences.get('filter', {})
        self.civitai_search_query = preferences.get('query', {'sort': 'Most Buzz'})

        self.max_images = preferences.get('max_images', sys.maxsize)
        self.max_pages = preferences.get('max_pages', sys.maxsize)

        self.max_attempts = preferences.get('max_attempts', 5)

        if self.civitai_key is None:
            self.civitai_key = env.get('civitai_key', None)

        return True

    def _download_image_fn(self, image_json: CivitaiImage):

        image = None
        for i in range(self.max_attempts):
            try:
                time.sleep(random.uniform(0.1, 1.25))
                image = download_image(image_json)
                break

            except:
                continue

        if image is not None:
            self.downloaded_images += 1

        return image_json, image

    def next(self) -> typing.Iterator[ImageLoader]:
        downloaded_images = 0
        queried_pages = 0

        retries = 0

        next_cursor: str | None = None
        while self.downloaded_images < self.max_images and queried_pages < self.max_pages:
            query = self.civitai_search_query.copy()

            if next_cursor is not None:
                query['cursor'] = next_cursor

            try:
                search_results = fetch_images(query)
                queried_pages += 1

                metadata = search_results.get('metadata', {})
                next_cursor = metadata.get('next_cursor', None)

                items = search_results.get('items', None)
                if items:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as tpe:
                        futures: list[concurrent.futures.Future[tuple[CivitaiImage, PIL.Image.Image]]] = []

                        for image_json in items:
                            if not filter_image(image_json, self.civitai_search_filter):
                                continue

                            if downloaded_images + 1 >= self.max_images:
                                break

                            retries = 0

                            future = tpe.submit(self._download_image_fn, image_json)
                            futures.append(future)

                            for future in concurrent.futures.as_completed(futures):
                                _image_json, downloaded_image = future.result()
                                yield CivitaiImageLoader(_image_json, downloaded_image)


            except Exception as e:
                traceback.print_exception(e)

                retries += 1
                if retries > 10:
                    self.logger.error("Failed to fetch images from Civitai API more than 10 times.")
                    break

                continue

    @property
    def type(self) -> TaskType:
        return TaskType.CPU

    @classmethod
    def id(cls):
        return 'fk:source:civitai_image_scraper'
