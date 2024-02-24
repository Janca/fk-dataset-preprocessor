import logging
import queue
import threading
import time
import traceback
import typing
from collections import defaultdict

from fk.image.ImageContext import ImageContext
from fk.task.Task import Task, TaskType

_DEFAULT_CPU_WORKERS = 24
_DEFAULT_GPU_WORKERS = 1

Work = tuple[Task, ImageContext]


class WorkerManagerPreferences(typing.TypedDict, total=False):
    cpu_workers: int
    gpu_workers: int


class WorkerManager:

    def __init__(self, preferences: WorkerManagerPreferences):
        self.logger = logging.getLogger(self.__class__.__name__)

        self.max_cpu_workers = preferences.get('cpu_workers', _DEFAULT_CPU_WORKERS)
        self.max_gpu_workers = preferences.get('gpu_workers', _DEFAULT_GPU_WORKERS)

        self._shutdown = False
        self._started = False

        self.cpu_queue = queue.LifoQueue[Work]()
        self.gpu_queue = queue.Queue[Work]()

        self.cpu_worker_threads: list[threading.Thread] = []
        self.cpu_worker_idle_states: list[bool] = [True] * self.max_cpu_workers

        self.gpu_worker_threads: list[threading.Thread] = []
        self.gpu_worker_idle_states: list[bool] = [True] * self.max_gpu_workers

        self.task_ipms: dict[str, tuple[int, float]] = defaultdict(lambda: (0, time.time()))

    def _queue_worker_fn(self, index: int, _type: TaskType, _queue: queue.Queue[Work]):
        while not self._shutdown:
            try:
                self.set_idle_state(index, _type, True)

                task, context = _queue.get_nowait()
                self.set_idle_state(index, _type, False)

                task_ipm = task.max_ipm
                item_count, first_task_time = self.task_ipms[task.id()]

                if task_ipm != -1:
                    delta_time_seconds = time.time() - first_task_time
                    if delta_time_seconds > 0 and item_count > 0:
                        ips = item_count / delta_time_seconds
                        ipm = ips * 60

                        if ipm > task.max_ipm:
                            self.logger.debug(
                                f"Rescheduling task '{task.id()}' - above images per minute threshold. "
                                f"[{ipm} > {task.max_ipm}]"
                            )

                            self.submit((task, context))
                            _queue.task_done()
                            continue

                self.task_ipms[task.id()] = (item_count + 1, first_task_time)
                max_attempts = task.max_attempts

                for i in range(max_attempts):
                    try:

                        success = task.process(context)

                        if success:
                            next_task = task.next_task

                            if not self._shutdown and next_task is not None:
                                self.logger.debug(f"Submitting from task '{task.id()}' to task '{next_task.id()}'")
                                self.submit((next_task, context))

                            # else:
                            #     self.logger.info(f"Task '{task.id()}' rejected an image.")

                            break

                    except Exception as e:
                        traceback.print_exception(e)
                        continue

                _queue.task_done()

            except queue.Empty:
                continue

        task_type = 'CPU' if _type == TaskType.CPU else 'GPU'
        self.logger.info(f'Thread:{task_type}:{index} complete.')

    def set_idle_state(self, index: int, _type: TaskType, idle: bool):
        if _type == TaskType.CPU:
            self.cpu_worker_idle_states[index] = idle
        elif _type == TaskType.GPU:
            self.gpu_worker_idle_states[index] = idle

    def start(self):
        self.logger.info(f"Starting {self.max_cpu_workers} CPU workers.")
        for i in range(self.max_cpu_workers):
            cpu_thread = threading.Thread(target=self._queue_worker_fn, args=[i, TaskType.CPU, self.cpu_queue])
            cpu_thread.start()

            self.cpu_worker_threads.append(cpu_thread)

        self.logger.info(f"Starting {self.max_gpu_workers} GPU workers.")
        for i in range(self.max_gpu_workers):
            gpu_thread = threading.Thread(target=self._queue_worker_fn, args=[i, TaskType.GPU, self.gpu_queue])
            gpu_thread.start()

            self.gpu_worker_threads.append(gpu_thread)

    def shutdown(self):
        self._shutdown = True

    def submit(self, work: Work):
        task, context = work

        if task.type == TaskType.CPU:
            self.cpu_queue.put((task, context))
        elif task.type == TaskType.GPU:
            self.gpu_queue.put((task, context))

        else:
            raise RuntimeError(f"Unknown task type '{task.id()}' for task '{task.id()}'.")

    def active(self) -> bool:
        return not all(self.cpu_worker_idle_states) \
            or not all(self.gpu_worker_idle_states) \
            or not self.cpu_queue.empty() \
            or not self.gpu_queue.empty()
