import os
import ahocorasick
import pickle
from tqdm import tqdm


def build_trie(txt_path, trie_path):
    A = ahocorasick.Automaton(ahocorasick.STORE_ANY, ahocorasick.KEY_STRING)
    with open(txt_path, 'r', encoding='utf-8') as fin:
        lines = fin.readlines()
        for line in tqdm(lines):
            words = line.strip().split('::=')
            if (len(words) < 2):
                continue

            mention = words[0]
            # eids = words[1:]
            A.add_word(mention, words)

    A.make_automaton()
    A.save(trie_path, pickle.dumps)


if __name__ == "__main__": 
    source = "bd"
    data_path = '/mnt/sdd/zfw/xlink2020/%s/' %(source)

    title_entity_txt_path = os.path.join(data_path, "title_entities.txt")
    title_entity_trie_path = os.path.join(data_path, "title_entities.pytrie")
    build_trie(title_entity_txt_path, title_entity_trie_path)

    mention_txt_path = os.path.join(data_path, "mention_anchors.txt")
    mention_trie_path = os.path.join(data_path, "mention_anchors.pytrie")
    build_trie(mention_txt_path, mention_trie_path)

    vocab_txt_path = os.path.join(data_path, "vocab_word.txt")
    vocab_trie_path = os.path.join(data_path, "vocab_word.pytrie")
    build_trie(vocab_txt_path, vocab_trie_path)