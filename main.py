# from jpype import *
import subprocess
import os
import argparse

def generate_standard_entity_dict(source, old_entity_path, entity_ttl_path, standard_entity_path) -> None:
    from utils.entity import EntityHolder
    from datatool.pipeline import prepare_standard_input as prep_input
    old_entity_holder = EntityHolder.get_instance(source, old_entity_path)
    standard_id2title = prep_input.get_id2title_from_ttl(source, entity_ttl_path)
    prep_input.generate_standard_entity_id(standard_entity_path, old_entity_holder, standard_id2title)

def generate_standard_corpus(source, data_path, corpus_name, mark_titles=False) -> None:
    import os, imp

    if (source == 'bd'):
        raw_corpus_path = os.path.join(data_path, "bd_{}.txt".format(corpus_name))
    elif (source == 'wiki'):
        raw_corpus_path = os.path.join(data_path, "en_{}.txt".format(corpus_name))
    refined_corpus_path = os.path.join(data_path, "refined_{}.txt".format(corpus_name))
    standard_corpus_path = os.path.join(data_path, "standard_{}.txt".format(corpus_name))

    from datatool.pipeline import prepare_standard_input as prep_input
    imp.reload(prep_input)
    if corpus_name == "infobox":
        prep_input.infobox_pre_refine(source, raw_corpus_path,
            os.path.join(data_path, "pre_raw_{}.txt".format(corpus_name)))
        # prep_input.corpus_refine(source, os.path.join(data_path, "pre_raw_{}.txt".format(corpus_name)), refined_corpus_path)
        prep_input.corpus_full_refine(source, os.path.join(data_path, "pre_raw_{}.txt".format(corpus_name)), standard_corpus_path, mark_titles)
    else:    
        # prep_input.corpus_refine(source, raw_corpus_path, refined_corpus_path)
        prep_input.corpus_full_refine(source, raw_corpus_path, standard_corpus_path, mark_titles)
    # prep_input.corpus_annotation_refine(source, refined_corpus_path, standard_corpus_path)

def statistics_about_mention_anchors_and_out_links(mention_anchors: dict, out_links: dict) -> None:
    from datatool.pipeline import tools
    import imp
    imp.reload(tools)

    # referred_entities = tools.cal_unique_anchors(mention_anchors)
    referred_entities = tools.cal_unique_refers(out_links)
    print("\tmentions #{}".format(len(mention_anchors)))
    print("\tanchors #{}".format(tools.cal_total_links(mention_anchors)))
    print("\tunique_anchors #{}".format(len(tools.cal_unique_anchors(mention_anchors))))
    print("\treferred entities: #{}".format(len(referred_entities)))
    print("\tvalid out links: #{}".format(len(out_links)))
    print("\tcandidate=1: #{}".format(tools.cal_mention_eq(mention_anchors, 1)))
    print("\tcandidate>1: #{}".format(tools.cal_mention_bigger(mention_anchors, 1)))
    print("\tcandidate>2: #{}".format(tools.cal_mention_bigger(mention_anchors, 2)))

def generate_mention_anchors_and_out_links(data_path: str, corpus_name: str) -> tuple:
    import os, json
    import time, datetime
    from datatool.pipeline import extract_mention_anchors
    standard_corpus_path = os.path.join(data_path, "standard_{}.txt".format(corpus_name))
    # mention_anchors, out_links = extract_mention_anchors.extract_mention_and_out_links_from_corpus(standard_corpus_path)
    mention_anchors, out_links, self_links = extract_mention_anchors.extract_mention_and_out_links_from_corpus(standard_corpus_path)

    mention_anchors_json_path   = os.path.join(data_path, "mention_anchors_{}.json".format(corpus_name))
    out_links_json_path         = os.path.join(data_path, "out_links_{}.json".format(corpus_name))

    # 2020.10.28
    self_links_json_path        = os.path.join(data_path, "self_links_{}.json".format(corpus_name))

    start_at = int(time.time())
    print("Saving mention_anchors and out_links to file:\n\t{}\n\t{}".format(
        mention_anchors_json_path, out_links_json_path))
    json.dump(mention_anchors, open(mention_anchors_json_path, "w", encoding="utf-8"))
    json.dump(out_links, open(out_links_json_path, "w", encoding="utf-8"))

    json.dump(self_links, open(self_links_json_path, "w", encoding="utf-8"))

    print("Json files saved. time: {}".format(
        str(datetime.timedelta(seconds=int(time.time()) - start_at))
    ))
    statistics_about_mention_anchors_and_out_links(mention_anchors, out_links)
    return mention_anchors, out_links

