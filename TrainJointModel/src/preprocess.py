import nltk as nk
import codecs
import regex as re
import datetime

anchor_p = r"\[\[((?>[^\[\]]+|(?R))*)\]\]"
anchor_text_p = r'(?<=\[\[).*?(?=\]\])'
trim_href_p = r"(^.+?\t\t)|(=+References=+(.*)$)|(\[http(.*?)\])"
anchor_split_p = r'\|'
eng_p = r'[a-zA-Z]+'
num_p = r'[0-9]+'
brace_p = r'\(.*?\)'
para_p = r'={2,}'

ent_half_window = 10

file_input = '../data/zhwiki/zhwiki-abstract.dat'
corpus = '../data/zhwiki/zhwiki_train_text_ab'
anchors = '../data/zhwiki/zhwiki_train_anchors_ab'

def toWord(anchor_text, ent_dic):
    items = re.split(anchor_split_p, re.search(anchor_text_p, anchor_text).group())
    if len(items) <= 2:
        re_word = re.sub(brace_p, "", items[0]).strip().replace(' ', '_')
        ent_dic[re_word] = items[0]
        return re_word
    else:
        return None

def segment(sent, words):
    tmp_words = nk.tokenize.word_tokenize(sent)
    for word in tmp_words:
        if re.match(eng_p, word):
            words.append(word)
        elif re.match(num_p, word):
            words.append("ddd")

with codecs.open(file_input, 'r', encoding='UTF-8') as fin:
    with codecs.open(corpus, 'w', encoding='UTF-8') as fout_text:
        with codecs.open(anchors, 'w', encoding='UTF-8') as fout_anchors:
            line_count = 0;
            texts = []
            anchors = []
            starttime = datetime.datetime.now()
            for line in fin:
                line_count += 1
                if line_count%10000 == 0 :
                    endtime = datetime.datetime.now()
                    print("has processed: %d lines, takes %d seconds..." % (line_count, (endtime - starttime).seconds))
                # split the paragraphs after removing references, head entity and href
                paras = re.split(para_p, re.sub(trim_href_p, "", line.lower()))
                for para in paras:
                    sent_pos = 0
                    words_set = []
                    entity_index = []
                    ent_dic = {}
                    # skip the para within length of 30 or Nonetype
                    if not para or len(para) <=30:
                        continue
                    # iterate all the anchors in wiki text
                    for anchor in re.finditer(anchor_p, para):
                        segment(para[sent_pos:anchor.start()], words_set)
                        anchor_word = toWord(anchor.group(), ent_dic)
                        if anchor_word:
                            entity_index.append(len(words_set))
                            words_set.append(anchor_word)
                        sent_pos = anchor.end()
                    if sent_pos < len(para):
                        segment(para[sent_pos:len(para)], words_set)
                    if len(words_set) > 8:
                        texts.append(" ".join(words_set)+"\n")
                        if len(texts) >= 10000:
                            fout_text.writelines(texts)
                            del texts[:]
                    for i in entity_index:
                        anchors.append(ent_dic[words_set[i]]+"\t\t"+";".join(reversed(words_set[max(0,i-ent_half_window-1):i]))+"\n")
                        anchors.append(ent_dic[words_set[i]] + "\t\t"+";".join(words_set[i+1:min(len(words_set), i+1+ent_half_window)])+"\n")
                        if len(anchors) >= 10000:
                            fout_anchors.writelines(anchors)
                            del anchors[:]
            if len(texts) > 0:
                fout_text.writelines(texts)
            if len(anchors) > 0:
                fout_anchors.writelines(anchors)
