# -*- coding: utf-8 -*-

# Utility for objects management.

import inspect
import uuid

from gcommon.utils import grand


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


def copy_attributes_with_new_name(src_obj, dest_obj, *attributes):
    """Shallow copy attributes from src-obj to dest-obj."""
    for item in attributes:
        convertor = None
        if type(item) in (list, tuple):
            if len(item) == 3:
                name, new_name, convertor = item
            elif len(item) == 2:
                name, new_name = item
            else:
                assert False
        else:
            name = new_name = item

        value = getattr(src_obj, name)
        if convertor:
            value = convertor(value)

        setattr(dest_obj, new_name, value)


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


class Entity(object):
    """具有唯一 ID 的实体对象"""
    def __init__(self, uid=""):
        self.uid = uid or grand.uuid_string()


def get_subclasses(base_class, context, func_get_name=None, allow_base=False):
    """注册某个上下文中的所有子类"""
    if inspect.ismodule(context):
        names = dir(context)
        context = {k: getattr(context, k) for k in names}

    subclasses = []
    for name, value in context.items():
        if inspect.isclass(value) and issubclass(value, base_class):
            if not allow_base and (value == base_class):
                continue

            if func_get_name:
                name = func_get_name(value)
            subclasses.append(value)

    return subclasses
