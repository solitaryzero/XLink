"""
MentionParser extracts possible mentions from plain text.

Input: a span of plain text
Output: a list of mentions with their positions in the text.
"""
import datetime
import heapq
import time
from abc import ABCMeta, abstractmethod
from typing import Dict, List

from jpype import *

from config import Config
from models import Candidate, Mention


class MentionParser(metaclass=ABCMeta):

    @abstractmethod
    def parse_text(self, text: str):
        pass


class TrieTreeConfig:
    dict_path = ""
    trie_path = ""
    name      = ""
    weight    = 0  # If two parsing results from different trie trees conflict, keep the higher one.

    def __init__(self, dict_path, trie_path, name, weight=0):
        self.dict_path = dict_path
        self.trie_path = trie_path
        self.name      = name
        self.weight    = weight


class TrieTreeMentionParser(MentionParser):
    param_config = None # type: TrieTreeConfig

    def __init__(self, trie_tree_config: TrieTreeConfig, jar_path=Config.project_root + "data/jar/BuildIndex.jar"):
        if not isJVMStarted():
            startJVM(getDefaultJVMPath(), "-Djava.class.path=%s" % jar_path)

        if not isThreadAttachedToJVM():
            attachThreadToJVM()

        JDClass = JClass("edu.TextParser")
        self.parser = JDClass(trie_tree_config.dict_path, trie_tree_config.trie_path)
        self.param_config = trie_tree_config

    def parse_text(self, text: str) -> List[Mention]:
        if not isThreadAttachedToJVM():
            attachThreadToJVM()

        parsed_result = self.solve_conflict(self.format_output(self.parser.parseText(text), text))

        mention_list = []  # type: List[Mention]
        for item in parsed_result:
            mention = Mention(int(item[0]), int(item[1]), item[2])
            mention.candidates = []
            for cand_id in item[3]:
                candidate = Candidate(cand_id)
                mention.add_candidate(candidate)
                mention.parse_from = self.param_config.name
            mention_list.append(mention)
        return mention_list

    @staticmethod
    def solve_conflict(formatted_result):
        if len(formatted_result) == 0: return []
        mention_list = []

        formatted_result = sorted(formatted_result, key=lambda item: item[0])
        conflict_items = [formatted_result[0]]
        start, end = formatted_result[0][:2]

        for item in formatted_result[1:]:
            if item[0] < end:
                conflict_items.append(item)
                end = max(item[1], end)
            else:
                max_mention_length, max_item = -1, None
                for conflict_item in conflict_items:
                    if len(conflict_item[2]) > max_mention_length:
                        max_mention_length = len(conflict_item[2])
                        max_item = conflict_item
                mention_list.append(max_item)
                conflict_items = [item]
                start, end = item[:2]

        max_mention_length, max_item = -1, None
        for conflict_item in conflict_items:
            if len(conflict_item[2]) > max_mention_length:
                max_mention_length = len(conflict_item[2])
                max_item = conflict_item
        mention_list.append(max_item)

        return mention_list

    @staticmethod
    def format_output(parsed_result, doc):
        parsed_result = parsed_result[1:-1]
        result = []
        if parsed_result != "":
            items = parsed_result.split(",")
            for item in items:
                item = item.strip()
                mention_indices, candidates = item.split("=", 1)
                start, end = mention_indices[1:-1].split(":")
                start = int(start)
                end = int(end)
                result.append((start, end, doc[start: end], candidates.split("::=")))
        return result


class TrieTreeMultiDictParser(MentionParser):
    """ Parses mentions by multiple trie trees.
    """
    _parsers = None    # type: Dict[str, TrieTreeMentionParser]

    def __new__(cls, trie_tree_configs: List[TrieTreeConfig],
                jar_path=Config.project_root + "data/jar/BuildIndex.jar"):
        """ Singleton Mode.
        """
        if not hasattr(TrieTreeMultiDictParser, 'instance'):
            cls.instance = super(TrieTreeMultiDictParser, cls).__new__(cls)
            cls.instance.init(trie_tree_configs, jar_path)
        return cls.instance

    def init(self, trie_tree_configs: List[TrieTreeConfig], jar_path: str):
        start_at = int(time.time())

        self._parsers = dict()
        for trie_tree_config in trie_tree_configs:
            self._parsers[trie_tree_config.name] = TrieTreeMentionParser(trie_tree_config, jar_path)

        print("{} trie tree(s) loaded, time: {}".format(len(trie_tree_configs), str(datetime.timedelta(seconds=int(time.time())-start_at))))

    def parse_text(self, document):
        parse_result = dict()
        for name in self._parsers:
            parse_result[name] = self.parse_text_by_trie(name, document)

        valid_result = []   # type: List[Mention]

        # 合并 k 个有序数组
        head_items = []
        for name in parse_result:
            if len(parse_result[name]) == 0: continue
            mention = parse_result[name][0]
            heapq.heappush(head_items, (
                mention.start,
                mention.end,
                name,
                self._parsers[name].param_config.weight,
                0,
                mention)) # (start, name, weight, index, mention)

        while len(head_items) > 0:
            # 假设这里第一个是最小值
            conflict_items = []
            smallest_item = head_items[0]
            for item in head_items:
                if item[0] < smallest_item[1]:
                    conflict_items.append(item)
            if len(conflict_items) == 1:
                valid_result.append(smallest_item[5])
                heapq.heappop(head_items)
                start, end, trie_name, trie_weight, trie_idx, mention = smallest_item
                if trie_idx+1 < len(parse_result[trie_name]):
                    trie_idx += 1
                    mention = parse_result[trie_name][trie_idx]
                    heapq.heappush(head_items, (
                        mention.start,
                        mention.end,
                        trie_name,
                        self._parsers[trie_name].param_config.weight,
                        trie_idx,
                        mention
                    ))
            else:
                highest_weight = conflict_items[0][3]
                highest_idx = 0
                for idx in range(1, len(conflict_items)):
                    if conflict_items[idx][3] > highest_weight:
                        highest_weight = conflict_items[idx][3]
                        highest_idx = idx
                for idx, item in enumerate(conflict_items):
                    if idx != highest_idx:
                        for head_idx, head_item in enumerate(head_items):
                            if head_item[0] == item[0] and head_item[1] == item[1] and head_item[2] == head_item[2]:
                                del head_items[head_idx]
                                break
                        start, end, trie_name, trie_weight, trie_idx, mention = item
                        if trie_idx + 1 < len(parse_result[trie_name]):
                            trie_idx += 1
                            mention = parse_result[trie_name][trie_idx]
                            head_items.append((
                                mention.start,
                                mention.end,
                                trie_name,
                                self._parsers[trie_name].param_config.weight,
                                trie_idx,
                                mention
                            ))
                heapq.heapify(head_items)

        return valid_result


    def parse_text_by_trie(self, trie_name: str, document: str) -> List[Mention]:
        parser = self._parsers.get(trie_name)   # type: TrieTreeMentionParser
        if parser is not None:
            return parser.parse_text(document)
        else: return []
