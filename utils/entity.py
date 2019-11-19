import os
import json
from typing import Dict
import time
import datetime


class EntityMaps:
    id2info = dict()   # type: Dict[str, tuple]

    uri2id = dict()    # type: Dict[str, str]
    title2id = dict()  # type: Dict[str, str]

    _instance = None

    def __init__(self):
        raise SyntaxError("Entity Maps mus be initialized by get_instance()")

    @classmethod
    def get_instance(cls, source: str, maps_path: str, force_load=False):
        if cls._instance is None or force_load:
            cls._instance = object.__new__(EntityMaps)
            cls._instance.init(source, maps_path)
        return cls._instance

    def init(self, source: str, maps_path: str):
        """
        :param source
        :param maps_path: <title>\t\t<sub_title>\t\t<uri1::;uri2::;...::;urin>\t\t<entity_id>
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


class EntityHolder:
    """
    加载实体相关信息并保存
        1. url -> id （only useful for `bd` source）
        2. id -> main_title  (inst_id2label)
        3. "title subtitle" -> id  (inst_label2id)
        4. main_title -> ids  (inst_mention2id)
    """

    _bd_instance = None
    _wiki_instance = None

    source = None

    inst_url2id     = None
    inst_id2label   = None
    inst_label2id   = None
    inst_mention2id = None
    inst_id2title   = None
    inst_id2uri     = None

    valid_entities  = None

    ambiguous_lowertitle2ids = None  # For data when `source` = "wiki".

    def __init__(self):
        raise SyntaxError("Entity can be initialized by __init__, please use get_instance()")

    @classmethod
    def get_instance(cls, source):
        if source == 'bd':
            if cls._bd_instance is None:
                cls._bd_instance = object.__new__(EntityHolder)
                cls._bd_instance.init(source)
            return cls._bd_instance
        if source == 'wiki':
            if cls._wiki_instance is None:
                cls._wiki_instance = object.__new__(EntityHolder)
                cls._wiki_instance.init(source)
            return cls._wiki_instance
        raise TypeError("The argument `source` should be `wiki` or `bd`")

    def init(self, source):
        """
        1. Loads the mapping relation from url to instance_id
        2. Loads the mapping relation from instance_id to instance_label

        :param source:  bd | wiki
        :return: url2id, id2label. Both are dicts
        """
        self.source = source
        self.inst_url2id, self.inst_id2label, self.inst_label2id, self.inst_mention2id, self.inst_id2title, self.inst_id2uri = self.load_inst_url_2_id()
        self.load_valid_entities()
        if source == 'wiki':
            self.ambiguous_lowertitle2ids = json.load(
                open("./data/wiki/ambiguous_lower_title_to_ids.json", "r", encoding="utf-8"))

    def load_inst_url_2_id(self):
        print("Loading {} instance id...".format(self.source))
        url2id     = dict()
        id2label   = dict()
        label2id   = dict()
        mention2id = dict()
        id2title   = dict()
        id2uri     = dict()
        inst_url2id_path = os.path.join("./data", self.source, "instance_id.txt")
        with open(inst_url2id_path, 'r', encoding='utf-8') as rf:
            for line in rf:
                line_arr = line.strip().split("\t\t")
                if len(line_arr) != 4:
                    continue
                title, sub_title, url, inst_id = line_arr
                url = url.split("::;")[0][23:]
                url2id[url] = inst_id
                id2uri[inst_id] = url
                id2label[inst_id] = title
                label = title
                if sub_title != "":
                    sub_title = sub_title[1:-1]
                    if self.source == "bd":
                        label += "（" + sub_title + "）"
                    elif self.source == "wiki":
                        label += "(" + sub_title + ")"
                label2id[label] = inst_id
                id2title[inst_id] = label
                if mention2id.get(title) is None:
                    mention2id[title] = list()
                mention2id[title].append(inst_id)
        print("Done.")
        return url2id, id2label, label2id, mention2id, id2title, id2uri

    def load_valid_entities(self):
        """
        加载有 embedding 的 entity id
        :return:
        """
        entity_vocab_path = "/mnt/sdd/zxr/xlink/" + self.source + "/emb/result300/vocab_entity.txt"
        self.valid_entities = set()
        with open(entity_vocab_path, "r", encoding="utf-8") as rf:
            for line in rf:
                self.valid_entities.add(line.split(" ")[0])
