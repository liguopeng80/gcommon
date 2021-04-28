# -*- coding: utf-8 -*-

# Utility for objects management.

import inspect


class ObjectWithLogger(object):
    logger = None

    @classmethod
    def set_class_logger(cls, logger):
        cls.logger = logger

    def set_logger(self, logger):
        self.logger = logger


def copy_attributes(src, dest, *attributes):
    """Shallow copy attributes from src-obj to dest-obj."""
    for attr in attributes:
        value = getattr(src, attr)
        setattr(dest, attr, value)


def clone_object(src, dest):
    """Shallow copy all public attributes from src-obj to dest-obj,
    but doesn't change the type of src-obj.

    This should only be used on POD objects.
    """
    for attr in dir(src):
        if attr.startswith("_"):
            continue

        # "getattr" may involve code execution
        value = getattr(src, attr)

        if inspect.ismethod(value):
            continue

        dest[attr] = value