def merge_multiple_mention_anchors(data_path: str, corpus_list: list, is_save=False) -> tuple:
    import os, time, datetime, json
    from datatool.pipeline import extract_mention_anchors

    start_at = int(time.time())
    print("Merging mention_anchors from: {}".format(",".join(corpus_list)))
    mention_anchors_list = list()
    out_links_list = list()
    self_links_list = list()

    for corpus in corpus_list:
        mention_anchors_json_path = os.path.join(data_path, "mention_anchors_{}.json".format(corpus))
        out_links_json_path = os.path.join(data_path,  "out_links_{}.json".format(corpus))
        self_links_json_path = os.path.join(data_path, "self_links_{}.json".format(corpus))

        mention_anchors_list.append(json.load(open(mention_anchors_json_path, "r", encoding="utf-8")))
        out_links_list.append(json.load(open(out_links_json_path, "r", encoding="utf-8")))
        self_links_list.append(json.load(open(self_links_json_path, "r", encoding="utf-8")))

    mention_anchors = extract_mention_anchors.merge_mention_anchors(mention_anchors_list)
    out_links = extract_mention_anchors.merge_out_links(out_links_list)
    self_links = extract_mention_anchors.merge_self_links(self_links_list)

    if is_save:
        mention_anchors_json_path = os.path.join(data_path, "mention_anchors.json")
        json.dump(mention_anchors, open(mention_anchors_json_path, "w", encoding="utf-8"))
        out_links_json_path = os.path.join(data_path, "out_links.json")
        json.dump(out_links, open(out_links_json_path, "w", encoding="utf-8"))
        self_links_json_path = os.path.join(data_path, "self_links.json")
        json.dump(out_links, open(self_links_json_path, "w", encoding="utf-8"))

        print("Finished, time: {}. merged files have been saved to: \n\t{}\n\t{}\n\t{}".format(
            str(datetime.timedelta(seconds=int(time.time()) - start_at)),
            mention_anchors_json_path,
            out_links_json_path,
            self_links_json_path
        ))
    statistics_about_mention_anchors_and_out_links(mention_anchors, out_links)
    return mention_anchors, out_links

def expand_mention_anchors_by_entity_dict(source, data_path, mention_anchors, is_save=False) -> tuple:
    import json, imp
    from datatool.pipeline import extract_mention_anchors, generate_trie_dict
    imp.reload(extract_mention_anchors)
    imp.reload(generate_trie_dict)

    title_entities = extract_mention_anchors.expand_mention_anchors(source, mention_anchors)

    if is_save:
        json.dump(mention_anchors, open(data_path + "mention_anchors.json", "w", encoding="utf-8"))
        json.dump(title_entities, open(data_path + "title_entities.json", "w", encoding="utf-8"))

    return mention_anchors, title_entities

def init_JVM():
    from config import Config
    jar_path = Config.project_root + "data/jar/BuildIndex.jar"

    if not isJVMStarted():
        startJVM(getDefaultJVMPath(), "-Djava.class.path=%s" % jar_path)
    if not isThreadAttachedToJVM():
        attachThreadToJVM()
    JDClass = JClass("edu.TextParser")
    return JDClass

