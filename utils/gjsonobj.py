#!/usr/bin/python
# -*- coding: utf-8 -*- 
# created: 23 Oct 2012
# author: "Li Guo Peng" <roc.lee.80@gmail.com>

import json
import sys

from gcommon.utils import gobject


class JsonAttributeError(AttributeError): pass


class JsonObject(dict):
    def __init__(self, d=None):
        if not d:
            d = {}

        dict.__init__(self, d)

        for key, value in self.items():
            if isinstance(value, dict):
                self[key] = JsonObject(value)
            elif isinstance(value, list):
                for i in range(len(value)):
                    item = value[i]
                    if isinstance(item, dict):
                        value[i] = JsonObject(item)

    def __getattr__(self, name):
        # __getattr__ is called after __getattribute__
        return self.get(name, None)

    def __setattr__(self, name, value):
        if name.find('.') == -1:
            self.__set_value(name, value)
        else:
            names = name.split('.', 1)
            child = self.get(names[0], None)

            if child is None:
                child = JsonObject()
                self[names[0]] = child

            setattr(child, names[1], value)

    def __set_value(self, name, value):
        if type(value) == JsonObject:
            self[name] = value
        elif type(value) == dict:
            self[name] = JsonObject(value)
        else:
            self[name] = value

    def __hash__(self):
        return id(self)

    @staticmethod
    def loads(json_content):
        if isinstance(json_content, str):
            return JsonObject(json.loads(json_content))
        else:
            j = json.loads(json_content.decode('utf-8'))
            if isinstance(j, list):
                result = []
                for item in j:
                    result.append(JsonObject(item))
                return result
            else:
                return JsonObject(j)

    @staticmethod
    def load_obj(obj, *names):
        return JsonObject({name: getattr(obj, name) for name in names})

    def dumps(self, indent=None, ensure_ascii=True, sort_keys=False):
        result = json.dumps(self, ensure_ascii=ensure_ascii, indent=indent, sort_keys=False)

        # if isinstance(result, str):
        #    result = result.encode('utf-8')

        return result

    def append(self, name, value):
        """Append an element to a list attr."""
        old = getattr(self, name)
        if isinstance(old, list):
            old.append(value)
        elif not old:
            setattr(self, name, [value])
        else:
            msg = 'Item:append - the old value is not list. Name: %s, Value: %s' % (name, value)
            raise JsonAttributeError(msg)

        return self

    def copy_obj(self, obj, *names, default=None):
        """从另一个对象拷贝指定名称的属性"""
        for name in names:
            if type(name) in (tuple, list):
                """(dest_name, source_name, default)"""
                if len(name) == 3:
                    source_name = name[1] or name[0]
                    self[name[0]] = getattr(obj, source_name, name[2])
                elif len(name) == 2:
                    source_name = name[1] or name[0]
                    value = getattr(obj, source_name, None)
                    if value is not None:
                        self[name[0]] = value
            else:
                value = getattr(obj, name, None)
                if value is not None:
                    self[name] = value

        return self

    @staticmethod
    def clone_obj(obj, *names, default=None):
        """创建 json 对象，从另一个对象拷贝指定名称的属性"""
        json_obj = JsonObject()
        for name in names:
            if type(name) in (tuple, list):
                if len(name) == 3:
                    json_obj[name[0]] = getattr(obj, name[1], name[2])
                elif len(name) == 2:
                    value = getattr(obj, name[1], None)
                    if value is not None:
                        json_obj[name[0]] = value
            else:
                value = getattr(obj, name, None)
                if value is not None:
                    json_obj[name] = value

        return json_obj


if __name__ == '__main__':
    user_def = {'name': 'user123', 'password': '123456',
                "values": {"a": 1, "b": 2}}

    user = JsonObject(user_def)
    print(user.name)
    print(user.password)
    print(user.email)

    user.email = 'user123@localhost'
    print(user.email)
    print(user)

    user.email_verified = True
    print(user)

    user.props = {}
    user.props.sex = 'male'
    user.props.age = 26
    print(user)

    user = JsonObject.loads(user.dumps())
    print(user, type(user))


class JsonField(object):
    def __init__(self, name, value=""):
        self.name = name
        self.value = value


class JSONable(object):
    """可以进行 json 序列化和反序列化的对象"""
    def to_json(self):
        """对象转换成 json """
        result = JsonObject()

        fields = gobject.get_instances_of(JsonField, self.__class__)
        for name, value in fields:
            obj_value = getattr(self, name)
            if type(obj_value) == JsonField:
                json_name = obj_value.name
                json_value = obj_value.value
            else:
                json_name = value.name
                json_value = obj_value

            if json_value != "":
                result[json_name] = json_value

        self._extra_json_fields(result)

        return result

    def _extra_json_fields(self, data: JsonObject):
        return

    @classmethod
    def create(cls):
        return cls.load_dict({})

    @classmethod
    def load_json(cls, json_string):
        data = JsonObject.load_obj(json_string)
        return cls()._copy_from_dict(data)

    @classmethod
    def load_dict(cls, data: dict):
        return cls()._copy_from_dict(data)

    def _copy_from_dict(self, data: dict):
        fields = gobject.get_instances_of(JsonField, self.__class__)

        for name, value in fields:
            new_value = data.get(name, None)
            if new_value is None:
                new_value = value

            setattr(self, name, new_value)

        return self
