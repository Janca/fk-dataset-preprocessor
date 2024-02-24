import abc

from fk.image.ImageContext import ImageContext
from .Task import Task


Work = tuple['ITaskPool', ImageContext]

class ITaskPool(abc.ABC):

    def submit(self, context: ImageContext):
        raise NotImplementedError()

    @abc.abstractmethod
    def steal_work(self) -> Work | None:
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def has_work(self) -> bool:
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def is_idle(self) -> bool:
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def task(self) -> Task:
        raise NotImplementedError()
