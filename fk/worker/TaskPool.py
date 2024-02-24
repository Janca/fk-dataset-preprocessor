import logging
import queue
import threading
import time

from fk.image.ImageContext import ImageContext
from .ITaskPool import ITaskPool, Work
from .IWorkerManager import IWorkerManager
from .Task import Task


class TaskPool(ITaskPool):

    def __init__(self, worker_manager: IWorkerManager, task: Task, pool_size: int):
        self._worker_manager = worker_manager
        self._task = task
        self._pool_size = pool_size
        self._queue = queue.Queue[Work](min(max(16, pool_size * 10), 1024))
        self._workers: list[threading.Thread] = []
        self._idle_state: list[bool] = [True] * pool_size

        self._processed_images: int = 0
        self._rejected_images: int = 0

        self._first_task_systime: float = -1

        self.logger = logging.getLogger(f"Pool-{task.__class__.__name__}")

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

            if task_pool.first_task_systime == -1:
                task_pool.first_task_systime = time.time()

            if pool_task.max_ipm > 0:
                delta_time_seconds = time.time() - task_pool.first_task_systime
                if delta_time_seconds > 0 and task_pool.processed_images > 0:
                    images_per_minute = (task_pool.processed_images / delta_time_seconds) * 60.0

                    if pool_task.max_ipm < images_per_minute:
                        task_pool.submit(context)
                        continue

            success = False
            for i in range(pool_task.max_attempts):
                try:
                    success = pool_task.process(context)
                    task_pool.increment_processed()

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

            if not success:
                task_pool.increment_rejected()

            task_pool.task_done()

    def submit(self, context: ImageContext):
        self.queue.put((self, context))

    def task_done(self):
        self.queue.task_done()

    def get_work(self) -> Work | None:
        try:
            return self.queue.get(block=True, timeout=1.25)

        except queue.Empty:
            return self.worker_manager.get_work(self)

    def steal_work(self) -> Work | None:
        try:
            return self.queue.get_nowait()

        except:
            return None

    def increment_processed(self):
        self._processed_images += 1

    def increment_rejected(self):
        self._rejected_images += 1

    @property
    def processed_images(self) -> int:
        return self._processed_images

    @property
    def rejected_images(self) -> int:
        return self._rejected_images

    @property
    def first_task_systime(self) -> float:
        return self._first_task_systime

    @first_task_systime.setter
    def first_task_systime(self, value: float):
        self._first_task_systime = value

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
