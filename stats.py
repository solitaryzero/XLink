# coding: utf-8

import json
from datatool.pipeline import tools


def statistics_about_mention_anchors_and_out_links(mention_anchors, out_links, fout):
    from datatool.pipeline import tools
    import imp
    imp.reload(tools)

    # referred_entities = tools.cal_unique_anchors(mention_anchors)
    referred_entities = tools.cal_unique_refers(out_links)
    fout.write("mentions #{}\n".format(len(mention_anchors)))
    fout.write("anchors #{}\n".format(tools.cal_total_links(mention_anchors)))
    fout.write("unique_anchors #{}\n".format(len(tools.cal_unique_anchors(mention_anchors))))
    fout.write("referred entities: #{}\n".format(len(referred_entities)))
    fout.write("valid out links: #{}\n".format(len(out_links)))
    fout.write("candidate=1: #{}\n".format(tools.cal_mention_eq(mention_anchors, 1)))
    fout.write("candidate>1: #{}\n".format(tools.cal_mention_bigger(mention_anchors, 1)))
    fout.write("candidate>2: #{}\n".format(tools.cal_mention_bigger(mention_anchors, 2)))


def statistics_about_entities(entity_path, fout):
    with open(entity_path, 'r') as fin:
        lines = fin.readlines()
        fout.write("Total entities: %d\n" %len(lines))

    
def statistics_about_links(link_prob_path, fout):
    with open(link_prob_path, 'r') as fin:
        lines = fin.readlines()
        fout.write("Total valid links: %d\n" %len(lines))


if __name__ == "__main__":
    fout = open('./status.txt', 'w', encoding='utf-8')

    entity_path = '/mnt/sdd/zfw/xlink2020/bd/bd_instance_ID.txt'
    statistics_about_entities(entity_path, fout)

    with open('/mnt/sdd/zfw/xlink2020/bd/mention_anchors.json') as fin:
        mention_anchors = json.load(fin)

    with open('/mnt/sdd/zfw/xlink2020/bd/out_links.json') as fin:
        out_links = json.load(fin)

    statistics_about_mention_anchors_and_out_links(mention_anchors, out_links, fout)

    link_prob_path = '/mnt/sdd/zfw/xlink2020/bd/link_prob.dat'
    statistics_about_links(link_prob_path, fout)

    fout.close()