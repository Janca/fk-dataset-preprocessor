import os
import typing

import PIL.Image

import fk.utils
from fk.image import ImageLoader
from fk.io.DatasetSource import DatasetSource


class DatasetDiskSourceImageLoader(ImageLoader):

    def __init__(self, image_filepath: str, caption_filepath: str | None):
        self.image_filepath = image_filepath
        self.caption_filepath = caption_filepath

    def load_image(self) -> PIL.Image.Image:
        return fk.utils.image.load_image_from_filepath(self.image_filepath)

    def load_caption_text(self) -> str | typing.Literal['']:
        if self.caption_filepath is not None:
            return fk.utils.text.load_text_from_file(self.caption_filepath)

        return ''


class DatasetDiskSource(DatasetSource[list[str] | str]):
    source_paths: list[str]

    def load_preferences(self, preferences: list[str] | str) -> bool:
        if isinstance(preferences, list):
            self.source_paths = preferences

        elif isinstance(preferences, str):
            self.source_paths = [preferences]

        else:
            raise TypeError(f"Invalid input source paths type: {type(preferences)}; expected str or list of str")

        self.source_paths = list(set(filter(lambda it: it is not None and len(it.strip()) > 0, self.source_paths)))
        for source_path in self.source_paths:
            if not os.path.exists(source_path):
                raise IOError(f"Directory path '{source_path}' does not exist.")

        return len(self.source_paths) > 0

    def next(self) -> typing.Iterator[ImageLoader]:
        for source_path in self.source_paths:
            self.logger.info(f"Processing directory path '{source_path}'.")
            for image_path, caption_path in self.iterate_path(source_path):
                yield DatasetDiskSourceImageLoader(image_path, caption_path)

    @classmethod
    def id(cls) -> str:
        return 'fk:source:disk'

    @classmethod
    def find_caption_sibling(cls, dirpath: str, name: str) -> str | None:
        for ext in fk.utils.text.SUPPORTED_CAPTION_EXTENSIONS:
            filepath = os.path.join(dirpath, name + ext)

            if os.path.exists(filepath):
                return filepath

        return None

    @classmethod
    def iterate_path(cls, path: str) -> tuple[str, str | None]:
        caption_filepaths = {}

        for dirpath, subs, files in os.walk(path):
            for file in files:
                filepath = os.path.join(dirpath, file)
                basename = os.path.basename(filepath)
                splitext = os.path.splitext(basename)

                name = splitext[0]
                if fk.utils.image.is_image(filepath):
                    if name in caption_filepaths:
                        caption_filepath = caption_filepaths[name]
                        del caption_filepaths[name]

                    else:
                        caption_filepath = cls.find_caption_sibling(dirpath, name)

                    yield filepath, caption_filepath

                elif fk.utils.text.is_caption_text(filepath):
                    caption_filepaths[name] = filepath

            for sub in subs:
                subpath = os.path.join(dirpath, sub)
                yield from cls.iterate_path(subpath)
