#!/usr/bin/python
# -*- coding: utf-8 -*-
# created: 23 Oct 2012
# author: "Li Guo Peng" <roc.lee.80@gmail.com>

import json

from gcommon.utils import gobject, gstr


class JsonAttributeError(AttributeError):
    pass


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
        if name.find(".") == -1:
            self.__set_value(name, value)
        else:
            names = name.split(".", 1)
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
        if not isinstance(json_content, str):
            json_content = json_content.decode("utf-8")

        j = json.loads(json_content)
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
            msg = "Item:append - the old value is not list. Name: %s, Value: %s" % (
                name,
                value,
            )
            raise JsonAttributeError(msg)

        return self

    def copy_obj(self, obj, *names, enable_snake_to_camel=False, default=None):
        """从另一个对象拷贝指定名称的属性"""
        for name in names:
            if type(name) in (tuple, list):
                if len(name) == 3:
                    """(dest_name, source_name, default)"""
                    source_name = name[1] or name[0]
                    self[name[0]] = getattr(obj, source_name, name[2])
                elif len(name) == 2:
                    """(dest_name, source_name)"""
                    source_name = name[1] or name[0]
                    value = getattr(obj, source_name, None)
                    if value is not None:
                        self[name[0]] = value
            else:
                value = getattr(obj, name, None)
                if value is not None:
                    if enable_snake_to_camel:
                        name = gstr.snakeToCamel(name)

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


if __name__ == "__main__":
    user_def = {"name": "user123", "password": "123456", "values": {"a": 1, "b": 2}}

    user = JsonObject(user_def)
    print(user.name)
    print(user.password)
    print(user.email)

    user.email = "user123@localhost"
    print(user.email)
    print(user)

    user.email_verified = True
    print(user)

    user.props = {}
    user.props.sex = "male"
    user.props.age = 26
    print(user)

    user = JsonObject.loads(user.dumps())
    print(user, type(user))


class JsonField(object):
    """可转化成 Json 字段的属性"""

    def __init__(self, name="", default_value=None, *, validator=None, desc="", allow_blank=False):
        self.name = name
        self.default_value = default_value
        self.validator = validator
        self._desc = desc or name
        self.allow_blank = allow_blank

    @property
    def desc(self):
        return self._desc or self.name

    def set_name(self, name):
        self.name = name

    def field_to_json(self, value):
        return value


class IntegerJsonField(JsonField):
    def __init__(self, name="", default_value=None, *, validator=None, desc="", allow_blank=False):
        JsonField.__init__(
            self,
            name=name,
            default_value=default_value or 0,
            validator=validator,
            desc=desc,
            allow_blank=allow_blank,
        )


class JSONable(object):
    """可以进行 json 序列化和反序列化的对象"""

    object_description = ""
    _enable_snake_to_camel = True

    def to_json(self):
        """对象转换成 json"""
        result = JsonObject()

        fields = gobject.get_instances_of(JsonField, self.__class__)
        for field_name, field in fields:
            obj_value = getattr(self, field_name)
            if type(obj_value) == JsonField:
                # 采用默认值；如果名称没有设置，则采用 field_name
                if obj_value.allow_blank:
                    continue

                json_name = obj_value.name or field_name
                json_value = obj_value.default_value
            else:
                json_name = field.name or field_name
                json_value = obj_value

            if self._enable_snake_to_camel:
                json_name = gstr.snakeToCamel(json_name)

            if isinstance(json_value, JSONable):
                result[json_name] = json_value.to_json()
            elif json_value:
                result[json_name] = field.field_to_json(json_value)

        self._extra_json_fields(result)

        return result

    def _extra_json_fields(self, data: JsonObject):
        return

    def _load_extra_json_fields(self, data: dict):
        pass

    @classmethod
    def create(cls, **kwargs):
        return cls.load_dict(kwargs)

    @classmethod
    def load_json(cls, json_string):
        data = JsonObject.load_obj(json_string)
        return cls()._copy_from_dict(data)

    @classmethod
    def load_dict(cls, data: dict):
        return cls()._copy_from_dict(data)

    def _copy_from_dict(self, data: dict):
        fields = gobject.get_instances_of(JsonField, self.__class__)

        for field_name, field in fields:
            json_name = field_name if not self._enable_snake_to_camel else gstr.snakeToCamel(field_name)
            json_value = data.get(json_name, None)

            if json_value is None:
                json_value = field
            elif type(field) == JsonListField:
                json_value = [field.list_to_field(item) for item in json_value]
            elif isinstance(field, JSONable):
                json_value = field.load_dict(json_value)
            else:
                assert type(field) == JsonField
                json_value = json_value

            setattr(self, field_name, json_value)

        self._load_extra_json_fields(data)
        return self


class JsonObjectField(JsonField, JSONable):
    """复合对象，用于构造复杂的 json 字段，也可以作为独立对象使用"""

    def __init__(self, name="", *, validator=None, desc=""):
        JsonField.__init__(self, name, default_value="", validator=validator, desc=desc)


class JsonListField(JsonField):
    """复合对象，用于构造数组型 json 字段"""

    def __init__(self, name="", *, meta_class=None, validator=None, desc=""):
        JsonField.__init__(self, name, validator=validator, desc=desc)
        self.meta_class = meta_class

    def field_to_json(self, values: list):
        """转换 list 对象"""
        if self.meta_class:
            if isinstance(self.meta_class, JsonListField):
                # 嵌套列表
                return [self.meta_class.to_json(item) for item in values]
            elif issubclass(self.meta_class, JSONable):
                # Json 对象
                return [item.to_json() for item in values]
            else:
                # 转换函数
                return [self.meta_class(item) for item in values]
        else:
            # 基础对象，直接返回
            return values

    def list_to_field(self, values: list):
        if not values or not self.meta_class:
            return values

        if isinstance(self.meta_class, JsonListField):
            # 嵌套列表
            return [self.meta_class.list_to_field(item) for item in values]
        elif issubclass(self.meta_class, JSONable):
            # Json 对象
            return self.meta_class.load_dict(values)
        else:
            # 转换函数 -> Json 转换成对象
            return [self.meta_class(item) for item in values]
