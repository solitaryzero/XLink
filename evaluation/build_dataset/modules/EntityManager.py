from evaluation.build_dataset.modules.VecModel import VecModel
from typing import Dict, List
from abc import ABCMeta, abstractmethod
import re
import time, datetime


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


class EntityManager(metaclass=ABCMeta):

    @abstractmethod
    def get_entity_dictionary(self):
        pass

    @abstractmethod
    def is_entity_has_embed(self, entity_id):
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
        if not hasattr(BaiduEntityManager, 'instance'):
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


class Entity:
    ID = None           # type: str
    full_title = None   # type: str
    title = None        # type: str
    sub_title = None    # type: str
    language = None     # type: str
    source = None       # type: str
    embed = None        # type: List[float]

    def __init__(self, entity_id, title, sub_title, source, language, embed=None):
        self.ID = entity_id
        self.full_title = title + sub_title
        self.title = title
        self.sub_title = sub_title
        self.source = source
        self.language = language
        self.embed = embed

    def set_embed(self, embed: List[float]):
        self.embed = embed

    def get_full_title(self):
        return self.full_title
