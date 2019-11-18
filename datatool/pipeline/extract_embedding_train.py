import jieba
import time
import datetime
import traceback
from utils.mention import extract_mention_and_plain_text_from_annotated_doc


punctuations = "!！?？/\'\".,:()\-\n·;。＂＃＄％＆＇（）＊＋，－／：；＜＝=＞＠［＼］＾＿｀｛｜｝{|}～｟｠｢｣､、〃《》<>「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…‧﹏"


def extract_bd_corpus(corpus_path, train_text_path):
    """
    :param corpus_path: <instance_id>\t\t<document>
    :param train_text_path:
    :return: mention_anchors, out_links
    """
    mention_anchors = dict()
    inst_out_links  = dict()
    exception_lines = list()

    counter, mode_cnt = 0, 100000
    start_time = int(time.time())
    last_update = start_time

    train_text_writer = open(train_text_path, "w", encoding="utf-8")
    with open(corpus_path, "r", encoding="utf-8") as rf:
        for line in rf:
            train_text = ""
            counter += 1
            if counter % mode_cnt == 0:
                curr_update = int(time.time())
                print("#{}, time: {}, total_time: {}".format(
                    counter,
                    str(datetime.timedelta(seconds=curr_update-last_update)),
                    str(datetime.timedelta(seconds=curr_update-start_time))
                ))
                last_update = curr_update
            try:
                instance_id, document = line.strip().split("\t\t")
                mention_anchor_list, plain_doc = extract_mention_and_plain_text_from_annotated_doc(document)
                if inst_out_links.get(instance_id) is None:
                    inst_out_links[instance_id] = set()

                # seg = pkuseg.pkuseg()
                # splitted_words = seg.cut(plain_doc)
                splitted_words = list(jieba.cut(plain_doc))

                offset, m_index, s_index = 0, 0, 0

                while s_index < len(splitted_words):
                    word = splitted_words[s_index]
                    if m_index >= len(mention_anchor_list):
                        if word not in punctuations:
                            train_text += word + " "
                        s_index += 1
                        continue

                    mention_item = mention_anchor_list[m_index]
                    if offset < mention_item[2]:
                        if word not in punctuations:
                            train_text += word + " "
                        offset += len(word)
                        s_index += 1
                    elif offset > mention_item[2]:
                        m_index += 1
                    else: # offset == mention_item[2], the start position of mention in the plain document.
                        tmp_mention = []

                        while s_index < len(splitted_words) and offset < mention_item[2] + len(mention_item[0]):
                            word = splitted_words[s_index]
                            tmp_mention.append(word)
                            offset += len(word)
                            s_index += 1

                        # 如果 mention 的分词边界没有问题
                        if offset == mention_item[2] + len(mention_item[0]) and \
                                ''.join(tmp_mention) == mention_item[0]:
                            mention = ''.join(tmp_mention)
                            train_text += "[[{}|{}]] ".format(instance_id, mention)
                            if mention_anchors.get(mention) is None:
                                mention_anchors[mention] = dict()
                            if mention_anchors[mention].get(mention_item[1]) is None:
                                mention_anchors[mention][mention_item[1]] = 0
                            mention_anchors[mention][mention_item[1]] += 1
                            inst_out_links[instance_id].add(mention_item[1])
                        else:
                            train_text += " ".join(tmp_mention) + " "
                        m_index += 1
                train_text_writer.write(train_text.strip() + "\n")
            except Exception as e:
                traceback.print_exc()
                print("Exception Line: {}".format(line))
                exception_lines.append(line)

    train_text_writer.close()

    return mention_anchors, inst_out_links, exception_lines

def extract_wiki_corpus(corpus_path, train_text_path):
    """
    只需要把 mention 外的标点符号去掉就 ok，mention 和 instance_id 原样保留
    :param corpus_path:
    :param train_text_path:
    :return:
    """
    mention_anchors = dict()
    out_links = dict()
    exception_lines = []

    train_text_writer = open(train_text_path, "w", encoding="utf-8")
    with open(corpus_path, "r", encoding="utf-8") as rf:
        counter, mode_cnt = 0, 100000
        start_time = int(time.time())
        last_update = start_time
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
                instance_id, document = line.strip().split("\t\t")
                if out_links.get(instance_id) is None:
                    out_links[instance_id] = set()

                train_text = ""

                split_segs = document.split("[[")
                if len(split_segs) < 2:
                    train_text_writer.write(document + "\n")
                    continue

                for item in split_segs[0].lower():
                    if item not in punctuations:
                        train_text += item

                for seg_index in range(1, len(split_segs)):
                    seg = split_segs[seg_index]
                    seg_segs = seg.split("]]")

                    train_text += "[[" + seg_segs[0] + "]] "
                    if len(seg_segs) > 1:
                        for item in seg_segs[1].lower():
                            if item not in punctuations:
                                train_text += item

                    anchor, mention = seg_segs[0].split("|")
                    if mention_anchors.get(mention) is None:
                        mention_anchors[mention] = dict()
                    if mention_anchors[mention].get(anchor) is None:
                        mention_anchors[mention][anchor] = 0
                    mention_anchors[mention][anchor] += 1
                    out_links[instance_id].add(anchor)

                train_text_writer.write(train_text.strip() + "\n")
            except Exception:
                traceback.print_exc()
                exception_lines.append(line)

    return mention_anchors, out_links, exception_lines

def generate_train_kg_from_out_links(out_links, train_kg_path):
    with open(train_kg_path, "w", encoding="utf-8") as wf:
        for i in out_links:
            if len(out_links[i]) > 0:
                wf.write(i + "\t" + ";".join(out_links[i]) + "\n")