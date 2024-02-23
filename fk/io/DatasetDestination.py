import abc
import logging
import typing

from fk.common.Preprocessor import Preprocessor
from fk.image.ImageContext import ImageContext

_T = typing.TypeVar("_T")


class DatasetDestination(Preprocessor[_T], abc.ABC):

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abc.abstractmethod
    def save(self, context: ImageContext) -> bool:
        raise NotImplementedError()
