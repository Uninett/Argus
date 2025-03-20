import importlib
from typing import Collection


class AttrGetter:
    def __init__(self, attr_name: str):
        self.attr_name = attr_name

    def __call__(self, obj):
        return getattr(obj, self.attr_name)

    @property
    def query(self):
        return self.attr_name


class NestedAttrGetter(AttrGetter):
    def __init__(self, attr_name: str):
        super().__init__(attr_name)
        self._attr_names = attr_name.split(".")
        self._attr_query = "__".join(self._attr_names)

    def __call__(self, obj):
        obj_attr = obj
        for attr_name in self._attr_names:
            obj_attr = getattr(obj_attr, attr_name)
        return obj_attr

    @property
    def query(self):
        return self._attr_query


def import_class_from_dotted_path(dotted_path: str):
    module_name, class_name = dotted_path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    class_ = getattr(module, class_name)
    return class_


def collection_to_prose(collection: Collection):
    if not collection:
        return ""
    if len(collection) == 1:
        return str(collection[0])
    last = collection[-1]
    preceding = collection[:-1]
    prose = ", ".join(map(str, preceding)) + " and " + str(last)
    return prose
