from evaluation.build_dataset.modules import SampleBuilder
from evaluation.build_dataset.modules import MentionParser
from evaluation.build_dataset.modules import OutputFormatter
from datatool.pipeline import extract_mention_anchors

source = "bd"
data_path = "/mnt/sdd/zxr/xlink/{}/".format(source)
entity_dict_path = data_path + "entity_id.txt"
entity_vec_path  = data_path + "emb/result300/vectors_entity"
word_vec_path    = data_path + "emb/result300/vectors_word"
mention_txt_path = data_path + "mention_anchors.txt"
mention_trie_path = data_path + "mention_anchors.trie"

doc = ""
mention_parser = MentionParser.TrieTreeMentionParser(mention_txt_path, mention_trie_path)
builder = SampleBuilder.SampleBuilder(source, entity_dict_path, entity_vec_path, word_vec_path)

def get_formatted_doc(doc):
    mention_list = mention_parser.parse_text(doc)
    mentions = builder.build_sample(mention_list, doc)

    doc_formatted_str = OutputFormatter.OutputFormatter.format(mentions, doc)
    return doc_formatted_str


corpus_name = "abstract"
corpus_path = data_path + "emb/train_text".format(corpus_name)
eval_annotation_path = data_path + "eval/annotations.txt"
docs = []

dataset_num = 100
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
            if counter >= dataset_num:
                break

f = open(data_path + "eval/docs.txt", "w", encoding="utf-8")
f.write("\n".format(docs))
f.close()