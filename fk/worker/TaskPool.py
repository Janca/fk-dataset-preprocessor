import logging
import queue
import threading

from fk.image.ImageContext import ImageContext
from .ITaskPool import ITaskPool, Work
from .IWorkerManager import IWorkerManager
from .Task import Task


class TaskPool(ITaskPool):

    def __init__(self, worker_manager: IWorkerManager, task: Task, pool_size: int):
        self._worker_manager = worker_manager
        self._task = task
        self._pool_size = pool_size
        self._queue = queue.Queue[Work](pool_size * 100)
        self._workers: list[threading.Thread] = []
        self._idle_state: list[bool] = [True] * pool_size
        self.logger = logging.getLogger(self.__class__.__name__)

        for thread_idx in range(pool_size):
            worker_thread = threading.Thread(target=self._thread_fn, args=[thread_idx])
            worker_thread.start()

            self._workers.append(worker_thread)

    def _thread_fn(self, index: int):
        while not self.worker_manager.is_shutdown:
            self._idle_state[index] = True

            work = self.get_work()
            if work is None:
                continue

            self._idle_state[index] = False
            task_pool, context = work
            pool_task = task_pool.task

            for i in range(pool_task.max_attempts):
                try:
                    success = pool_task.process(context)

                    if success:
                        next_task_pool = self.worker_manager.get_next_task_pool(task_pool)

                        if not self.worker_manager.is_shutdown and next_task_pool is not None:
                            self.logger.debug(
                                f"Submitting from task '{task_pool.task.id()}' "
                                f"to task '{next_task_pool.task.id()}'"
                            )

                            next_task_pool.submit(context)

                        break

                except:
                    continue

    def submit(self, context: ImageContext):
        self.queue.put((self, context))

    def get_work(self) -> Work | None:
        try:
            return self.queue.get(block=True, timeout=0.25)

        except queue.Empty:
            return self.worker_manager.get_work(self)

    def steal_work(self) -> Work | None:
        try:
            return self.queue.get_nowait()

        except:
            return None

    @property
    def has_work(self) -> bool:
        return self.queue.qsize() > 0

    @property
    def is_idle(self) -> bool:
        return all(self._idle_state)

    @property
    def worker_manager(self):
        return self._worker_manager

    @property
    def task(self):
        return self._task

    @property
    def pool_size(self):
        return self._pool_size

    @property
    def queue(self):
        return self._queue
