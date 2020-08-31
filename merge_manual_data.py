import os, json
from datatool.pipeline.generate_prob_files import Parser
from jpype import *
import argparse

def init_JVM():
    from config import Config
    jar_path = Config.project_root + "data/jar/BuildIndex.jar"

    if not isJVMStarted():
        startJVM(getDefaultJVMPath(), "-Djava.class.path=%s" % jar_path)
    if not isThreadAttachedToJVM():
        attachThreadToJVM()
    JDClass = JClass("edu.TextParser")
    return JDClass


def merge_mention_anchors(orig_anchor_file, manual_anchor_file, new_anchor_file, new_anchor_trie, JDClass):
    mention_anchor_map = {}
    with open(orig_anchor_file, 'r', encoding="utf-8") as fin:
        for line in fin:
            words = line.strip().split('::=')
            mention = words[0]
            mention_anchor_map[mention] = set()
            for ent in words[1:]:
                mention_anchor_map[mention].add(ent)
    
    with open(manual_anchor_file, 'r', encoding="utf-8") as fin:
        pass

    with open(new_anchor_file, 'w', encoding="utf-8") as fout:
        for mention in mention_anchor_map:
            fout.write(mention)
            for ent in mention_anchor_map[mention]:
                fout.write('::='+ent)
            fout.write('\n')

    if (os.path.exists(new_anchor_trie)):
        os.remove(new_anchor_trie)

    parser = Parser.get_instance(new_anchor_file, new_anchor_trie, JDClass)


def merge_link_prob(orig_link_file, manual_anchor_file, new_link_file):
    link_prob_map = {}
    with open(orig_link_file, 'r', encoding="utf-8") as fin:
        for line in fin:
            words = line.strip().split('::;')
            mention = words[0]
            ent = words[1]
            freq_m = int(words[2])
            freq_w = int(words[3])
            link_prob = float(words[4])
            prior_prob = float(words[5])
            link_prob_map[(mention, ent)] = (freq_m, freq_w, link_prob, prior_prob)

    with open(manual_anchor_file, 'r', encoding="utf-8") as fin:
        pass

    with open(new_link_file, 'w', encoding="utf-8") as fout:
        for mention, ent in link_prob_map:
            freq_m, freq_w, link_prob, prior_prob = link_prob_map[(mention, ent)]
            fout.write('%s::;%s::;%d::;%d::;%f::;%f\n' %(mention, ent, freq_m, freq_w, link_prob, prior_prob))


if __name__ == "__main__":
    source, corpus_name = "bd", "abstract"
    # data_path       = "/mnt/sdd/zxr/xlink/{}/".format(source)
    data_path = '/mnt/sdd/zfw/xlink2020/%s/' %(source)
    JDClass = init_JVM()

    manual_data_file = os.path.join(data_path, "")

    title_entity_txt_path = os.path.join(data_path, "mention_anchors.txt")
    new_title_entity_txt_path = os.path.join(data_path, "mention_anchors_new.txt")
    new_title_entity_trie_path = os.path.join(data_path, "mention_anchors_new.trie")

    merge_mention_anchors(title_entity_txt_path, manual_data_file, new_title_entity_txt_path, new_title_entity_trie_path, JDClass)

    link_prob_path = os.path.join(data_path, "link_prob.dat")
    new_link_prob_path = os.path.join(data_path, "link_prob_new.dat")
    merge_link_prob(link_prob_path, manual_data_file, new_link_prob_path)

    shutdownJVM()