import datetime
import json
import time
from typing import Dict


class ProbHolder:
    # entity->prob
    entity_prior = None # type: Dict[str, float]
    # entity->mention->prob
    m_given_e    = None # type: Dict[str, Dict[str, float]]
    # mention->entity->prob
    e_given_m    = None # type: Dict[str, Dict[str, float]]
    # mention->prob
    link_prob    = None # type: Dict[str, float]

    def __init__(self, entity_prior_path, m_given_e_path, e_given_m_path, link_prob_path):
        """
        :param entity_prior_path:
        :param m_given_e_path:
        :param e_given_m_path:
        :param link_prob_path:
        """
        print("\nLoading prob files: \n\t{}\n\t{}\n\t{}\n\t{}".format(
            entity_prior_path,
            m_given_e_path,
            e_given_m_path,
            link_prob_path
        ))
        start_at = int(time.time())
        self.entity_prior = json.load(open(entity_prior_path, "r", encoding="utf-8"))
        self.m_given_e    = json.load(open(m_given_e_path, "r", encoding="utf-8"))
        self.e_given_m    = json.load(open(e_given_m_path, "r", encoding="utf-8"))
        self.link_prob    = json.load(open(link_prob_path, "r", encoding="utf-8"))
        print("Loaded. Time: {}".format(str(datetime.timedelta(seconds=int(time.time())-start_at))))

    def get_link_prob(self, mention: str):
        return self.link_prob.get(mention)

    def get_m_given_e(self, mention: str, entity_id: str):
        if self.m_given_e.get(entity_id) is not None and self.m_given_e.get(entity_id).get(mention) is not None:
            return self.m_given_e[entity_id][mention]
        return None

    def get_e_given_m(self, entity_id: str, mention: str):
        if self.e_given_m.get(mention) is not None and self.e_given_m.get(mention).get(entity_id) is not None:
            return self.e_given_m[mention][entity_id]
        return None

    def get_entity_prior(self, entity_id):
        return self.entity_prior.get(entity_id)


class BaiduProbHolder(ProbHolder):
    source = "bd"
    language = "en"

    def __new__(cls, entity_prior_path, m_given_e_path, e_given_m_path, link_prob_path):
        if not hasattr(BaiduProbHolder, 'instance'):
            cls.instance = super(BaiduProbHolder, cls).__new__(cls)
        return cls.instance

class WikiProbHolder(ProbHolder):
    source = "bd"
    language = "en"

    def __new__(cls, entity_prior_path, m_given_e_path, e_given_m_path, link_prob_path):
        if not hasattr(WikiProbHolder, 'instance'):
            cls.instance = super(WikiProbHolder, cls).__new__(cls)
        return cls.instance