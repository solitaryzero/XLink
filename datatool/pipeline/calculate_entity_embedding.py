# TODO
import jieba
import time
import datetime
import traceback
import re
from utils.mention import extract_mention_and_plain_text_from_annotated_doc


def calculate_embedding_with_abstract(corpus_path, out_path):
    """
    :param corpus_path: <instance_id>\t\t<document>
    :param out_path: path to store embeddings
    :return: none
    """
    print("Calculating `bd` entity embedding from standard corpus file:\n\t{}".format(corpus_path))
    counter, mode_cnt = 0, 100000
    start_time = int(time.time())
    last_update = start_time

    with open(corpus_path, "r", encoding="utf-8") as rf:
        for line in rf:
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

                # 2020.8.20 strip spaces between chinese words
                document = re.sub(r'([^a-zA-Z])( )([^a-zA-Z])', r'\1\3', document)
                document = document.lower()

                mention_anchor_list, plain_doc = extract_mention_and_plain_text_from_annotated_doc(document)

                splitted_words = list(jieba.cut(plain_doc))



            except Exception as e:
                traceback.print_exc()

    print("Embedding generated, time: {}, saved to file:\n\t{}".format(
        str(datetime.timedelta(seconds=int(time.time()) - start_time)), out_path))