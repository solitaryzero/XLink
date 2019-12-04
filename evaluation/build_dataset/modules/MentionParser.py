"""
MentionParser extracts possible mentions from plain text.

Input: a span of plain text
Output: a list of mentions with their positions in the text.
"""
from abc import ABCMeta, abstractmethod
from jpype import *
from config import Config


class MentionParser(metaclass=ABCMeta):

    @abstractmethod
    def parse_text(self, text: str):
        pass


class TrieTreeMentionParser(MentionParser):

    def __new__(cls, dict_path, trie_path, jar_path=Config.project_root + "data/jar/BuildIndex.jar"):
        if not hasattr(TrieTreeMentionParser, 'instance'):
            cls.instance = super(TrieTreeMentionParser, cls).__new__(cls)
            cls.instance.init(dict_path, trie_path, jar_path)
        return cls.instance

    def init(self, dict_path, trie_path, jar_path):
        if not isJVMStarted():
            startJVM(getDefaultJVMPath(), "-Djava.class.path=%s" % jar_path)

        if not isThreadAttachedToJVM():
            attachThreadToJVM()

        JDClass = JClass("edu.TextParser")
        self.parser = JDClass(dict_path, trie_path)

    def parse_text(self, text: str):
        if not isThreadAttachedToJVM():
            attachThreadToJVM()
        return self.solve_conflict(self.format_output(self.parser.parseText(text), text))

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

    def solve_conflict(self, formatted_result):
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

class MultiTrieTreeParser(MentionParser):
    def parse_text(self, text: str):
        pass
