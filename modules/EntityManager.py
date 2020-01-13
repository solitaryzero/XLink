import datetime
import re
import time
from abc import ABCMeta, abstractmethod
from typing import Dict

from models import Entity
from modules.VecModel import VecModel


class EntityDictionary:
    source = None               # type: str
    language = None             # type: str

    entity_dict = dict()        # type: Dict[str, Entity]

    _fulltitle_2_id = dict()    # type: Dict[str, str]
    _uri_2_id = dict()          # type: Dict[str, str]
    _mention_2_ids = dict()     # type: Dict[str, Dict[str, None]]

    def __init__(self, source, language, dict_path):
        self.load_dictionary(source, language, dict_path)

    def load_dictionary(self, source, language, dict_path):
        counter, start_at = 0, int(time. time())
        print("\nLoading entity_dictionary from: {}".format(dict_path))
        with open(dict_path, "r", encoding="utf-8") as rf:
            for line in rf:
                line_arr = line.strip().split("\t\t")
                if len(line_arr) != 4: continue
                title, sub_title, uris, entity_id = line_arr
                uris = uris.split("::;")

                counter += 1

                entity = Entity(entity_id, title, sub_title, source, language)
                for uri in uris:
                    self._uri_2_id[uri] = entity_id

                self._fulltitle_2_id[entity.get_full_title()] = entity_id

                title_mention = self.get_mention_from_title(entity.get_full_title())
                if self._mention_2_ids.get(title_mention) is None:
                    self._mention_2_ids[title_mention] = dict()
                self._mention_2_ids[title_mention][entity_id] = None

                self.entity_dict[entity_id] = entity

        print("Loaded, #{}, time: {}.".format(counter, str(datetime.timedelta(seconds=int(time.time())-start_at))))

    @staticmethod
    def get_mention_from_title(title: str) -> str:
        mention = ""
        st = re.split("[（(]", title)
        for t in st:
            mention += re.split("[)）]", t)[-1]
        return mention

    def get_entity_from_id(self, entity_id):
        return self.entity_dict.get(entity_id)

    def get_entity_from_uri(self, entity_uri):
        if self._uri_2_id.get(entity_uri) is None: return None
        return self.entity_dict.get(self._uri_2_id.get(entity_uri))

    def get_entity_from_fulltitle(self, entity_title):
        if self._fulltitle_2_id.get(entity_title) is None: return None
        return self.entity_dict.get(self._fulltitle_2_id.get(entity_title))

class EntityManager(metaclass=ABCMeta):
    @abstractmethod
    def get_entity_dictionary(self) -> EntityDictionary:
        pass

    @abstractmethod
    def is_entity_has_embed(self, entity_id):
        pass

    @abstractmethod
    def get_vec_model(self) -> VecModel:
        pass


class BaiduEntityManager(EntityManager):
    def __new__(cls, dict_path, vec_path, force_reload=False):
        if not hasattr(BaiduEntityManager, 'instance'):
            cls.instance = super(BaiduEntityManager, cls).__new__(cls)
            cls.instance.init(dict_path, vec_path)
        elif force_reload:
            cls.instance.init(dict_path, vec_path)
        return cls.instance

    def init(self, dict_pth, vec_path):
        source, language = "bd", "zh"
        self.source = source
        self.language = language
        self.entity_dictionary = EntityDictionary(source, language, dict_pth)
        self.vec_model = VecModel(vec_path)
        for entity_id in self.vec_model.vectors:
            if self.entity_dictionary.entity_dict.get(entity_id) is not None:
                self.entity_dictionary.entity_dict[entity_id].set_embed(
                    self.vec_model.vectors.get(entity_id))
        print("BaiduEntityManager prepared.\n")

    def get_entity_dictionary(self):
        return self.entity_dictionary

    def get_vec_model(self):
        return self.vec_model

    def is_entity_has_embed(self, entity_id):
        return self.vec_model.vectors.get(entity_id) is not None


class WikiEntityManager(EntityManager):
    def __new__(cls, dict_path, vec_path, force_reload=False):
        if not hasattr(WikiEntityManager, 'instance'):
            print("Initializing WikiEntityManager...\n\tsource: {}\n\tlanguage:{}")
            cls.instance = super(WikiEntityManager, cls).__new__(cls)
            cls.instance.init(dict_path, vec_path)
        elif force_reload:
            cls.instance.init(dict_path, vec_path)
        return cls.instance


    def init(self, dict_pth, vec_path):
        source, language = "wiki", "en"
        self.source = source
        self.language = language
        self.entity_dictionary = EntityDictionary(source, language, dict_pth)
        self.vec_model = VecModel(vec_path)
        for entity_id in self.vec_model.vectors:
            if self.entity_dictionary.entity_dict.get(entity_id) is not None:
                self.entity_dictionary.entity_dict[entity_id].set_embed(
                    self.vec_model.vectors.get(entity_id))
        print("WikiEntityManager prepared.\n")

    def get_entity_dictionary(self):
        return self.entity_dictionary

    def get_vec_model(self):
        return self.vec_model

    def is_entity_has_embed(self, entity_id):
        return self.vec_model.vectors.get(entity_id) is not None
