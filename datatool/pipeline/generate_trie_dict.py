from utils.dictionary import EntityDictionary
import time
import datetime


def expand_mention_anchors(source, mention_anchors):
    """
    从 mention_anchor.json 扩充词典
        a. 将满足以下条件的实体加入到全文统计的实体中，出现次数记为 1
            - 其 title 与 mention-anchor 字典中的某一 mention 相同
            - 该实体从未在语料中以 title 作为 mention 出现过
        b. 对于 title 没有作为 mention 出现过的实体
            - 以 title 作为 mention 构造 title-entity 字典

    :param source: string
    :param mention_anchors: dict
    :return: (dict, dict)
    """

    entity_dict = EntityDictionary.get_instance(source)
    title_entities = dict()

    print("\nExpanding mention anchors from entity dictionary...")
    start_at = int(time.time())
    for instance_id in entity_dict.entity_dict:
        mention = entity_dict.get_entity_by_id(instance_id).get_mention()
        if mention_anchors.get(mention) is not None:
            if mention_anchors[mention].get(instance_id) is None:
                mention_anchors[mention][instance_id] = 1
        else:
            title_entities[mention] = instance_id
    print("Expanded, entities with different mentions: #{}, time: {}".format(
        len(title_entities), str(datetime.timedelta(seconds=int(time.time())-start_at))))
    return title_entities


def generate_mention_anchors_txt_for_trie(mention_anchors, mention_anchors_txt_path):
    print("\nGenerating file for building mention_anchor trie tree, target file path: \n\t{}"
          .format(mention_anchors_txt_path))
    start_at = int(time.time())
    with open(mention_anchors_txt_path, "w", encoding="utf-8") as wf:
        for mention in mention_anchors:
            if mention.strip() == "": continue
            wf.write(mention + "::=" + "::=".join(mention_anchors[mention].keys()) + "\n")
    print("Generated, time: {}".format(str(datetime.timedelta(seconds=int(time.time())-start_at))))

def generate_title_entities_txt_for_trie(title_entities, title_entities_txt_path):
    print("\nGenerating file for building title_entities trie tree, target file path: \n\t{}"
          .format(title_entities_txt_path))
    start_at = int(time.time())
    with open(title_entities_txt_path, "w", encoding="utf-8") as wf:
        for title in title_entities:
            if title.strip() == "": continue
            wf.write(title + "::=" + title_entities[title] + "\n")
    print("Generated, time: {}".format(str(datetime.timedelta(seconds=int(time.time())-start_at))))

def generate_vocab_word_for_trie(emb_vocab_path, vocab_word_txt_path):
    with open(emb_vocab_path, "r", encoding="utf-8") as rf:
        with open(vocab_word_txt_path, "w", encoding="utf-8") as wf:
            for line in rf:
                wf.write("::=".join(line.split(" "))+"\n")
