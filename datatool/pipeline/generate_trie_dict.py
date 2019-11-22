import time
import datetime

def generate_mention_anchors_txt_for_trie(mention_anchors, mention_anchors_txt_path):
    print("\nGenerating file for building mention_anchor trie tree, target file path: \n\t{}"
          .format(mention_anchors_txt_path))
    start_at = int(time.time())
    with open(mention_anchors_txt_path, "w", encoding="utf-8") as wf:
        for mention in mention_anchors:
            if mention.strip() == "": continue
            anchors = [a for a in mention_anchors[mention].keys() if a != "__all__"]
            wf.write(mention + "::=" + "::=".join(anchors) + "\n")
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
