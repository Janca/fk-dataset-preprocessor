import importlib
import inspect
import os
import sys
import warnings


def _load_modules_from_directory(directory, parent_package=None):
    """
    Method provided by Google Bard <3
    :param directory:
    :param parent_package:
    :return:
    """
    modules = []

    directory_path = os.path.abspath(directory)
    if directory_path not in sys.path:
        sys.path.append(directory_path)

    for entry in os.listdir(directory):
        entry_path = os.path.join(directory, entry)

        if os.path.isfile(entry_path) and entry.endswith(".py") and not entry.startswith("__"):
            module_name = entry[:-3]

            if parent_package:
                full_module_name = f"{parent_package}.{module_name}"
            else:
                full_module_name = module_name

            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=DeprecationWarning)
                module = importlib.import_module(full_module_name)
                modules.append(module)

        elif os.path.isdir(entry_path) and os.path.isfile(os.path.join(entry_path, "__init__.py")):
            package_name = entry
            if parent_package:
                full_package_name = f"{parent_package}.{package_name}"
            else:
                full_package_name = package_name

            sub_modules = _load_modules_from_directory(entry_path, full_package_name)
            modules.extend(sub_modules)

    return modules


def get_classes_from_module(module):
    """
    Method provided by Google Bard
    :param module:
    :return:
    """
    classes = []

    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and obj.__module__ == module.__name__ and not name[0] == "_":
            classes.append(obj)

    return classes


def load_modules_and_classes_from_directory(directory, parent_package=None):
    """
    Method provided by Google Bard
    :param directory:
    :param parent_package:
    :return:
    """
    modules = _load_modules_from_directory(directory, parent_package)
    classes = []

    for module in modules:
        module_classes = get_classes_from_module(module)
        classes.extend(module_classes)

    return modules, classes
