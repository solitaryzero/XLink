from __future__ import unicode_literals

import json
from typing import List

from datatool.pipeline import extract_mention_anchors
from evaluation.build_dataset import OutputFormatter, SampleBuilder
from modules import MentionParser

source = "bd"
data_path = "/mnt/sdd/zxr/xlink/{}/".format(source)
entity_dict_path = data_path + "entity_id.txt"
entity_vec_path  = data_path + "emb/result300/vectors_entity"
word_vec_path    = data_path + "emb/result300/vectors_word"
mention_txt_path = data_path + "mention_anchors.txt"
mention_trie_path = data_path + "mention_anchors.trie"

mention_parser = MentionParser.TrieTreeMentionParser(mention_txt_path, mention_trie_path)
builder = SampleBuilder.SampleBuilder(source, entity_dict_path, entity_vec_path, word_vec_path)
builder.set_super_params(context_window=100, context_words_sim_th=0.4, seed_candidates_sim_th=0.45, believe_score_th=0.5)


def get_formatted_doc(doc):
    mention_list = mention_parser.parse_text(doc)
    mentions = builder.build_sample(mention_list, doc)

    doc_formatted_str = OutputFormatter.OutputFormatter.format(mentions, doc)
    return doc_formatted_str

def get_formatted_doc_for_json(doc)->List[str]:
    mention_list = mention_parser.parse_text(doc)
    mentions = builder.build_sample(mention_list, doc)
    formatted_list = OutputFormatter.OutputFormatter.format_for_json(mentions)
    return formatted_list

def generate_annotation_json(corpus_path, target_dir_path, offset=0, expected_dataset_num=100, doc_min_len=200):
    annotations, cnt = list(), 0
    docs = list()
    with open(corpus_path, "r", encoding="utf-8") as rf:
        for line in rf:
            corpus = "".join(line.strip().split(" "))
            _, plain_text = extract_mention_anchors.extract_mention_and_plain_text_from_annotated_doc(corpus)
            if len(plain_text) < doc_min_len: continue

            if cnt < offset:
                cnt += 1
                continue
            docs.append(plain_text)
            annotations.append(get_formatted_doc_for_json(plain_text))
            cnt += 1
            if len(docs) >= expected_dataset_num: break
    json.dump(annotations, open(target_dir_path + "annotations_{}_{}.json".format(offset, expected_dataset_num), "w", encoding="utf-8"), indent=4, ensure_ascii=False)
    json.dump(docs, open(target_dir_path + "docs_{}_{}.json".format(offset, expected_dataset_num), "w", encoding="utf-8"), indent=4, ensure_ascii=False)


def generate_annotation_txt():
    corpus_path = data_path + "emb/train_text"
    eval_annotation_path = data_path + "eval/annotations.txt"
    docs, dataset_num = [], 100
    with open(corpus_path, "r", encoding="utf-8") as rf:
        with open(eval_annotation_path, "w", encoding="utf-8") as wf:
            counter = 0
            for line in rf:
                corpus = "".join(line.strip().split(" "))
                ma, plain_text = extract_mention_anchors.extract_mention_and_plain_text_from_annotated_doc(corpus)
                if len(plain_text) < 200: continue

                docs.append(plain_text)
                wf.write("<doc>{}</doc>\n".format(get_formatted_doc(plain_text)))

                counter += 1
                if counter >= dataset_num: break

    f = open(data_path + "eval/docs.txt", "w", encoding="utf-8")
    f.write("\n".format(docs))
    f.close()