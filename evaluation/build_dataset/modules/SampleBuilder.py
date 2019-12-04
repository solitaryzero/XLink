""" Build samples for manually annotating.

Prepare for Usage

    from evaluation.build_dataset.modules import MentionParser

    mention_parser = MentionParser.TrieTreeMentionParser(mention_txt_path, mention_dict_path)
    mention_list = mention_parser.parse_text(document)

Example Usage:

    builder = SamplerBuilder(source, entity_dict_path, entity_vec_path, word_vec_path, word_txt_path, word_trie_path)
    mentions = builder.build_sample(mention_list, document)
"""
from evaluation.build_dataset.modules import EntityManager
from evaluation.build_dataset.modules import WordManager
from evaluation.build_dataset.modules import WordParser
from typing import List, Any
from config import Config
import numpy


class Candidate:
    entity_id = None            # type: str
    entity    = None            # type: EntityManager.Entity
    context_words_sim = None    # type: float
    context_entities_sim = None # type: float

    def __init__(self, entity_id, entity_title=""):
        self.entity_id = entity_id
        self.entity_title = entity_title

    def set_context_words_sim(self, similarity):
        self.context_words_sim = similarity

    def set_context_entities_sim(self, similarity):
        self.context_entities_sim = similarity

    def set_entity(self, entity):
        self.entity = entity

class Mention:
    label = None        # type: str
    candidates = None   # type: List[Candidate]
    start = None        # type: int
    end   = None        # type: int

    prev_context = None         # type: List[str]
    after_context = None        # type: List[str]

    def __init__(self, start, end, mention_str, candidates=None):
        self.start = start
        self.end = end
        self.label = mention_str
        self.candidates = candidates
        pass

    def set_prev_context(self, context_words):
        self.prev_context = context_words

    def set_after_context(self, context_words):
        self.after_context = context_words


class SampleBuilder:
    entity_manager = None   # type: Any[EntityManager.BaiduEntityManager, EntityManager.EntityManager]
    word_manager = None     # type: WordManager.WordManager
    word_parser = None      # type: WordParser.WordParser

    def __new__(cls, source,
                entity_dict_path,
                entity_vec_path,
                word_vec_path,
                word_txt_path="",
                word_trie_path=""):
        if not hasattr(SampleBuilder, 'instance'):
            cls.instance = super(SampleBuilder, cls).__new__(cls)
            cls.instance.init(source, entity_dict_path, entity_vec_path, word_vec_path, word_txt_path, word_trie_path)
        return cls.instance

    def init(self, source,
                entity_dict_path,
                entity_vec_path,
                word_vec_path,
                word_txt_path="",
                word_trie_path=""):
        if not Config.is_source_valid(source):
            raise ValueError("Currently, `source` should be in [{}]".format(",".join(Config.get_sources())))

        EManager, WManager, WParser = None, None, WordParser.JiebaWordParser

        if source == 'bd':
            EManager = EntityManager.BaiduEntityManager
            WManager = WordManager.BaiduWordManager
        elif source == 'wiki':
            EManager = EntityManager.WikiEntityManager
            WManager = WordManager.WikiWordManager

        self.entity_manager = EManager(entity_dict_path, entity_vec_path)
        self.word_manager = WManager(word_vec_path)
        self.word_parser = WParser()
        # This is for WordParser.TrieTreeWordParser
        # self.word_parser = WParser(word_txt_path, word_trie_path)

    def build_sample(self, mention_list: List, document: str, context_window=50):
        """
            1. 由 mention list 和 document 构造 List[Mention] (主要是 prev_context, after_context 和 context_words_sim)
            2. 由 List[Mention] 计算 context_entities_sim.

        Args:
            mention_list: [(start, end, mention, candidates)], the result should come from MentionParser.parse_text(document)
            document: the input document.
            context_window: the window size is the character number, not word number.

        Return: List[Mention]
        """
        mentions = []
        for start, end, mention_str, candidates in mention_list:
            valid_candidates = []   # type: List[Candidate]
            for candidate_id in candidates:
                if self.entity_manager.is_entity_has_embed(candidate_id) and \
                    self.entity_manager.entity_dictionary.entity_dict.get(candidate_id) is not None:
                    candidate = Candidate(candidate_id)
                    candidate.set_entity(self.entity_manager.entity_dictionary.entity_dict.get(candidate_id))
                    valid_candidates.append(candidate)

            if len(valid_candidates) > 0:
                mention = Mention(start, end, mention_str, valid_candidates)

                prev_start = start - context_window
                if prev_start < 0: prev_start = 0
                after_end = end + context_window
                if after_end > len(document): after_end = len(document)
                prev_context_words = [word for word in self.word_parser.parse_text(document[prev_start: start]) if word in self.word_manager.vec_model.vectors]
                after_context_words = [word for word in self.word_parser.parse_text(document[end: after_end]) if word in self.word_manager.vec_model.vectors]

                mention.set_prev_context(prev_context_words)
                mention.set_after_context(after_context_words)

                context_words = prev_context_words
                context_words.extend(after_context_words)
                for i in range(len(mention.candidates)):
                    mention.candidates[i].set_context_words_sim(
                        self.cal_candidate_context_words_sim(mention.candidates[i].entity_id, context_words))

                mention.candidates = sorted(mention.candidates, key=lambda item: item.context_words_sim, reverse=True)
                mentions.append(mention)

        # 开始计算 context_entities_similarity
        seed_candidates = []
        # TODO: build seed candidates here
        for i, mention in enumerate(mentions):
            for j, candidate in enumerate(mentions[i].candidates):
                mentions[i].candidates[j].set_context_entities_sim(
                    self.cal_candidate_context_entities_sim(candidate.entity_id, seed_candidates))
        # TODO: expand seed candidates here
        for i, mention in enumerate(mentions):
            for j, candidate in enumerate(mentions[i].candidates):
                mentions[i].candidates[j].set_context_entities_sim(
                    self.cal_candidate_context_entities_sim(candidate.entity_id, seed_candidates))

        return mentions

    def cal_candidate_context_words_sim(self, entity_id, context_words) -> float:
        if len(context_words) == 0: return 0
        context_embed = numpy.zeros(self.word_manager.vec_model.vec_size)
        for word in context_words:
            context_embed += numpy.array(self.word_manager.vec_model.vectors.get(word))
        context_embed /= len(context_words)

        entity_embed = self.entity_manager.vec_model.vectors.get(entity_id)
        return numpy.matmul(entity_embed, context_embed)

    def cal_candidate_context_entities_sim(self, entity_id, context_entities) -> float:
        if len(context_entities) == 0: return 0
        context_embed = numpy.zeros(self.entity_manager.vec_model.vec_size)
        for eid in context_entities:
            context_embed += numpy.array(self.entity_manager.vec_model.vectors.get(eid))
        context_embed /= len(context_entities)

        entity_embed = self.entity_manager.vec_model.vectors.get(entity_id)
        return numpy.matmul(entity_embed, context_embed)