# def calculate_freq_m(data_path, corpus_name, JDClass) -> dict:
def calculate_freq_m(data_path, corpus_name) -> dict:
    import os, json
    from datatool.pipeline import generate_prob_files

    standard_corpus_path = os.path.join(data_path, "standard_{}.txt".format(corpus_name))
    mention_anchors_txt_path = os.path.join(data_path, "mention_anchors.txt")
    # mention_anchors_trie_path = os.path.join(data_path, "mention_anchors.trie")

    # if (os.path.exists(mention_anchors_trie_path)):
    #     os.remove(mention_anchors_trie_path)

    # freq_m = generate_prob_files.cal_freq_m(standard_corpus_path, mention_anchors_txt_path, mention_anchors_trie_path,
    #                                         JDClass)
    freq_m = generate_prob_files.cal_freq_m(standard_corpus_path, mention_anchors_txt_path)
    json.dump(freq_m, open(os.path.join(data_path, "freq_m_{}.json".format(corpus_name)), "w", encoding="utf-8"))
    return freq_m

def merge_freq_m(data_path, corpus_list, is_save=False) -> dict:
    from datatool.pipeline import generate_prob_files
    import os, json
    freq_m_list = list()
    for corpus in corpus_list:
        freq_m_path = os.path.join(data_path, "freq_m_{}.json".format(corpus))
        freq_m_list.append(json.load(open(freq_m_path, "r", encoding="utf-8")))
    freq_m = generate_prob_files.merge_freq_m(freq_m_list)
    if is_save:
        json.dump(freq_m, open(os.path.join(data_path, "freq_m.json"), "w"))
    return freq_m

def refine_mention_anchors_by_freq_m(data_path, freq_m=None, mention_anchors=None, is_save=False) -> dict:
    import os, json
    ma = dict()
    if mention_anchors is None:
        mention_anchors = json.load(open(os.path.join(data_path, "mention_anchors.json"), "r", encoding="utf-8"))

    if freq_m is None:
        freq_m_path = os.path.join(data_path, "freq_m.json")
        freq_m      = json.load(open(freq_m_path, "r", encoding="utf-8"))

    for m in mention_anchors:
        if m in freq_m:
            ma[m] = mention_anchors[m]
    if is_save:
        json.dump(ma, open(os.path.join(data_path, "mention_anchors.json"), "w", encoding="utf-8"))
    return ma

def filter_mention_anchors_by_len_and_prob(
        data_path, link_prob_th, mention_anchors=None, link_m=None, freq_m=None):
    from datatool.pipeline import extract_mention_anchors
    import imp
    import json, os, time, datetime
    imp.reload(extract_mention_anchors)

    start_at = int(time.time())
    if mention_anchors is None:
        ma_path     = os.path.join(data_path, "mention_anchors.json")
        print("\nLoading mention_anchors from file: {}".format(ma_path))
        mention_anchors = json.load(open(ma_path, "r", encoding="utf-8"))

    if link_m is None:
        print("Counting link(m)...")
        link_m = dict()
        for m in mention_anchors:
            link_m[m] = 0
            for a in mention_anchors[m]:
                link_m[m] += mention_anchors[m][a]

    if freq_m is None:
        freq_m_path = os.path.join(data_path, "freq_m.json")
        print("\nLoading freq(m) from file: {}".format(freq_m_path))
        freq_m      = json.load(open(freq_m_path, "r", encoding="utf-8"))

    self_links_path = os.path.join(data_path, "self_links.json")
    print("\nLoading self links from file: {}".format(self_links_path))
    self_links      = json.load(open(self_links_path, "r", encoding="utf-8"))

    print("\nFiltering mention anchors, link_prob threshold: {}".format(link_prob_th))
    ma = extract_mention_anchors.filter_mention_anchors(mention_anchors, link_m, freq_m, self_links, link_prob_th)

    print("\nFiltered, time: {}".format(str(datetime.timedelta(seconds=int(time.time())-start_at))))
    return ma

