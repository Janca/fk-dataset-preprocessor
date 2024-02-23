import abc
import typing

_T = typing.TypeVar('_T')


class Preprocessor(typing.Generic[_T], abc.ABC):

    def initialize(self, env: dict[str, any] = None):
        pass

    def load_preferences(self, preferences: _T) -> bool:
        return True

    @classmethod
    def name(cls):
        return cls.__name__

    @classmethod
    @abc.abstractmethod
    def id(cls):
        raise NotImplementedError()
