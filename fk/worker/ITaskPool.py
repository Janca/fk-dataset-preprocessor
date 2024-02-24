import abc

from fk.image.ImageContext import ImageContext
from .Task import Task

Work = tuple['ITaskPool', ImageContext]


class ITaskPool(abc.ABC):

    def submit(self, context: ImageContext):
        raise NotImplementedError()

    @abc.abstractmethod
    def task_done(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def steal_work(self) -> Work | None:
        raise NotImplementedError()

    @abc.abstractmethod
    def increment_processed(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def increment_rejected(self):
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def rejected_images(self) -> int:
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def processed_images(self) -> int:
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def first_task_systime(self) -> float:
        raise NotImplementedError()

    @first_task_systime.setter
    @abc.abstractmethod
    def first_task_systime(self, value: float):
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
