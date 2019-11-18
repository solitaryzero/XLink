import re


punctuations = "!！?？/\'\".,:()\-\n·;。＂＃＄％＆＇（）＊＋，－／：；＜＝=＞＠［＼］＾＿｀｛｜｝{|}～｟｠｢｣､、〃《》<>「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…‧﹏"


def cal_unique_anchors(mention_anchors):
    """
        计算词表中有多少个实体

    :param mention_anchors:
    :return:
    """
    inst = set()
    for m in mention_anchors:
        for i in mention_anchors[m]:
            inst.add(i)
    return inst


def trim_train_text_punctuations(train_text_line, punctuations):
    trimmed_line = ""
    splitted_segs = train_text_line.split("[[")
    # add splitted_segs[0] to trimmed_train_text
    for c in splitted_segs[0]:
        if c not in punctuations:
            trimmed_line += c
    if len(splitted_segs) > 1:
        index = 1
        while index < len(splitted_segs):
            seg = splitted_segs[index]
            seg_segs = seg.split("]]")
            trimmed_line += "[[" + seg_segs[0] + "]]"
            if len(seg_segs) > 1:
                for c in seg_segs[1]:
                    if c not in punctuations:
                        trimmed_line += c
            index += 1
    trimmed_line_arr = trimmed_line.split(" ")
    trimmed_line = ""
    for item in trimmed_line_arr:
        if item != '':
            trimmed_line += item + " "
    return trimmed_line.strip()


def cal_mention_eq(mention_anchors, th):
    """
        计算词表中 candidate 数量 == th 的 mention 数量
    :param mention_anchors:
    :param th:
    :return:
    """
    c = 0
    for m in mention_anchors:
        if len(mention_anchors[m]) == th:
            c += 1
    return c


def cal_mention_bigger(mention_anchors, th):
    """
        计算词表中 candidate 数量 > th 的 mention 数量

    :param mention_anchors:
    :param th:
    :return:
    """
    c = 0
    for m in mention_anchors:
        if len(mention_anchors[m]) > th:
            c += 1
    return c


def cal_valid_out_links(out_links):
    valid_ol = dict()
    for i in out_links:
        if len(out_links[i]) > 0:
            valid_ol[i] = out_links[i]
    return valid_ol


def cal_linked_entities(out_links):
    inst = set()
    for i in out_links:
        for o in out_links[i]:
            inst.add(o)
    return inst