def generate_mention_anchors_trie(data_path) -> None:
    import os, json, imp, time, datetime
    from datatool.pipeline import generate_trie_dict
    imp.reload(generate_trie_dict)
    mention_anchors_json_path = os.path.join(data_path, "mention_anchors.json")
    mention_anchors_txt_path = os.path.join(data_path, "mention_anchors.txt")
    start_at = int(time.time())
    print("Generating mention_anchors.txt for building trie tree.\n\tdata_from: {}\n\tsaved_to: {}".format(
        mention_anchors_json_path, mention_anchors_txt_path))
    mention_anchors = json.load(open(mention_anchors_json_path, "r", encoding="utf-8"))
    generate_trie_dict.generate_mention_anchors_txt_for_trie(mention_anchors, mention_anchors_txt_path)
    print("Generated. Time: {}".format(str(datetime.timedelta(seconds=int(time.time())-start_at))))

    if (os.path.exists(os.path.join(data_path, "mention_anchors.trie"))):
        os.remove(os.path.join(data_path, "mention_anchors.trie"))

def generate_vocab_word_for_trie(data_path):
    import os, imp
    from datatool.pipeline import generate_trie_dict
    imp.reload(generate_trie_dict)

    vocab_word_path = os.path.join(data_path, "emb/result300/vocab_word.txt")
    vocab_word_txt_path = os.path.join(data_path, "vocab_word.txt")
    print("\nLoading vocab from file: {}".format(vocab_word_path))
    generate_trie_dict.generate_vocab_word_for_trie(vocab_word_path, vocab_word_txt_path)
    print("\nVocab word txt file is saved to: {}".format(vocab_word_txt_path))

def generate_input_for_tries(data_path) -> None:
    import os, json
    from datatool.pipeline import generate_trie_dict

    mention_anchors_json_path = os.path.join(data_path, "mention_anchors.json")
    title_entities_json_path  = os.path.join(data_path, "title_entities.json")
    mention_anchors = json.load(open(mention_anchors_json_path, "r", encoding="utf-8"))
    title_entities  = json.load(open(title_entities_json_path, "r", encoding="utf-8"))

    mention_anchors_txt_path = os.path.join(data_path, "mention_anchors.txt")
    title_entities_txt_path  = os.path.join(data_path, "title_entities.txt")

    generate_trie_dict.generate_mention_anchors_txt_for_trie(mention_anchors, mention_anchors_txt_path)
    generate_trie_dict.generate_title_entities_txt_for_trie(title_entities, title_entities_txt_path)

def generate_emb_train_kg(data_path) -> None:
    import os, json
    from datatool.pipeline import extract_embedding_train

    train_kg_path = os.path.join(data_path, "emb/train_kg")
    out_links = json.load(open(os.path.join(data_path, "out_links.json"), "r", encoding="utf-8"))
    extract_embedding_train.generate_train_kg_from_out_links(out_links, train_kg_path)

def generate_emb_train_text(source, data_path, corpus_name) -> None:
    import os
    from datatool.pipeline import extract_embedding_train

    train_text_path = os.path.join(data_path, "emb/train_text_{}.txt".format(corpus_name))
    standard_corpus_path = os.path.join(data_path, "standard_{}.txt".format(corpus_name))
    if source == "bd":
        extract_embedding_train.extract_bd_corpus(standard_corpus_path, train_text_path)
    elif source == "wiki":
        # TODO: 没验证过
        extract_embedding_train.extract_wiki_corpus(standard_corpus_path, train_text_path)

def filter_mention_anchor_by_entity_emb(source, mention_anchors, entity_dict_path, entity_vec_path):
    from modules import EntityManager
    import imp
    imp.reload(EntityManager)

    EManager = EntityManager.BaiduEntityManager
    if source == 'wiki':
        EManager = EntityManager.WikiEntityManager
    entity_manager = EManager(entity_dict_path, entity_vec_path)
    mas = dict()
    for m in mention_anchors:
        mas[m] = dict()
        for a in mention_anchors[m]:
            if entity_manager.is_entity_has_embed(a):
                mas[m][a] = mention_anchors[m][a]
        if len(mas[m]) == 0:
            del mas[m]
    return mas

