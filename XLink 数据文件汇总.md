# XLink 数据文件汇总

#### 1. 词向量
>文件位置：`/home/zj/EntityLinkingWeb/src/config.properties`

	vec_path.baidu_word='/home/zj/EntityLinkingWeb/data/baidu/vec_model/vectors_word'
	vec_path.baidu_entity='/home/zj/EntityLinkingWeb/data/baidu/vec_model/vectors_entity'
	vec_path.wiki_word='/home/zj/EntityLinkingWeb/data/wiki/vec_model/vectors_word'
	vec_path.wiki_entity='/home/zj/EntityLinkingWeb/data/wiki/vec_model/vectors_entity'

> **vector_word**: 第一行的格式 word_number$<space>$vector_dimension
> **entity_word**: 第一行的格式 entity_number$<space>$vector_dimension

---
>训练上述词向量的命令`demo-align.sh`
>文件位置：`/home/zj/EntityLinkingPreprocess/TrainJointModel/src/demo-align.sh`

	time ./align -train_text ../data/wiki/train_text -train_kg ../data/wiki/train_kg -train_anchor ../data/wiki/train_text -output_path ../data/wiki/result300/ -min-count 5 -   cw 0 -sg 1 -size 300 -negative 5 -sample 1e-4 -threads 24 -binary 1 -iter 10 -window 10

---
**因此需要准备的数据有**

1. /home/zj/EntityLinkingPreprocess/TrainJointModel/data/wiki/train_text **(wiki数据)**
2. /home/zj/EntityLinkingPreprocess/TrainJointModel/data/wiki/train_kg **(wiki数据)**
3. /home/zj/EntityLinkingPreprocess/TrainJointModel/data/train_text **(baidu数据)**
4. /home/zj/EntityLinkingPreprocess/TrainJointModel/data/train_kg **(baidu数据)**

---
#### 2. P(e), P(m|e), link_prob(a)

$$ link\_prob(a) = \frac{link(a)}{freq(a)}$$
$$ entity\ popularity = P(e) = \frac{A_{e,*}}{A_{*,*}} $$
$$ entity\ popularity\ to\ mention = P(e|m) = \frac{A_{e,m}}{A_{*,m}} $$
$$P(m|e) = \frac{A_{e,*}}{A_{e,m}}$$

**1). baiduEntityPriorFile**
- **文件位置**：/home/zj/EntityLinkingWeb/data/**baidu**/prob/baidu_entity_prior.dat
- **文件格式**：entity::;prior

**2) baiduMGivenEProbFile**
- **文件位置**：/home/zj/EntityLinkingWeb/data/**baidu**/prob/prob_mention_entity.dat
- **文件格式**：entity::;mention::;prob

**3) baiduLinkProbFile**
- **文件位置**：/home/zj/EntityLinkingWeb/data/**baidu**/prob/link_prob.dat
- **文件格式**：mention::;entity_id::;link(a)::;freq(a)::;link_prob::;entity_popularity

对应的wiki数据把路径以及文件名里的百度换为 wiki 即可。

#### 3. mention_anchor表以及 trie tree
1) mention_anchor 表
- **文件位置**：/home/zj/EntityLinkingPreprocess/BuildIndex/etc/baidu/dictionary_baidu.dat
- **文件格式**：mention::=anchor

根据 mention_anchor 表生成 trie tree

