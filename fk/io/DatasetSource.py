import abc
import logging
import typing

from fk.common.Preprocessor import Preprocessor
from fk.image.ImageLoader import ImageLoader

_T = typing.TypeVar("_T")


class DatasetSource(Preprocessor[_T], abc.ABC):

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abc.abstractmethod
    def next(self) -> typing.Iterator[ImageLoader]:
        raise NotImplementedError()
