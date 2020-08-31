
import warnings
import logging
import os.path
import sys
import multiprocessing
import re
from tqdm import tqdm

import gensim
from gensim.models import Word2Vec
from gensim.models.word2vec import LineSentence

logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s',level=logging.INFO)

import jieba


def genPlainText(inpath, outpath):
    def getAnchor(matched):
        x = matched.group(1)
        l = list(jieba.cut(x))
        return ' '.join(l)

    with open(inpath, 'r', encoding='utf-8') as fin:
        with open(outpath, 'w', encoding='utf-8') as fout:
            lines = fin.readlines()
            for line in tqdm(lines):
                nline = re.sub(r'\[\[.+\|(.+)\]\]', getAnchor, line.strip())
                fout.write(nline)
                fout.write('\n')


def trainw2v(fin, fout_model, fout_vector):
    model = Word2Vec(LineSentence(inp), size=50, window=5, min_count=5,
                     workers=multiprocessing.cpu_count())
 
    # 保存模型
    model.save(out_model)
    # 保存词向量
    model.wv.save_word2vec_format(out_vector, binary=False)


def genUnprocessedPlainText(inpath, outpath, append=False):
    def getAnchor(matched):
        x = matched.group(1)
        return x

    with open(inpath, 'r', encoding='utf-8') as fin:
        if (append):
            fout = open(outpath, 'a', encoding='utf-8')
        else:
            fout = open(outpath, 'w', encoding='utf-8')

        lines = fin.readlines()
        for line in tqdm(lines):
            content = line.strip().split('\t\t')[1]

            paras = content.split('::;')
            for para in paras:
                nline = re.sub(r'\[\[.+\|(.+)\]\]', getAnchor, para)
                fout.write(nline)
                fout.write('\n')

            fout.write('\n')

        fout.close()


if __name__ == "__main__":
    '''
    inp = '/mnt/sdd/zfw/xlink2020/bd/emb/train_text'
    out_model = '/mnt/sdd/zfw/xlink2020/bd/w2v/entity.model'
    out_vector = '/mnt/sdd/zfw/xlink2020/bd/w2v/entity.vector'
    logging.info('Training vector with entities')
    trainw2v(inp, out_model, out_vector)


    genPlainText('/mnt/sdd/zfw/xlink2020/bd/emb/train_text', '/mnt/sdd/zfw/xlink2020/bd/emb/train_text_plain')

    inp = '/mnt/sdd/zfw/xlink2020/bd/emb/train_text_plain'
    out_model = '/mnt/sdd/zfw/xlink2020/bd/w2v/plain.model'
    out_vector = '/mnt/sdd/zfw/xlink2020/bd/w2v/plain.vector'
    logging.info('Training vector with plain text')
    trainw2v(inp, out_model, out_vector)
    '''

    genUnprocessedPlainText('/mnt/sdd/zfw/xlink2020/bd/standard_abstract.txt', '/mnt/sdd/zfw/xlink2020/bd/emb/train_text_plain')
    genUnprocessedPlainText('/mnt/sdd/zfw/xlink2020/bd/standard_article.txt', '/mnt/sdd/zfw/xlink2020/bd/emb/train_text_plain', append=True)
    genUnprocessedPlainText('/mnt/sdd/zfw/xlink2020/bd/standard_infobox.txt', '/mnt/sdd/zfw/xlink2020/bd/emb/train_text_plain', append=True)