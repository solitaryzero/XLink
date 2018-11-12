# XLink 数据更新文档

XLink 数据更新流程详细说明文档，需要了解每个数据文件的格式，可参照 [XLink 数据文件汇总](https://github.com/XinruZhang/XLink/blob/master/XLink%20数据文件汇总.md)。

**XLink 的数据生成是一个流程化过程**

- 0. 【原始语料处理】首先对原始语料进行处理，得到本程序的标准输入数据。
- 1. 【基础数据生成】得到标准输入数据后，数据生成程序会对其进行处理，得到 XLink 系统需要的基础数据文件，或中间文件（经过进一步处理可得到系统需要的基础数据文件的文件）。
- 2. 【中间文件处理】随后，对于中间文件进行处理，包括 1. 词向量与实体向量的生成; 2. AC Trie Tree 的构建; 3. Xlore Url Map 的生成。
- 3. 【配置系统数据文件】生成所有系统需要的数据后，将其配置到系统中相应的位置。

## 0. 原始语料处理
- **项目路径**: `/home/xlore/xlink/DataPrepare`
- **运行方式**: `ant` 随后 `ant StandardizeV1`
- **输入**: 文件来源 `/home/xlore/Wikipedia20180301/1_extraction/_article.txt`，路径可在 `./src/pre/Standardize.java` 里进行配置
- **输出**：格式 `title\t\tsub_title\t\tentity_id\t\tfulltext`，路径可在 `./src/pre/Standardize.java` 里进行配置。fulltext 是原文的分词结果，fulltext 中 `[[mention|anchor]]`表示一个实体

输出实例

```
# baidu_input.txt
海鸥            （契诃夫的剧本）                /item/海鸥/1342809              出版 时间 [[11|/item/11%E5%AF%B9%E6%88%98%E5%B9%B3%E5%8F%B0/6602849?fromtitle=11&fromid=8270434]] 印刷 时间 装订 精装 简介 [[俄罗斯|/item/%E4%BF%84%E7%BD%97%E6%96%AF/125568]] 作家 [[安东尼·巴甫洛维奇·契诃夫|/item/%E5%AE%89%E4%B8%9C%C2%B7%E5%B7%B4%E7%94%AB%E6%B4%9B%E7%BB%B4%E5%A5%87%C2%B7%E5%A5%91%E8%AF%83%E5%A4%AB/5048959?fromtitle=%E5%AE%89%E4%B8%9C%E5%B0%BC%C2%B7%E5%B7%B4%E7%94%AB%E6%B4%9B%E7%BB%B4%E5%A5%87%C2%B7%E5%A5%91%E8%AF%83%E5%A4%AB&fromid=3779962]] 创作 于 同名 四幕 话剧 故事 背景 是 沙俄 统治 时期 俄国 讲述 在 庄园 里 青年 作家 特里波列夫 和 想 要 成为 演员 女 青年妮娜 故事

# wiki_input.txt 
Actrius         _placeholder_           Actrius         In order to prepare herself to play a role commemorating the life of legendary actress Empar Ribera young actress [[Mercè Pons]]  interviews three established actresses who had been the Riberas pupils the international diva Glòria Marc [[Núria Espert]]  the television star Assumpta Roca [[Rosa Maria Sardà]]  and dubbing director Maria Caminal [[Anna Lizaran]]  [[Núria Espert]]  as Glòria Marc  [[Rosa Maria Sardà]]  as Assumpta Roca  [[Anna Lizaran]]  as Maria Caminal  [[Mercè Pons]]  as Estudiant==Actrius screened in 2001 at the [[Grauman's Egyptian Theatre]]  in an [[American Cinematheque]]  retrospective of the works of its director The film had first screened at the same location in 1998 It was also shown at the 1997 [[Stockholm International Film Festival]] ==In Movie  Film  Review [[Daily Mail]]  staffer Christopher Tookey wrote that though the actresses were competent in roles that may have some reference to their own careers  the film is visually unimaginative never escapes its stage origins and is almost totally lacking in revelation or surprising incident  Noting that there were occasional refreshing moments of intergenerational bitchiness  they did not justify comparisons to [[All About Eve]]   and were insufficiently different to deserve critical parallels with [[Rashomon]]   He also wrote that [[The Guardian]]  called the film a slow stuffy chamberpiece  and that [[The Evening Standard]]  stated the films best moments exhibit the bitchy tantrums seething beneath the threesomes composed veneers  [[MRQE]]  wrote This cinematic adaptation of a theatrical work is true to the original but does not stray far from a theatrical rendering of the story== 1997 won Best Catalan Film at [[Butaca Awards]]  for [[Ventura Pons]]   1997 won Best Catalan Film Actress at Butaca Awards shared by [[Núria Espert]]  [[Rosa Maria Sardà]]  [[Anna Lizaran]]  and [[Mercè Pons]]   1998 nominated for Best Screenplay at [[Goya Awards]]  shared by [[Josep Maria Benet i Jornet]]  and Ventura Pons  [[Wayback Machine|as archived February 17, 2009]]  Spanish
```


## 1. Generator.py 生成基础数据
- **项目路径(18服务器)**：`/home/xlore/xlink/DataPrepare/`
- **运行方式**：python3 Generator.py
- **输入**: 可在 `Generatory.py` 里进行配置
- **输出**: `output_dir` 可在 `Generatory.py` 里进行配置
	- output_dir/baidu/entity\_prior
	- output_dir/baidu/link\_prob
	- output_dir/baidu/m\_given\_e
	- (中间文件) output_dir/baidu/mention\_anchor
	- (中间文件) output_dir/baidu/train\_kg
	- (中间文件) output_dir/baidu/train\_text
	- (中间文件) output_dir/baidu/words

> 1. 上述是百度百科生成的数据文件，将路径中的 baidu 换为 wiki，即为维基百科的生成数据。
> 2. 2018.8 版本的 output_dir 是 data/production

## 2. 中间文件的处理
- 2.1 训练词向量与实体向量
- 2.2 构建 AC Trie Tree
- 2.3 构建 Xlore Url Map

### 2.1 训练词向量与实体向量

- **项目路径**(18服务器)：`/home/xlore/xlink/TrainJointModel`
- **输入**：第 1 步生成的 train\_kg 与 train\_text，具体路径可在 `./src/demo-align.sh` 中进行配置
- **输出**：生成 `vectors_word` 与 `vectors_entity`，具体路径可在 `./src/demo-align.sh` 中进行配置


### 2.2 构建 AC Trie Tree
- **项目路径**(18): `/home/xlore/xlink/BuildIndex`
- **输入**: 第 1 步生成的 `mention_anchor` 与 `words`，具体路径可在 `./src/main/BuildBaiudAll.java` 中进行配置
- **输出**: 生成 `baidu.trie` 与 `baidu_word.trie`，具体路径可在 `./src/main/BuildBaiudAll.java` 中进行配置
- **运行方法**：路径配置好之后，在项目路径下运行 `ant` 进行编译，随后运行 `ant BuildBaiduAll`

### 2.3 构建 Xlore Url Map


## 3. 配置系统数据文件

1. 第一步生成的数据
	- entity\_prior 移到 /home/zj/EntityLinkingWeb/data/baidu/prob/baidu\_entity\_prior.dat
	- m\_given\_e 移到 /home/zj/EntityLinkingWeb/data/baidu/prob/prob\_mention\_entity.dat
	- link\_prob 移到 /home/zj/EntityLinkingWeb/data/baidu/prob/link\_prob.dat
2. 第二步生成的数据移到
	- **词向量**
	- /home/zj/EntityLinkingWeb/data/baidu/vec\_model/vectors\_word
	- /home/zj/EntityLinkingWeb/data/baidu/vec\_model/vectors\_entity
	- /home/zj/EntityLinkingWeb/data/wiki/vec\_model/vectors\_word
	- /home/zj/EntityLinkingWeb/data/wiki/vec\_model/vectors\_entity
	- **AC Trie Tree**
	- /home/zj/EntityLinkingWeb/data/baidu/trie/baidu.trie
	- /home/zj/EntityLinkingWeb/data/wiki/trie/wiki.trie
	- /home/zj/EntityLinkingWeb/data/baidu/trie/baidu_word.trie
	- /home/zj/EntityLinkingWeb/data/wiki/trie/wiki_word.trie


