# XLink
*Entity Linking System from KEG*

[![XLink](https://img.shields.io/badge/XLink-Web-blue)](https://xlink.xlore.org)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/c0ff3cc16611479f8920c00e552e5c82)](https://www.codacy.com/manual/XinruZhang/XLink?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=XinruZhang/XLink&amp;utm_campaign=Badge_Grade)

## 1. XLink Data Update Tool

Generate necessary data for XLink from Wikipedia and Baidu Bake. The
process is shown in the Fig below, and for the detailed codes, please
check `./datatool/main.py`.

通过数据更新工具生成的文件对应的 XLink 项目路径详见
[XLink 数据文件汇总 V1](https://github.com/XinruZhang/XLink/blob/master/XLink%20数据文件汇总.md)。

1. 从 raw_corpus 得到 standard corpus。对于 infobox，需要先从 pre_raw_corpus 得到 raw_corpus.
2. 从 standard corpus 中抽取 mention_anchors 和 out_links.
3. 根据 mention_anchors 构建 mention_anchors.trie，用于计算 freq(m)
4. 用 freq(m) 来 refine 第 2 步得到的 mention_anchors
5. 过滤 mention_anchors，过滤掉 link(m)<2, link_prob<0.0001 的 mentions. 得到新的 mention_anchors.
6. 扩展新得到的 mention_anchors，同时得到 title_entities：将 entity 中去掉括号的 title 作为 mention 在 mention_anchors 中出现过，但是该实体本身并没有在文本中以 title 为 mention 被引用过，则将其加入到 mention_anchors 中。
7. 根据 mention_anchors 计算概率，生成字典树和三个概率文件

<img src="./assets/pipeline.png" alt="Update Process" style="width:100%" />


## 2. XLink Predictor

The prediction method of XLink can be found in
`modules.prob_gm_predictors.xlink`.

The basic idea is maximizing $P(e|m, C, N) = P(e|m)*P(e|C) * P(e|N)$,
where $P(e|m)$ is counted from Wikipedia corpus, $P(e|C) =
\frac{1}{m}\sum_{w_i\in C} cos\_sim(e, w_i)$, $C$ is the context of the
given mention, $P(e|N) = \frac{1}{n}\sum_{e_i\in N} cos\_sim(e, e_i)$,
$N$ is the context disambiguous mentions' entities.

## Ref

\[1\].
[XLink 数据更新文档 V1](https://github.com/XinruZhang/XLink/blob/master/XLink%20数据更新文档.md)

\[2\].
[XLink 数据文件汇总 V1](https://github.com/XinruZhang/XLink/blob/master/XLink%20数据文件汇总.md)

\[3\]. [The online web service of XLink](https://xlink.xlore.org/).