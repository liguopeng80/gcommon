# -*- coding: utf-8 -*-

# Utility for objects management.

import inspect
import logging

from gcommon.utils import grand


class ObjectWithLogger(object):
    logger = None
    _logger_name = ""

    @classmethod
    def set_class_logger(cls, logger=None):
        """为类设置 logger"""
        if not logger:
            logger = logging.getLogger(cls._logger_name or cls.__name__)

        cls.logger = logger

    def set_logger(self, logger=None):
        """为对象设置 logger"""
        if not logger:
            name = getattr(self, "_logger_name", self.__class__.__name__)
            logger = logging.getLogger(name)

        self.logger = logger

    def set_logger_by_name(self, logger_name):
        logger = logging.getLogger(logger_name)
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

    uid = ""
    _HAS_UID = True

    def __init__(self, uid=""):
        if self._HAS_UID:
            self.uid = uid or grand.uuid_string()
        else:
            self.uid = uid


class EntityManager(object):
    def __init__(self):
        self._entities: {str: Entity} = {}

    def __bool__(self):
        return len(self._entities) > 0

    def __len__(self):
        return len(self._entities)

    def put(self, entity: Entity):
        self._entities[entity.uid] = entity

    def get(self, uid):
        return self._entities.get(uid, None)

    def find(self, key) -> Entity:
        """根据查找函数查找 entity"""
        for entity in self._entities.values():
            if key(entity):
                return entity

        return None

    def remove(self, entity: Entity):
        return self.remove_by_uid(entity.uid)

    def remove_by_uid(self, uid):
        if uid in self._entities:
            return self._entities.pop(uid)

    def items(self, key=None) -> [Entity]:
        entities = list(self._entities.values())
        if key:
            entities.sort(key=key)

        return entities

    def transfer_to(self, other, uid):
        entity = self.get(uid)
        if entity:
            self.remove_by_uid(uid)
            other.put(entity)

    def take_from(self, other, uid):
        entity = other.get(uid)
        if entity:
            other.remove_by_uid(uid)
            self.put(entity)

    @staticmethod
    def find_in_managers(uid, *managers):
        """聚合查询"""
        for manager in managers:
            entity = manager.get(uid)
            if entity:
                return entity


def get_subclasses(base_class, context, func_get_name=None, allow_base=False):
    """注册某个上下文中的所有子类"""
    if inspect.ismodule(context):
        names = dir(context)
        context = {k: getattr(context, k) for k in names}

    subclasses = []
    for name, value in context.items():
        if inspect.isclass(value) and issubclass(value, base_class):
            if not allow_base and (value == base_class):
                # ignore base class
                continue

            if func_get_name:
                # todo: user can register the class with a different name
                func_get_name(value)

            subclasses.append(value)

    return subclasses


def get_instances_of(cls, context):
    """从 context 中获取所有类型为 cls 的实例"""
    if type(context) is not dict:
        names = dir(context)
        context = {k: getattr(context, k) for k in names}

    objects = []
    for name, value in context.items():
        value_type = type(value)
        if inspect.isclass(value_type) and issubclass(value_type, cls):
            objects.append((name, value))

    return objects


def ensure_enum(value, cls):
    """确保返回值是对应的 class 对象"""
    if type(value) == cls:
        return value

    return cls(value)
