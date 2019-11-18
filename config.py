import json
import os


local_config = json.load(open("./config.json", "r"))


class Config:
    data_root = local_config["data_path"]
    project_root = local_config["project_path"]

    @classmethod
    def get_file_full_path(cls, source, file_name):
        return os.path.join(cls.data_root, source, file_name)

    @classmethod
    def get_instance_id_path(cls, source):
        return cls.get_file_full_path(source, "instance_id.txt")

    @classmethod
    def get_entity_id_path(cls, source):
        return cls.get_file_full_path(source, "entity_id.txt")
