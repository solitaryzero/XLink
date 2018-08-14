### XLink 数据更新文档
XLink 数据更新流程详细说明文档，需要了解每个数据文件的格式，可参照[XLink 数据文件汇总](https://github.com/XinruZhang/XLink/blob/master/XLink%20数据文件汇总.md)。

#### 0. 准备标准输入数据
XLink 数据生成是一个流程化的过程，有了标准输入数据之后，可一次性生成所有基础文件。

标准输入数据是经过处理过的百度百科和维基百科数据，具体的数据格式为：
`title\t\tsub_title\t\tentity_id\t\tfulltext`

其中，fulltext 是原文的分词结果，`[[mention|anchor]]`表示一个实体

	# baidu_input.txt
	海鸥            （契诃夫的剧本）                /item/海鸥/1342809              出版 时间 [[11|/item/11%E5%AF%B9%E6%88%98%E5%B9%B3%E5%8F%B0/6602849?fromtitle=11&fromid=8270434]] 印刷 时间 装订 精装 简介 [[俄罗斯|/item/%E4%BF%84%E7%BD%97%E6%96%AF/125568]] 作家 [[安东尼·巴甫洛维奇·契诃夫|/item/%E5%AE%89%E4%B8%9C%C2%B7%E5%B7%B4%E7%94%AB%E6%B4%9B%E7%BB%B4%E5%A5%87%C2%B7%E5%A5%91%E8%AF%83%E5%A4%AB/5048959?fromtitle=%E5%AE%89%E4%B8%9C%E5%B0%BC%C2%B7%E5%B7%B4%E7%94%AB%E6%B4%9B%E7%BB%B4%E5%A5%87%C2%B7%E5%A5%91%E8%AF%83%E5%A4%AB&fromid=3779962]] 创作 于 同名 四幕 话剧 故事 背景 是 沙俄 统治 时期 俄国 讲述 在 庄园 里 青年 作家 特里波列夫 和 想 要 成为 演员 女 青年妮娜 故事

	# wiki_input.txt 
	Actrius         _placeholder_           Actrius         In order to prepare herself to play a role commemorating the life of legendary actress Empar Ribera young actress [[Mercè Pons]]  interviews three established actresses who had been the Riberas pupils the international diva Glòria Marc [[Núria Espert]]  the television star Assumpta Roca [[Rosa Maria Sardà]]  and dubbing director Maria Caminal [[Anna Lizaran]]  [[Núria Espert]]  as Glòria Marc  [[Rosa Maria Sardà]]  as Assumpta Roca  [[Anna Lizaran]]  as Maria Caminal  [[Mercè Pons]]  as Estudiant==Actrius screened in 2001 at the [[Grauman's Egyptian Theatre]]  in an [[American Cinematheque]]  retrospective of the works of its director The film had first screened at the same location in 1998 It was also shown at the 1997 [[Stockholm International Film Festival]] ==In Movie  Film  Review [[Daily Mail]]  staffer Christopher Tookey wrote that though the actresses were competent in roles that may have some reference to their own careers  the film is visually unimaginative never escapes its stage origins and is almost totally lacking in revelation or surprising incident  Noting that there were occasional refreshing moments of intergenerational bitchiness  they did not justify comparisons to [[All About Eve]]   and were insufficiently different to deserve critical parallels with [[Rashomon]]   He also wrote that [[The Guardian]]  called the film a slow stuffy chamberpiece  and that [[The Evening Standard]]  stated the films best moments exhibit the bitchy tantrums seething beneath the threesomes composed veneers  [[MRQE]]  wrote This cinematic adaptation of a theatrical work is true to the original but does not stray far from a theatrical rendering of the story== 1997 won Best Catalan Film at [[Butaca Awards]]  for [[Ventura Pons]]   1997 won Best Catalan Film Actress at Butaca Awards shared by [[Núria Espert]]  [[Rosa Maria Sardà]]  [[Anna Lizaran]]  and [[Mercè Pons]]   1998 nominated for Best Screenplay at [[Goya Awards]]  shared by [[Josep Maria Benet i Jornet]]  and Ventura Pons  [[Wayback Machine|as archived February 17, 2009]]  Spanish

*这一版本(2018.8)预处理代码在(18服务器)`/home/xlore/xlink/DataPrepare`项目中，运行命令 `ant StandardizeV1` 可生成标准输入数据。*

#### 1. Generator.py 生成基础数据
项目路径(18服务器)：/home/xlore/xlink/DataPrepare/

**I. 生成基础数据**
运行 Generator.py
*在里面可以配置输入输出文件夹和文件名，处理的语料库(baidu/wiki)*等

可生成如下文件：
output_dir/baidu/entity_prior
output_dir/baidu/link_prob
output_dir/baidu/m_given_e
output_dir/baidu/mention_anchor
output_dir/baidu/train_kg
output_dir/baidu/train_text

> ps: 上述是百度百科生成的数据文件，将路径中的 baidu 换为 wiki，即为维基百科的生成数据。
pss: 本版本(2018.8)的 output_dir 是 data/production

前三个文件可直接用于 XLink，后三个文件需要进行进一步处理。其中，train_kg, train_text 用于训练词向量和实体向量，mention_anchor 用于生成 AC Trie Tree.

**II. 将 entity_prior, link_prob, m_given_e 移到XLink的项目路径**
a. entity_prior 移到 /home/zj/EntityLinkingWeb/data/baidu/prob/baidu_entity_prior.dat
b. m_given_e 移到 /home/zj/EntityLinkingWeb/data/baidu/prob/prob_mention_entity.dat
c. link_prob 移到 /home/zj/EntityLinkingWeb/data/baidu/prob/link_prob.dat

#### 2. 词向量与实体向量
项目路径(68服务器)：/home/zj/EntityLinkingPreprocess/TrainJointModel

**I. 将基础数据的 train_kg, train_text 移到向量训练项目中** 
路径可根据下面一步中的程序（`demo-align.sh`）进行配置

**II. 通过训练语料训练向量表示 **
配置并运行程序：./src/demo-align.sh 
*通过修改 `demo-align.sh`中的参数来配置训练语料的文件路径*

**III. 将生成的向量复制到项目中的使用位置(68服务器) **
/home/zj/EntityLinkingWeb/data/baidu/vec_model/vectors_word
/home/zj/EntityLinkingWeb/data/baidu/vec_model/vectors_entity
/home/zj/EntityLinkingWeb/data/wiki/vec_model/vectors_word
/home/zj/EntityLinkingWeb/data/wiki/vec_model/vectors_entity

ps: 注意备份


#### 3. AC 自动机的 Trie Tree
**I. 生成初始语料：mention_anchor 表**
与词向量的训练语料一样，本步骤可以与其他文件一起生成（Generator.py）。
程序路径(18服务器): /home/xlore/xlink/DataPrepare/Generator.py

**II. 通过 mention_anchor 表生成 AC Trie Tree**
a. 打开项目路径(68服务器): /home/zj/EntityLinkingPreprocess/BuildIndex
b. 编辑文件 ./src/main/BuildBaiudAll.java，配置相关参数
c. 运行 `ant` 编译后，再运行 `ant BuildBaiudAll` 生成 Trie Tree

**III. 将生成好的 .trie 文件保存到 XLink 项目的使用位置(68服务器)**
/home/zj/EntityLinkingWeb/data/baidu/trie/baidu.trie
/home/zj/EntityLinkingWeb/data/wiki/trie/wiki.trie
/home/zj/EntityLinkingWeb/data/baidu/trie/baidu_word.trie（不知道怎么生成，好像也没用到）
/home/zj/EntityLinkingWeb/data/wiki/trie/wiki_word.trie（不知道怎么生成，好像也没用到）
