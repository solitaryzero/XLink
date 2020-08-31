set -ex
make
# min-count 如果词频小于它，过滤。
# cw 是否使用cbow
# sg 是否使用skip-gram
# size 向量维度
# negative 负采样个数
# sample 负采样的一个参数
# threads 线程
# binary 生成文件的格式
# iter 迭代次数
# window 上下文的词个数

#path="/home/zxr/dsel/preprocess/domain_extractor/data/domain/"
#domain="computing"
#path="/home/zxr/dsel/preprocess/domain_extractor/data/category/wiki_en/"
#domain="general"

#path="/mnt/sdd/zxr/domain/sports/"
#path="/mnt/sdd/zxr/jist/computing/"
#train_text=$path"train_text.txt"
#train_kg=$path"train_kg.txt"
#train_anchor=$path"train_text.txt"
#output_path=$path"result300/"

source="bd"
# path="/mnt/sdd/zxr/xlink/"$source"/emb/"
path="/mnt/sdd/zfw/xlink2020/"$source"/emb/"
train_text=$path"train_text"
train_kg=$path"train_kg"
train_anchor=$path"train_text"
# output_path="/mnt/sdd/zfw/xlink2020/bd/emb/result300/"
output_path=$path"result300/"

# time ./TrainJointModel/src/align -train_text $train_text -train_kg $train_kg -train_anchor $train_anchor -output_path $output_path -min-count 5 -cw 0 -sg 1 -size 300 -negative 5 -sample 1e-4 -threads 24 -binary 1 -iter 10 -window 8
time ./align -train_text $train_text -train_kg $train_kg -train_anchor $train_anchor -output_path $output_path -min-count 5 -cw 0 -sg 1 -size 300 -negative 5 -sample 1e-4 -threads 24 -binary 1 -iter 10 -window 10

# time ./align -train_text ../data/wiki/train_text -train_kg ../data/wiki/train_kg -train_anchor ../data/wiki/train_text -output_path ../data/wiki/result300/ -min-count 5 -cw 0 -sg 1 -size 300 -negative 5 -sample 1e-4 -threads 24 -binary 1 -iter 10 -window 10

# time ./align -train_text ../data/wiki/train_text -train_kg ../data/wiki/train_kg -train_anchor ../data/wiki/train_text -output_path ../data/wiki/result300/ -min-count 5 -cw 0 -sg 1 -size 300 -negative 5 -sample 1e-4 -threads 24 -binary 1 -iter 10 -window 10

