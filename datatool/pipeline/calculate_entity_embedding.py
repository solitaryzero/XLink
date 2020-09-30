import jieba
import time
import datetime
import traceback
import re
import struct
import numpy as np
from utils.mention import extract_mention_and_plain_text_from_annotated_doc

from tqdm import tqdm


def read_bytes_until_tab(fin):
    res = b''
    c = fin.read(1)
    while (c != b'\t') and (c != b'\n'):
        res += c
        c = fin.read(1)

    return res.decode('utf-8')


def read_binary_vectors(vector_path, debug=False):
    fin = open(vector_path, 'rb')
    status = fin.readline().strip().split()
    num_words = int(status[0])
    num_dim = int(status[1])

    vector_map = {}

    for i in tqdm(range(num_words)):
        word = read_bytes_until_tab(fin)
        vec = struct.unpack('f'*num_dim,fin.read(4*num_dim))
        fin.read(1)
        
        vec = np.array(vec)
        vector_map[word] = vec

        if (debug):
            print(word)
            print(vec)
            print(len(vec))
            input()
    
    fin.close()
    return vector_map, num_words, num_dim


def calculate_embedding_with_abstract(corpus_path, vector_path, out_path):
    """
    :param corpus_path: <instance_id>\t\t<document>
    :param vector_path: path to word embeddings
    :param out_path: path to store entity embeddings
    :return: none
    """
    print("Loading `bd` word embedding from vector file:\n\t{}".format(vector_path))
    vector_map, num_words, num_dim = read_binary_vectors(vector_path)
    print('Word num = %d, Word dim = %d' %(num_words, num_dim))

    print("Calculating `bd` entity embedding from standard corpus file:\n\t{}".format(corpus_path))
    counter, mode_cnt = 0, 100000
    start_time = int(time.time())
    last_update = start_time

    entity_vectors = {}
    entity_vec_writer = open(out_path, "wb")

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
                entity_vec = np.zeros(num_dim)
                for word in splitted_words:
                    entity_vec += vector_map.get(word, np.zeros(num_dim))
                
                entity_vec /= len(splitted_words)
                entity_vectors[instance_id] = entity_vec

            except Exception as e:
                traceback.print_exc()

    entity_vec_writer.write(('%d %d\n' %(len(entity_vectors), num_dim)).encode('utf-8'))

    for instance_id in entity_vectors:
        entity_vec = entity_vectors[instance_id]
        entity_vec_writer.write(('%s\t' %instance_id).encode('utf-8'))
        entity_vec_writer.write(struct.pack('f'*num_dim, *entity_vec))
        entity_vec_writer.write('\n'.encode('utf-8'))


    entity_vec_writer.close()

    print("Embedding generated, time: {}, saved to file:\n\t{}".format(
        str(datetime.timedelta(seconds=int(time.time()) - start_time)), out_path))