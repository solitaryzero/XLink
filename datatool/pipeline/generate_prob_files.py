import traceback
import json
import time
import datetime
from jpype import *
from datatool.pipeline.extract_mention_anchors import extract_mention_and_plain_text_from_annotated_doc

class Parser:
    _instance = None
    index_builder = None

    def __init__(self):
        raise SyntaxError('class IndexBuilder should be initialized by get_instance(mention_anchor_path, trie_tree_path)')

    @classmethod
    def get_instance(cls, mention_anchor_path, trie_tree_path, JDClass: JClass):
        if cls._instance is None:
            cls._instance = object.__new__(Parser)
            cls._instance.init(mention_anchor_path, trie_tree_path, JDClass)

        return cls._instance

    def init(self, mention_anchor_path, trie_tree_path, JDClass: JClass):
        self.index_builder = JDClass(mention_anchor_path, trie_tree_path)

    def parse_text(self, doc):
        """
        从 plain_text 中 parse 到可能的所有 mention
        :param text:
        :return:
        """
        parsed_res_text = self.index_builder.parseText(doc)
        text = parsed_res_text[1:-1]
        result = []
        if text != "":
            items = text.split(",")
            for item in items:
                item = item.strip()
                mention_indices, candidates = item.split("=", 1)
                start, end = mention_indices[1:-1].split(":")
                start = int(start)
                end = int(end)
                result.append({
                    "start": start,
                    "end": end,
                    "label": doc[start: end],
                    "candidates": candidates.split("::=")})
        return result


def cal_4_prob_from_mention_anchors(mention_anchors):
    """
    p(e), p(m|e), p(e|m), link(m)

    :param mention_anchors:
    :return: p(e), p(m|e), p(e|m), link(m)
    """

    all = '__all__'

    entity_prior = dict()  # p(e)
    m_given_e    = dict()  # p(m|e)
    e_given_m    = dict()  # p(e|m)
    mention_link = dict()  # link(m) = mention_anchors[mention][all]

    link_sum = 0  # is the total number of both mention and entity
    anchor_mentions = dict()

    for mention in mention_anchors:
        mention_anchors[mention][all] = 0
        for anchor in mention_anchors[mention]:

            # 2020.8.11: Fix the 0.5 bug
            if anchor == all: continue

            if anchor_mentions.get(anchor) is None:
                anchor_mentions[anchor] = dict()
                anchor_mentions[anchor][all] = 0
            if anchor_mentions[anchor].get(mention) is None:
                anchor_mentions[anchor][mention] = 0
            anchor_mentions[anchor][mention] += mention_anchors[mention][anchor]
            anchor_mentions[anchor][all] += mention_anchors[mention][anchor]

            mention_anchors[mention][all] += mention_anchors[mention][anchor]

            link_sum += mention_anchors[mention][anchor]

            if entity_prior.get(anchor) is None:
                entity_prior[anchor] = 0
            entity_prior[anchor] += mention_anchors[mention][anchor]

    # build entity_prior: p(e) and m_given_e: p(m|e)
    for anchor in anchor_mentions:
        mention = ""
        try:
            if anchor == all: continue
            entity_prior[anchor] = float(entity_prior[anchor]/link_sum)
            m_given_e[anchor] = dict()
            for mention in anchor_mentions.get(anchor):
                if mention == all: continue
                m_given_e[anchor][mention] = float(anchor_mentions[anchor][mention]/anchor_mentions[anchor][all])
        except Exception:
            traceback.print_exc()
            print(anchor, ",", mention)

    # build link(m) and e_given_m p(e|m)
    for mention in mention_anchors:
        anchor = ""
        try:
            if mention == all: continue
            mention_link[mention] = mention_anchors[mention][all]
            e_given_m[mention] = dict()
            for anchor in mention_anchors[mention]:
                if anchor == all: continue
                e_given_m[mention][anchor] = float(mention_anchors[mention][anchor]/mention_anchors[mention][all])
        except Exception:
            traceback.print_exc()
            print(anchor, ",", mention)

    return entity_prior, m_given_e, e_given_m, mention_link



"""
jar_path = ""
startJVM(getDefaultJVMPath(), "-Djava.class.path=%s" % jar_path)
JDClass = JClass("edu.TextParser")
shutdownJVM()
"""
def cal_freq_m(corpus_path, mention_anchor_path, trie_tree_path, JDClass: JClass):
    parser = Parser.get_instance(mention_anchor_path, trie_tree_path, JDClass)

    counter, mode_cnt = 0, 100000
    start_time = int(time.time())
    last_update = start_time

    freq_m = dict()
    with open(corpus_path, "r", encoding="utf-8") as rf:
        for line in rf:
            counter += 1
            if counter % mode_cnt == 0:
                curr_update = int(time.time())
                print("{}, time: {}, total_time: {}".format(
                    counter,
                    str(datetime.timedelta(seconds=curr_update - last_update)),
                    str(datetime.timedelta(seconds=curr_update - start_time))
                ))
                last_update = curr_update
            try:
                _, plain_doc = extract_mention_and_plain_text_from_annotated_doc(line)
                mentions = parser.parse_text(plain_doc.lower())
                for item in mentions:
                    if freq_m.get(item['label']) is None:
                        freq_m[item['label']] = 0
                    freq_m[item['label']] += 1
            except Exception:
                traceback.print_exc()
    return freq_m



def generate_entity_prior_file(entity_prior, entity_prior_path, entity_prior_json_path):
    json.dump(entity_prior, open(entity_prior_json_path, "w", encoding="utf-8"))
    with open(entity_prior_path, "w", encoding="utf-8") as wf:
        for entity in entity_prior:
            wf.write("{}::;{}\n".format(entity, str(entity_prior[entity])))


def generate_prob_mention_entity_file(m_given_e, prob_mention_entity_path, prob_mention_entity_json_path):
    json.dump(m_given_e, open(prob_mention_entity_json_path, "w", encoding="utf-8"))
    with open(prob_mention_entity_path, "w", encoding="utf-8") as wf:
        for entity in m_given_e:
            for m in m_given_e[entity]:
                wf.write("{}::;{}::;{}\n".format(entity, m, str(m_given_e[entity][m])))


def generate_link_prob_file(e_given_m, link_m, freq_m, link_prob_path):
    with open(link_prob_path, "w", encoding="utf-8") as wf:
        for m in e_given_m:
            for e in e_given_m[m]:
                wf.write("{}::;{}::;{}::;{}::;{}::;{}\n".format(
                    m,
                    e,
                    str(link_m[m]),
                    str(freq_m[m]),
                    str(float(link_m[m]/freq_m[m])),
                    e_given_m[m][e]
                ))

def update_mention_anchor_from_freq_m(ma, freq_m):
    mention_anchors = dict()
    for m in ma:
        if m in freq_m:
            mention_anchors[m] = ma[m]
    return mention_anchors


def merge_freq_m(freq_m_list):
    merged_freq_m = dict()
    for freq_m in freq_m_list:
        for m in freq_m:
            if merged_freq_m.get(m) is None:
                merged_freq_m[m] = 0
            merged_freq_m[m] += freq_m[m]
    return merged_freq_m
