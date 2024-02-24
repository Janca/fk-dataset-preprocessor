import inspect
import logging
import os
import textwrap
import time
import traceback
import typing

import fk.io
import fk.task
import fk.utils.modules
import fk.utils.time
from fk.image.ImageContext import ImageContext
from fk.task.Task import TaskType
from fk.worker.WorkerManager import WorkerManager, WorkerManagerPreferences

Preferences = dict[str, any]
_T = typing.TypeVar('_T')


class DatasetDestinationTaskWrapper(fk.task.Task):

    def __init__(self, *destination: fk.io.DatasetDestination):
        super().__init__()
        self.destination = destination

    def process(self, context: ImageContext) -> bool:
        success = []
        for destination in self.destination:
            try:
                _success = destination.save(context)
                success.append(_success)

            except Exception as e:
                exc_str = textwrap.indent('\n'.join(traceback.format_exception_only(e)), '  ')
                destination.logger.error(f"Exception thrown when saving image.\n{exc_str}")

        context.close()
        return all(success)

    @classmethod
    def id(cls) -> str:
        return 'fk:wrapper:destination'

    @property
    def type(self) -> TaskType:
        return TaskType.CPU


class DatasetPreprocessorPreferences(typing.TypedDict, total=False):
    log_level: int

    workers: WorkerManagerPreferences

    input: Preferences
    output: Preferences

    env: dict[str, any]

    tasks: Preferences
    suppress_invalid_keys: bool | None


