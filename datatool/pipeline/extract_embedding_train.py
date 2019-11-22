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
    print("Extracting `bd` train text for embedding training from standard corpus file:\n\t{}".format(corpus_path))
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
                        else:
                            train_text += " ".join(tmp_mention) + " "
                        m_index += 1
                train_text_writer.write(train_text.strip() + "\n")
            except Exception as e:
                traceback.print_exc()
    train_text_writer.close()
    print("Train text extracted, time: {}, saved to file:\n\t{}".format(
        str(datetime.timedelta(seconds=int(time.time()) - start_time)), train_text_path))

def extract_wiki_corpus(corpus_path, train_text_path):
    """
    TODO: 这个函数没有验证有效性
    只需要把 mention 外的标点符号去掉就 ok，mention 和 instance_id 原样保留
    :param corpus_path:
    :param train_text_path:
    :return:
    """
    print("Extracting `wiki` train text for embedding training from standard corpus file:\n\t{}".format(corpus_path))
    train_text_writer = open(train_text_path, "w", encoding="utf-8")
    with open(corpus_path, "r", encoding="utf-8") as rf:
        counter, mode_cnt = 0, 100000
        start_time = int(time.time())
        last_update = start_time
        for line in rf:
            counter += 1
            if counter % mode_cnt == 0:
                curr_update = int(time.time())
                print("{}, time: {}, total_time: {}".format(counter,
                    str(datetime.timedelta(seconds=curr_update-last_update)),
                    str(datetime.timedelta(seconds=curr_update-start_time))
                ))
                last_update = curr_update
            try:
                instance_id, document = line.strip().split("\t\t")
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

                train_text_writer.write(train_text.strip() + "\n")
            except Exception:
                traceback.print_exc()
    train_text_writer.close()

def generate_train_kg_from_out_links(out_links, train_kg_path):
    print("\nGenerating train kg from out_links, train_kg_path: \n\t{}".format(train_kg_path))
    start_at = int(time.time())
    with open(train_kg_path, "w", encoding="utf-8") as wf:
        for i in out_links:
            if len(out_links[i]) > 0:
                wf.write(i + "\t" + ";".join(out_links[i]) + "\n")
    print("Generated, time: {}".format(str(datetime.timedelta(seconds=int(time.time())-start_at))))