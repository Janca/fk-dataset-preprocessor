import abc

from .ITaskPool import ITaskPool, Work


class IWorkerManager(abc.ABC):

    def get_next_task_pool(self, task_pool: ITaskPool) -> ITaskPool | None:
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def is_shutdown(self) -> bool:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_work(self, worker: ITaskPool) -> Work | None:
        raise NotImplementedError()