class DatasetPreprocessor:

    def __init__(self, preferences: DatasetPreprocessorPreferences):
        self.preferences = preferences

        log_level = preferences.get('log_level', logging.INFO)
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S'
        )

        self._task_map: dict[str, fk.task.Task] = {}
        self._source_map: dict[str, fk.io.DatasetSource] = {}
        self._destination_map: dict[str, fk.io.DatasetDestination] = {}
        self._destination_wrapper: fk.task.Task | None = None

        worker_manager_preferences = preferences.get('workers', {})
        self._worker_manager = WorkerManager(worker_manager_preferences)

        self._shutdown = False
        self.logger = logging.getLogger(self.__class__.__name__)

    def register_tasks(self, package: str):
        self.logger.info(f"Registering tasks from '{package}'.")

        loaded_classes: list[type[fk.task.Task]] = self._load_modules_and_classes(package)
        task_classes: dict[str, type[fk.task.Task]] = {}

        for task_class in loaded_classes:
            if issubclass(task_class, fk.task.Task):
                task_id = task_class.id()
                self.logger.debug(f"Found task with id '{task_id}'.")
                task_classes[task_id] = task_class

        tasks = self.preferences['tasks']
        for task_id, task_preferences in tasks.items():
            if task_id in self._task_map:
                raise ValueError(f"Task with id '{task_id}' already registered.")

            if task_id not in task_classes:
                if self.preferences.get('suppress_invalid_keys', False):
                    self.logger.warning(f"Task preferences references invalid task with id '{task_id}'.")
                    continue

                raise ValueError(f"Task with id '{task_id}' not found.")

            task_class = task_classes[task_id]
            task_inst = task_class()

            self.register_task(task_inst, task_preferences)

    def register_task(self, task: fk.task.Task, preferences: Preferences = None):
        task_id = task.id()
        task_name = task.name()

        if task_id in self._task_map:
            raise ValueError(f"Task with id '{task_id}' already registered")

        if preferences is None:
            preferences = self.get_task_preferences(task_id)

        if not task.load_preferences(preferences, self.env):
            self.logger.warning(f"Task with id '{task_id}' failed to load.")
            raise RuntimeError(f"Task with id '{task_id}' failed to load.")

        registered_tasks = self.tasks
        if len(registered_tasks) > 0:
            last_task = registered_tasks[-1]
            # noinspection PyProtectedMember
            last_task_next_task = last_task._next
            if last_task_next_task is not None:
                raise RuntimeError(
                    f"Task '{task_name}' already has next task "
                    f"registered as '{last_task_next_task.name()}'."
                )

            else:
                last_task._next = task

        task._work_pool = self
        self._task_map[task_id] = task
        self.logger.info(f"Registered task with id '{task_id}'.")

    def register_io(self, package: str):
        self.register_sources(package)
        self.register_destinations(package)

    def register_sources(self, package: str):
        self.logger.info(f"Registering sources from package '{package}'.")

        loaded_classes: list[type[fk.io.DatasetSource]] = self._load_modules_and_classes(package)
        source_classes: dict[str, type[fk.io.DatasetSource]] = {}

        for source_class in loaded_classes:
            if inspect.isabstract(source_class):
                continue

            if source_class != fk.io.DatasetSource and issubclass(source_class, fk.io.DatasetSource):
                source_id = source_class.id()
                self.logger.debug(f"Found source with id '{source_id}'.")
                source_classes[source_id] = source_class

        sources = self.preferences['input']
        for source_id, source_preferences in sources.items():
            if source_id in self._source_map:
                raise ValueError(f"Source with id '{source_id}' already registered.")

            if source_id not in source_classes:
                if self.preferences.get('suppress_invalid_keys', False):
                    self.logger.warning(f"Source preferences references invalid source with id '{source_id}'.")
                    continue

                raise ValueError(f"Source with id '{source_id}' not found.")

            source_class = source_classes[source_id]
            source_inst = source_class()

            self.register_source(source_inst, source_preferences)

    def register_source(self, source: fk.io.DatasetSource, preferences: Preferences):
        source_id = source.id()
        if source_id in self._source_map:
            raise ValueError(f"Source with id '{source_id}' is already registered.")

        if preferences is None:
            preferences = self.get_source_preferences(source_id)

        if not source.load_preferences(preferences, self.env):
            self.logger.fatal(f"Source with id '{source_id}' failed to load.")
            raise IOError(f"Source with id '{source_id}' failed to load.")

        self._source_map[source_id] = source
        self.logger.info(f"Registered source with id '{source_id}'.")

    def register_destinations(self, package: str):
        self.logger.info(f"Registering destinations from package '{package}'.")

        loaded_classes: list[type[fk.io.DatasetDestination]] = self._load_modules_and_classes(package)
        destination_classes: dict[str, type[fk.io.DatasetDestination]] = {}

        for dest_class in loaded_classes:
            if inspect.isabstract(dest_class):
                continue

            if dest_class != fk.io.DatasetDestination and issubclass(dest_class, fk.io.DatasetDestination):
                dest_id = dest_class.id()
                self.logger.debug(f"Found destination with id '{dest_id}'.")
                destination_classes[dest_id] = dest_class

        destinations = self.preferences['output']
        for dest_id, source_preferences in destinations.items():
            if dest_id in self._source_map:
                raise ValueError(f"Destination with id '{dest_id}' already registered.")

            if dest_id not in destination_classes:
                if self.preferences.get('suppress_invalid_keys', False):
                    self.logger.warning(f"Destination preferences references invalid destination with id '{dest_id}'.")
                    continue

                raise ValueError(f"Destination with id '{dest_id}' not found.")

            dest_class = destination_classes[dest_id]
            dest_inst = dest_class()

            self.register_destination(dest_inst, source_preferences)

    def register_destination(self, destination: fk.io.DatasetDestination, preferences: Preferences):
        destination_id = destination.id()
        if destination_id in self._destination_map:
            raise ValueError(f"Destination with id '{destination_id}' is already registered.")

        if preferences is None:
            preferences = self.get_destination_preferences(destination_id)

        if not destination.load_preferences(preferences, self.env):
            self.logger.fatal(f"Destination with id '{destination_id}' failed to load.")
            raise IOError(f"Destination with id '{destination_id}' failed to load.")

        self._destination_map[destination_id] = destination
        self.logger.info(f"Registered destination with id '{destination_id}'.")

    def get_task_preferences(self, task_id: str) -> typing.Optional[Preferences]:
        task_preferences = self.preferences.get('tasks', None)
        if task_preferences is None:
            return None

        return task_preferences.get(task_id, {})

    def get_source_preferences(self, source_id: str) -> typing.Optional[Preferences]:
        source_preferences = self.preferences.get('input', None)
        if source_preferences is None:
            return None

        return source_preferences.get(source_id, {})

    def get_destination_preferences(self, destination_id: str) -> typing.Optional[Preferences]:
        destination_preferences = self.preferences.get('output', None)
        if destination_preferences is None:
            return None

        return destination_preferences.get(destination_id, {})

    def start(self):
        tasks = self.tasks
        tasks_length = len(self.tasks)

        if tasks_length == 0:
            raise RuntimeError('No tasks configured.')

        first_task = tasks[0]
        last_task = tasks[-1]

        sources = list(self._source_map.values())
        destinations = list(self._destination_map.values())

        destination_task_wrapper = DatasetDestinationTaskWrapper(*destinations)
        self._destination_wrapper = destination_task_wrapper

        self.logger.info(f"Appending destination task wrapper to task with id '{last_task.id()}'.")
        last_task._next = destination_task_wrapper

        self.logger.info('Initializing tasks...')

        for source in sources:
            source.initialize()

        for task in tasks:
            task.initialize()

        for destination in destinations:
            destination.initialize()

        items = 0
        start_time = time.time()

        self.logger.info("Starting worker threads...")
        self._worker_manager.start()

        self.logger.info("Processing sources...")

        try:
            for source_id, source in self._source_map.items():
                self.logger.info(f"Processing source with id '{source_id}'.")
                for image_loader in source.next():
                    image_context = ImageContext(image_loader)
                    self._worker_manager.submit((first_task, image_context))

                    items += 1
                    if items % 100 == 0:
                        time.sleep(0.25)

            self.logger.info("Completed processing sources.")
            self.logger.info('Waiting for tasks to complete...')

            while not self._shutdown:
                if not self._worker_manager.active():
                    break

                time.sleep(0.25)

        except (KeyboardInterrupt, InterruptedError):
            self.logger.info("Interrupted processing, shutting down...")
            self._shutdown = True

        end_time = time.time()
        delta_time = end_time - start_time
        items_per_second = items / delta_time

        delta_time_str = fk.utils.time.format_timedelta(start_time, end_time)

        self.logger.info(f'Completed in {delta_time_str}')
        self.logger.info(f'Processed {items} images @ {items_per_second:0.2f}/s')

        self.shutdown()
        self.report()

    def shutdown(self):
        self._shutdown = True
        self._worker_manager.shutdown()

    @property
    def tasks(self) -> list[fk.task.Task]:
        return list(self._task_map.values())

    @property
    def env(self) -> dict[str, any]:
        return self.preferences.get('env', {})

    def report(self):
        report_str = 'Task Report:\n'

        for task in self.tasks:
            report_str += f'{task.name()}\n'
            report_str += f'  {task.id()}\n'
            report_str += ('-' * 48) + '\n'

        self.logger.info(report_str)

    @classmethod
    def _load_modules_and_classes(cls, package: str) -> list[type[_T]]:
        working_filepath = os.path.realpath(__file__)
        working_dirpath = os.path.dirname(working_filepath)
        package_path = os.path.join(*[p for p in package.split('.')])
        working_dirname = os.path.basename(working_dirpath)

        common_prefix = os.path.commonprefix([working_dirname, package_path])
        if common_prefix:
            package_path = package_path.split(common_prefix + os.path.sep)[1]

        package_filepath = os.path.join(working_dirpath, str(package_path))
        _, loaded_classes = fk.utils.modules.load_modules_and_classes_from_directory(package_filepath)

        return loaded_classes