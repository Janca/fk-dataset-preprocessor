import abc
import enum
import inspect
import logging
import typing

from fk.common.Preprocessor import Preprocessor
from fk.image.ImageContext import ImageContext

_T = typing.TypeVar('_T')


class TaskType(enum.IntEnum):
    CPU = enum.auto()
    GPU = enum.auto()
    IO = enum.auto()


class Task(Preprocessor[_T], abc.ABC):

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._priority: int = 0

    def __lt__(self, other: typing.Any) -> bool:
        return self.priority > other.priority

    @abc.abstractmethod
    def process(self, context: ImageContext) -> bool:
        raise NotImplementedError()

    @property
    def max_attempts(self) -> int:
        return 1

    @property
    def pool_size(self) -> int:
        return -1

    @property
    @abc.abstractmethod
    def type(self) -> TaskType:
        raise NotImplementedError()

    @property
    def max_ipm(self) -> int:
        return -1

    @property
    def priority(self):
        return self._priority

    @classmethod
    def preferences_cls(cls) -> typing.Type | None:
        return None

    @classmethod
    def print_preferences_docs(cls):
        pref_cls = cls.preferences_cls()
        if pref_cls is None:
            return

        doc_str = inspect.getdoc(pref_cls)
        if doc_str is None:
            return

        print(doc_str)
