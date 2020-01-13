from abc import ABCMeta, abstractmethod
from typing import List
import os, json, string

from models import Entity, Mention
from modules import EntityManager


class AnnotationFormatter(metaclass=ABCMeta):
    @abstractmethod
    def format(self, *args, **kwargs):
        pass


class AIDAYAGO2Formatter(AnnotationFormatter):
    entity_manager = None

    def __new__(cls, entity_dict_path, entity_vec_path):
        if not hasattr(AIDAYAGO2Formatter, 'instance'):
            cls.instance = super(AIDAYAGO2Formatter, cls).__new__(cls)
            cls.instance.init(entity_dict_path, entity_vec_path)
        return cls.instance

    def init(self, entity_dict_path, entity_vec_path):
        self.entity_manager = EntityManager.WikiEntityManager(entity_dict_path, entity_vec_path)

    def format(self, raw_dataset_path, target_dataset_dir):
        nme_mentions = []
        total_mentions = []
        NIL_mentions = []

        mentions = []  # type: List[List[tuple]]
        docs = []
        xlore_misses = list()
        valid_entities = list()
        with open(raw_dataset_path, "r", encoding="utf-8") as rf:
            doc_mentions = []  # type: List[List]
            doc = ""
            for line in rf:
                if line.startswith("-DOCSTART-"):
                    doc = doc.strip()
                    if len(doc) > 0:
                        docs.append(doc)
                        mentions.append(doc_mentions)
                    doc, doc_mentions = "", []
                elif len(line.strip()) == 0: # 如果为空
                    doc = doc.strip(' ')
                    doc += "\n"
                elif line.strip() in string.punctuation: # 如果是符号
                    doc = doc.strip(' ')
                    doc += line.strip()
                else:
                    line_arr = line.strip().split("\t")
                    if len(line_arr) > 1:
                        token, flag, mention_label, yago_id = line_arr[0], line_arr[1], line_arr[2], line_arr[3]
                        if flag == 'B':
                            total_mentions.append(mention_label)
                            mention = Mention(len(doc), len(doc) + len(mention_label), mention_label)
                            if yago_id != '--NME--':
                                wiki_url = line_arr[4][23:]
                                entity = self.entity_manager.entity_dictionary.get_entity_from_uri(wiki_url) # type: Entity
                                if entity is not None:
                                    valid_entities.append(wiki_url)
                                    mention.set_gold_entity(entity)
                                    doc_mentions.append((mention.start, mention.end, mention.label, mention.gold_entity.ID))
                                else:
                                    NIL_mentions.append(mention_label)
                                    doc_mentions.append((mention.start, mention.end, mention.label, 'NIL'))
                                    xlore_misses.append(wiki_url)
                            else:
                                NIL_mentions.append(mention_label)
                                nme_mentions.append(mention.label)
                                doc_mentions.append((mention.start, mention.end, mention.label, "NIL"))
                        if flag != 'I':
                            doc += mention_label + ' '
                    else:
                        doc += line_arr[0] + " "

            if len(doc_mentions) > 0:
                mentions.append(doc_mentions)
                docs.append(doc)

        json.dump(mentions, open(os.path.join(target_dataset_dir, "annotations.json"), "w", encoding="utf-8"), indent=4, ensure_ascii=False)
        json.dump(docs, open(os.path.join(target_dataset_dir, "docs.json"), "w", encoding="utf-8"), indent=4, ensure_ascii=False)
        json.dump(xlore_misses, open(os.path.join(target_dataset_dir, "xlore_misses.json"), "w", encoding="utf-8"), indent=4, ensure_ascii=False)
        json.dump(valid_entities, open(os.path.join(target_dataset_dir, "valid_entities.json"), "w", encoding="utf-8"), indent=4, ensure_ascii=False)
        print("Total Document: #{}\n"
              "Total Labeled Mentions\t total: #{}\t unique: #{}\n"
              "NIL Mentions({}%)\t total: #{}\t unique: #{}\n"
              "Xlore Missed({}%)\t total: #{}\t unique: #{}\n"
              "NME Mentions({}%)\t total: #{}\t unique: #{}\n".format(
            len(docs),
            len(total_mentions), len(set(total_mentions)),
            "%.2f"%(len(NIL_mentions)/len(total_mentions)*100), len(NIL_mentions), len(set(NIL_mentions)),
            "%.2f"%(len(xlore_misses)/len(total_mentions)*100), len(xlore_misses), len(set(xlore_misses)),
            "%.2f"%(len(nme_mentions)/len(total_mentions)*100), len(nme_mentions), len(set(nme_mentions))))
        return total_mentions, NIL_mentions, xlore_misses, nme_mentions
