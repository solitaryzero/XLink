from typing import Dict
import time
import datetime
import struct


class EntityHolder:
    id2info = dict()   # type: Dict[str, tuple]

    uri2id = dict()    # type: Dict[str, str]
    title2id = dict()  # type: Dict[str, str]

    _instance = None

    def __init__(self):
        raise SyntaxError("Entity Maps must be initialized by get_instance()")

    @classmethod
    def get_instance(cls, source: str, maps_path: str, force_load=False):
        if cls._instance is None or force_load:
            cls._instance = object.__new__(EntityHolder)
            cls._instance.init(source, maps_path)
        return cls._instance

    def init(self, source: str, maps_path: str):
        """
        :param source
        :param maps_path: <title>\t\t<sub_title>\t\t<uri_1::;uri_2::;...::;uri_n>\t\t<entity_id>
        :return:
        """
        print("Loading mapping relations of related entity information from file: \n\t{}".format(maps_path))
        start_at = int(time.time())
        valid_lines = 0
        with open(maps_path, "r", encoding="utf-8") as rf:
            for line in rf:
                line_arr = line.strip().split("\t\t")

                if len(line_arr) < 4: continue
                valid_lines += 1

                title, sub_title, uris, entity_id = line_arr

                uris_list = list()
                for uri in uris.split("::;"):
                    offset = 0
                    if source == 'bd': offset = 23
                    elif source == 'wiki': offset = 24
                    uris_list.append(uri[offset:])

                self.id2info[entity_id] = (title, sub_title, uris_list)
                for uri in uris_list:
                    self.uri2id[uri] = entity_id

                full_title = title + sub_title
                self.title2id[full_title] = entity_id
        print("Loaded, #valid line: {}, time consume: #{}".format(
            valid_lines, str(datetime.timedelta(seconds=int(time.time())-start_at))))
