def extract_mention_and_plain_text_from_annotated_doc(document):
    """
    从标准标注数据得到 mention_anchor 列表和 plain_text, for example:

    document = "《海鸥》是网剧《[[bdi1697355|南北兄弟]]》插曲，由[[bdi7840364|顾峰]]、清源作词，顾峰作曲，[[bdi2647186|孟瑞]]演唱"

    mention_anchor = [['南北兄弟', 'bdi1697355', 8],
                      ['顾峰', 'bdi7840364', 17],
                      ['孟瑞', 'bdi2647186', 30]],
    plain_text = "《海鸥》是网剧《南北兄弟》插曲，由顾峰、清源作词，顾峰作曲，孟瑞演唱"

    :param document: string
    :return: list(), string
    """
    plain_text = ""
    mention_anchor_list = []

    split_segs = document.split("[[")
    if len(split_segs) < 2:
        return mention_anchor_list, document

    plain_text += split_segs[0]

    for seg_index in range(1, len(split_segs)):
        seg = split_segs[seg_index]
        seg_segs = seg.split("]]")
        
        instance_id, mention = seg_segs[0].split("|", 1)

        mention_anchor_list.append([mention, instance_id, len(plain_text)])
        plain_text += mention

        if len(seg_segs) > 1:
            plain_text += seg_segs[1]
    return mention_anchor_list, plain_text