def generate_prob_files(data_path) -> None:
    import os, json, time, datetime
    from datatool.pipeline import generate_prob_files

    start_at = int(time.time())
    mention_anchors = json.load(open(os.path.join(data_path, "mention_anchors.json"), encoding="utf-8"))
    entity_prior, m_given_e, e_given_m, mention_link = generate_prob_files.cal_4_prob_from_mention_anchors(
        mention_anchors)

    entity_prior_path = os.path.join(data_path, "entity_prior.dat")
    entity_prior_json_path = os.path.join(data_path, "entity_prior.json")
    generate_prob_files.generate_entity_prior_file(entity_prior, entity_prior_path, entity_prior_json_path)

    link_prob_path = os.path.join(data_path, "link_prob.dat")
    freq_m         = json.load(open(os.path.join(data_path, "freq_m.json"), encoding="utf-8"))
    generate_prob_files.generate_link_prob_file(e_given_m, mention_link, freq_m, link_prob_path)

    link_prob_json_path = os.path.join(data_path, "link_prob.json")
    link_prob = dict()
    for m in e_given_m: link_prob[m] = float(mention_link[m])/freq_m[m]
    json.dump(link_prob, open(link_prob_json_path, "w", encoding="utf-8"))

    prob_mention_entity_path = os.path.join(data_path, "prob_mention_entity.dat")
    prob_mention_entity_json_path = os.path.join(data_path, "prob_mention_entity.json")
    generate_prob_files.generate_prob_mention_entity_file(m_given_e, prob_mention_entity_path,
                                                          prob_mention_entity_json_path)
    print("Four prob files generated, time: {}, saved to: \n\t{}\n\t{}\n\t{}\n\t{}".format(
        str(datetime.timedelta(seconds=int(time.time()) - start_at)),
        entity_prior_path, link_prob_path, prob_mention_entity_path, link_prob_json_path))

def filter_title_entities(source, data_path):
    import json, os, imp
    from modules import EntityManager
    imp.reload(EntityManager)

    EManager = None # type: EntityManager.EntityManager
    if source == 'bd': 
        EManager = EntityManager.BaiduEntityManager
        entity_manager = EManager(data_path + "bd_instance_ID.txt", data_path + "emb/result300/vectors_entity")
    if source == 'wiki': 
        EManager = EntityManager.WikiEntityManager
        entity_manager = EManager(data_path + "en_instance_ID.txt", data_path + "emb/result300/vectors_entity")
    
    title_entities = json.load(open(os.path.join(data_path, "title_entities.json"), "r", encoding="utf-8"))
    refined_tt = dict()
    for title in title_entities:
        if entity_manager.is_entity_has_embed(title_entities[title]):
            refined_tt[title] = title_entities[title]
    json.dump(refined_tt, open(os.path.join(data_path, "title_entities.json"), "w", encoding="utf-8"))
    return refined_tt


def train_embeddings(data_path, corpus_list, source, merge=True, train=True, move=True):
    from datatool.pipeline import calculate_entity_embedding

    train_text_paths = [os.path.join(data_path, "emb/train_text_{}.txt".format(corpus_name)) for corpus_name in corpus_list]
    merge_command = 'cat ' + ' '.join(train_text_paths) + ' > ' + os.path.join(data_path, "emb/train_text")
    if (merge):
        print('Executing: ' + merge_command)
        subprocess.call(merge_command, shell=True)
    train_command = ['bash', './TrainJointModel/src/xlink-align.sh', source]
    if (train):
        print('Executing: ' + ' '.join(train_command))
        subprocess.call(train_command)

    if (move):
        mv_command1 = ['cp', '%s/emb/result300/vectors_entity10.dat' %data_path, '%s/emb/result300/vectors_entity' %data_path]
        subprocess.call(mv_command1)
        mv_command2 = ['cp', '%s/emb/result300/vectors_word10.dat' %data_path, '%s/emb/result300/vectors_word' %data_path]
        subprocess.call(mv_command2)

    calculate_entity_embedding.calculate_embedding_with_abstract(corpus_path='%s/standard_abstract.txt' %data_path,
                                                                 vector_path='%s/emb/result300/vectors_word' %data_path,
                                                                 out_path='%s/emb/result300/vectors_abstract' %data_path)


