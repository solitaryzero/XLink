""" WordParser splits the text into a word sequence.

TrieTreeWordParser is for using a pre-built trie tree to obtain a word sequence.
JiebaWordParser splits the text into a word sequence by word segmentation algorithms.

Example Usage:

    parser = TrieTreeWordParser(dict_path, trie_path)
    result = parser.parse_text(text) # [word1, word2, word3, ...]
"""

from abc import ABCMeta, abstractmethod
from config import Config
from jpype import *
from typing import List
import jieba


class WordParser(metaclass=ABCMeta):
    @abstractmethod
    def parse_text(self, text: str) -> List[str]:
        """ parse the text into a word sequence.

        Args:
            text: the text for parsing.

        Return:
            List[str], word sequence.
        """
        pass


class TrieTreeWordParser(WordParser):
    def __new__(cls, dict_path, trie_path, jar_path=Config.project_root + "data/jar/BuildIndex.jar"):
        if not hasattr(TrieTreeWordParser, 'instance'):
            cls.instance = super(TrieTreeWordParser, cls).__new__(cls)
            cls.instance.init(dict_path, trie_path, jar_path)
        return cls.instance

    def init(self, dict_path, trie_path, jar_path):
        if not isJVMStarted():
            startJVM(getDefaultJVMPath(), "-Djava.class.path=%s" % jar_path)

        if not isThreadAttachedToJVM():
            attachThreadToJVM()

        JDClass = JClass("edu.TextParser")
        self.parser = JDClass(dict_path, trie_path)

    def parse_text(self, text):
        parsed_result = self.parser.parseText(text)
        formatted_result = self.format_output(parsed_result, text)
        return self.solve_conflict(formatted_result, text)

    def solve_conflict(self, formatted_result, doc) -> List[str]:
        pass

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
                result.append([start, end, doc[start: end], candidates.split("::=")])
        return result


class JiebaWordParser(WordParser):
    def parse_text(self, text):
        words = [item for item in jieba.cut(text)]
        return words