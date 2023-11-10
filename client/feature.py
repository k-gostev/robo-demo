import yaml


class Feature:
    def __init__(self, name, namespace_id, properties):
        self.__name__ = name
        self.__namespace_id__ = namespace_id
        self.__properties__ = properties
        self.__change_handler__ = None

    def get_name(self):
        return self.__name__

    def get_namespace_id(self):
        return self.__namespace_id__

    def get_properties(self):
        return self.__properties__

    def set_properties(self, properties):
        self.__properties__ = properties
        self.__change_handler__.on_properties_change(properties)

    def set_change_handler(self, change_handler):
        self.__change_handler__ = change_handler


def from_yaml(file):
    with open(file) as f:
        data_map = yaml.safe_load(f)
        print(data_map)
        return Feature(name=data_map['name'], namespace_id=data_map['namespaceID'], properties=data_map['properties'])
