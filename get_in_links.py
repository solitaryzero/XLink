import argparse
import json
import subprocess

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', type=str, required=True)
    args = parser.parse_args()

    js = json.load(open('/data/zfw/xlink/bd/out_links.json', 'r', encoding='utf-8'))
    res = []
    for x in js:
        if (args.id in js[x]):
            res.append(x)

    with open('/data/zfw/xlink/bd/bd_instance_ID.txt', 'r', encoding='utf-8') as fin:
        for line in fin:
            if (line.strip().split('\t\t')[3] in res):
                print(line)