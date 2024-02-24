import abc
import typing

_T = typing.TypeVar('_T')


class Preprocessor(typing.Generic[_T], abc.ABC):
    _preferences: _T

    def _load_preferences(self, preferences: _T, env: dict[str, any]) -> bool:
        self._preferences = preferences
        return self.load_preferences(preferences, env)

    def load_preferences(self, preferences: _T, env: dict[str, any]) -> bool:
        return True

    def initialize(self):
        pass

    @classmethod
    def name(cls):
        return cls.__name__

    @classmethod
    @abc.abstractmethod
    def id(cls):
        raise NotImplementedError()

    @property
    def preferences(self) -> _T:
        return self._preferences
