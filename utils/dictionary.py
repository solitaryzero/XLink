from typing import Dict
import time
import datetime
from config import Config
import re


class EntityDictionary:
    _bd_instance = None     # type: EntityDictionary
    _wiki_instance = None   # type: EntityDictionary

    _source     = ""    # type: str
    _language   = ""    # type: str

    entity_dict      = dict()  # type: Dict[str, Entity]

    title2entity     = dict()  # type: Dict[str, Entity]
    uri2entity       = dict()  # type: Dict[str, Entity]

    mention2entities = dict()  # type: Dict[str, Dict[str, Entity]]

    def __init__(self):
        raise SyntaxError("InstanceDictionary can be initialized by __init__, please use get_instance()")

    @classmethod
    def get_instance(cls, source: str, force=False):
        """
        :param source:
        :return: EntityDictionary
        """
        entity_dict_path = Config.get_entity_id_path(source)

        if source == 'bd':
            if cls._bd_instance is None:
                cls._bd_instance = object.__new__(EntityDictionary)
                cls._bd_instance.init(source, entity_dict_path)
            return cls._bd_instance

        if source == 'wiki':
            if cls._wiki_instance is None:
                cls._wiki_instance = object.__new__(EntityDictionary)
                cls._wiki_instance.init(source, entity_dict_path)
            return cls._wiki_instance

    def init(self, source, entity_dict_path):
        """
        :param source: corpus source
        :param entity_dict_path: <title>\t\t<sub_title>\t\t<uri>\t\t<entity_id>
        :return: void
        """
        self._source           = source
        self.uri2entity       = dict()
        self.title2entity     = dict()
        self.mention2entities = dict()

        if self._source in ["bd"]:
            self._language = "zh"
        elif self._source in ["wiki"]:
            self._language = "wiki"

        print("\nLoading entities from {}".format(entity_dict_path))
        print("\tsource: {}\n\tlanguage: {}".format(self._source, self._language))

        counter = 0
        start_time = int(time.time())
        with open(entity_dict_path, "r", encoding="utf-8") as rf:
            for line in rf:
                line_arr = line.strip().split("\t\t")
                if len(line_arr) != 4: continue
                title, sub_title, uris, entity_id = line_arr
                uris = uris.split("::;")

                counter += 1
                entity = Entity(source, entity_id, title, self._language, uris, sub_title)  # type: Entity

                self.entity_dict[entity_id] = entity

                for uri in uris:
                    self.uri2entity[uri] = entity

                self.title2entity[entity.get_full_title()] = entity

                title_mention = self.get_mention_from_title(title)
                if self.mention2entities.get(title_mention) is None:
                    self.mention2entities[title_mention] = dict()
                self.mention2entities[title_mention][entity_id] = entity

        print("Entities loaded, #entity: {}, time: {}.".format(
            counter, str(datetime.timedelta(seconds=int(time.time()-start_time)))))

    def get_entity_by_id(self, entity_id) -> object:
        return self.entity_dict.get(entity_id)

    def get_entity_by_full_title(self, full_title) -> object:
        return self.title2entity.get(full_title)

    def get_entity_by_uri(self, uri) -> object:
        return self.uri2entity.get(uri)

    @staticmethod
    def get_mention_from_title(title: str) -> str:
        mention = ""
        st = re.split("[（(]", title)
        for t in st:
            mention += re.split("[)）]", t)[-1]
        return mention

class Entity:
    _source = None

    _id = None
    _title = None
    _language = None
    _uri = None
    _sub_title = None

    def __init__(self, source, entity_id, title, language, uris=None, sub_title=None):
        self._source = source
        self._id = entity_id
        self._title = title
        self._language = language
        self._uris = uris
        self._sub_title = sub_title

    def get_full_title(self):
        if self._sub_title is not None and self._sub_title.strip() != "":
            if self._language == 'en':
                return "{}({})".format(self._title, self._sub_title)
            else:
                return "{}（{}）".format(self._title, self._sub_title)
        else:
            return self._title

    def get_title_mention(self):
        return self._title

    def get_id(self):
        return self._id

    def get_title(self):
        return self._title

    def get_language(self):
        return self._language

    def get_sub_title(self):
        return self._sub_title

    def get_source(self):
        return self._source

    def get_mention(self):
        mention = ""
        st = re.split("[（(]", self._title)
        for t in st:
            mention += re.split("[)）]", t)[-1]
        return mention