def generate_tries(data_path):
    from datatool.pipeline import generate_tries
    title_entity_txt_path = os.path.join(data_path, "title_entities.txt")
    title_entity_trie_path = os.path.join(data_path, "title_entities.pytrie")
    generate_tries.build_trie(title_entity_txt_path, title_entity_trie_path)

    mention_txt_path = os.path.join(data_path, "mention_anchors.txt")
    mention_trie_path = os.path.join(data_path, "mention_anchors.pytrie")
    generate_tries.build_trie(mention_txt_path, mention_trie_path)

    vocab_txt_path = os.path.join(data_path, "vocab_word.txt")
    vocab_trie_path = os.path.join(data_path, "vocab_word.pytrie")
    generate_tries.build_trie(vocab_txt_path, vocab_trie_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=str, default='bd')
    args = parser.parse_args()
    source = args.source
    data_path = '/data/zfw/xlink/%s/' %(source)
    corpus_list = ["abstract", "article", "infobox"]

    # 第一步
    # 1.1 生成标准输入: standard_entity_id.txt   standard_corpus.txt
    # ttl_path                = data_path + "entity_id.ttl"
    # standard_entity_id_path = data_path + "entity_id.txt"
    # old_entity_path         = data_path + "old_entity_id.txt"
    # generate_standard_entity_dict(source, old_entity_path, ttl_path, standard_entity_id_path)
    for c in corpus_list:
        generate_standard_corpus(source, data_path, c, True)
    

    # 第二步
    # 2.1 抽取 mention_anchors 和 out_links
    for c in corpus_list:
        _m, _o = generate_mention_anchors_and_out_links(data_path, c)
    _, __ = merge_multiple_mention_anchors(data_path, corpus_list, is_save=True)

    # 2.2 由 standard_corpus 生成 train_text
    for c in corpus_list:
        generate_emb_train_text(source, data_path, c) # 中文 30h，英文很快
    
    # 第三步
    # 3.1 生成 mention_anchors.trie 来计算 freq(m)
    generate_mention_anchors_trie(data_path)

    # 3.2 从 out_links 生成 train_kg
    generate_emb_train_kg(data_path)
    
    # 第四步
    # 4.1 全文统计 freq(m)
    for c in corpus_list: 
        _fm = calculate_freq_m(data_path, c)
    
    freq_m = merge_freq_m(data_path, corpus_list, is_save=True)

    # 4.2
    # TrainJointModel 训练 Embedding.
    train_embeddings(data_path, corpus_list, source, merge=True, train=True)
    # train_embeddings(data_path, corpus_list, source, merge=False, train=False)
    
    # 第五步
    # 5.1 根据 freq(m) refine mention_anchors.
    mention_anchors = refine_mention_anchors_by_freq_m(data_path)
    ma, tt = expand_mention_anchors_by_entity_dict(source, data_path, mention_anchors)
    
    # 5.2 过滤 link(m)<2 和 link_prob(m)<0.0001 的 mentions
    mention_anchors = filter_mention_anchors_by_len_and_prob(data_path, 0.0001, ma, None, None)
    # 5.3 从训练得到的词表 vocab_word 得到 vocab_word.trie
    generate_vocab_word_for_trie(data_path)

    # 第六步
    # 6.1 重新 expand mention anchors 得到没有统计值的 title_entities
    ma, tt = expand_mention_anchors_by_entity_dict(source, data_path, mention_anchors, is_save=True)
    _ = filter_title_entities(source, data_path)

    # 第七、八步
    # 7.1 生成 title_entities.txt 和 mention_anchors.txt
    #       - mention_anchors.txt
    #       - title_entities.txt
    generate_input_for_tries(data_path)

    # 7.2 & 8 生成三个概率文件
    #     - baidu_entity_prior.dat        entity::;prior
    #     - prob_mention_entity.dat       entity::;mention::;prob
    #     - link_prob.dat                 mention::;entity_id::;link(a)::;freq(a)::;link_prob::;p(e|m)
    generate_prob_files(data_path)

    # 9 生成各个字典树
    generate_tries(data_path)