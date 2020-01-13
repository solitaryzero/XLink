from abc import ABCMeta, abstractmethod
from typing import Any, List

import numpy
from numpy import linalg as LA

from config import Config
from models import Candidate, Mention
from modules import EntityManager, MentionParser, WordManager, WordParser


class Predictor(metaclass=ABCMeta):
    @abstractmethod
    def predict(self, document) -> List[Mention]:
        pass

class Disambiguator(metaclass=ABCMeta):
    @abstractmethod
    def predict(self, document, mentions_for_ed: List[Mention]):
        pass


"""
import os
from config import Config
source = "bd"
data_path = os.path.join(Config.data_root, source)
entity_dict_path = os.path.join(data_path, "entity_id.txt")
entity_vec_path = os.path.join(data_path, "emb/result300/vectors_entity")
word_vec_path = os.path.join(data_path, "emb/result300/vectors_word")
mention_txt_path = os.path.join(data_path, "mention_anchors.txt")
mention_trie_path = os.path.join(data_path, "mention_anchors.trie")
"""
class GenerativeModelPredictor(Predictor):
    entity_manager = None   # type: Any[EntityManager.BaiduEntityManager,  EntityManager]
    word_manager = None     # type: WordManager.WordManager
    word_parser = None      # type: WordParser.WordParser
    mention_parser = None   # type: MentionParser.MentionParser

    context_words_window = 50
    context_words_sim_th = 0.3
    seed_candidates_sim_th = 0.45
    believe_score_th = 0.5
    words_sim_weight = 0.5

    def __new__(cls, source,
                entity_dict_path,
                entity_vec_path,
                word_vec_path,
                mention_dict_txt_path,
                mention_dict_trie_path):
        if not hasattr(GenerativeModelPredictor, 'instance'):
            cls.instance = super(GenerativeModelPredictor, cls).__new__(cls)
            cls.instance.init(source, entity_dict_path, entity_vec_path, word_vec_path, mention_dict_txt_path, mention_dict_trie_path)
        return cls.instance

    def init(self, source,
             entity_dict_path,
             entity_vec_path,
             word_vec_path,
             mention_dict_txt_path,
             mention_dict_trie_path):
        if not Config.is_source_valid(source):
            raise ValueError("Currently, `source` should be in [{}]".format(",".join(Config.get_sources())))

        EManager, WManager, WParser, MParser = None, None, WordParser.JiebaWordParser, MentionParser.TrieTreeMentionParser

        if source == 'bd':
            EManager = EntityManager.BaiduEntityManager
            WManager = WordManager.BaiduWordManager
        elif source == 'wiki':
            EManager = EntityManager.WikiEntityManager
            WManager = WordManager.WikiWordManager

        self.entity_manager = EManager(entity_dict_path, entity_vec_path)
        self.word_manager = WManager(word_vec_path)
        self.word_parser = WParser()
        self.mention_parser = MParser(mention_dict_txt_path, mention_dict_trie_path)

    def set_hyper_params(self, context_words_window=50,
                         context_words_sim_th=0.3,
                         seed_candidates_sim_th=0.45,
                         believe_score_th=0.5,
                         words_sim_weight=0.5):
        """
        :param context_words_window:
        :param context_words_sim_th:
        :param seed_candidates_sim_th:
        :param believe_score_th:
        :param words_sim_weight: believe_score = words_sim_weight * context_words_sim + (1-words_sim_weight) * context_entities_sim
        :return:
        """
        self.context_words_window = context_words_window
        self.context_words_sim_th = context_words_sim_th
        self.seed_candidates_sim_th = seed_candidates_sim_th
        self.believe_score_th = believe_score_th
        self.words_sim_weight = words_sim_weight

    def predict(self, document) -> List[Mention]:
        mention_list = self.mention_parser.parse_text(document)

        mentions = []
        for start, end, mention_str, candidates in mention_list:

            prev_start = start - self.context_words_window
            if prev_start < 0: prev_start = 0
            after_end = end + self.context_words_window
            if after_end > len(document): after_end = len(document)
            prev_context_words = [word for word in self.word_parser.parse_text(document[prev_start: start]) if
                                  word in self.word_manager.vec_model.vectors]
            after_context_words = [word for word in self.word_parser.parse_text(document[end: after_end]) if
                                   word in self.word_manager.vec_model.vectors]
            context_words = prev_context_words
            context_words.extend(after_context_words)

            # 按照 context_words_sim 初步筛选出 valid candidate for mention
            valid_candidates = []  # type: List[Candidate]
            for candidate_id in candidates:
                if self.entity_manager.is_entity_has_embed(candidate_id) and \
                        self.entity_manager.entity_dictionary.entity_dict.get(candidate_id) is not None:
                    candidate = Candidate(candidate_id)
                    candidate.set_entity(self.entity_manager.entity_dictionary.entity_dict.get(candidate_id))

                    candidate.set_context_words_sim(self.cal_candidate_context_words_sim(candidate_id, context_words))
                    if candidate.context_words_sim > self.context_words_sim_th:
                        valid_candidates.append(candidate)

            if len(valid_candidates) > 0:
                mention = Mention(start, end, mention_str, valid_candidates)
                mention.set_prev_context(prev_context_words)
                mention.set_after_context(after_context_words)
                mentions.append(mention)

        # 开始计算 context_entities_similarity
        seed_candidates = []  # type: List[Candidate]

        # 根据 context_words_sim_th_for_seed_candidates 筛选出 seed_candidates
        for i, mention in enumerate(mentions):
            max_sim = -1
            max_cand = None
            for candidate in mention.candidates:
                if candidate.context_words_sim > max_sim:
                    max_cand = candidate
            if max_cand.context_words_sim > self.seed_candidates_sim_th:
                seed_candidates.append(max_cand)
                mention.set_result_cand(max_cand)

        # 为未消歧的 mention 构建 context_entities
        context_entities = []
        for cand in seed_candidates:
            context_entities.append(cand.entity)

        # 为所有的 mention 的 candidate 计算 context_entities_sim
        for i, mention in enumerate(mentions):
            if mention.result_cand is None:
                # 如果是未消歧的 mention，直接计算与 seed_candidates 的相似度
                for j, candidate in enumerate(mentions[i].candidates):
                    mentions[i].set_context_entities(context_entities)
                    mentions[i].candidates[j].set_context_entities_sim(
                        self.cal_candidate_context_entities_sim(candidate.entity_id, seed_candidates))
            else:
                # 如果是已消歧的 mention，则去掉该 mention 的 candidates 得到 seed_candidates_for_mention，计算相似度
                seed_entities_for_mention = []  # type: List[Candidate]
                for seed_cand in seed_candidates:
                    belong_to_mention = False
                    for cand in mention.candidates:
                        if cand.entity_id == seed_cand.entity_id:
                            belong_to_mention = True
                    if not belong_to_mention:
                        seed_entities_for_mention.append(seed_cand)

                for j, candidate in enumerate(mentions[i].candidates):
                    mentions[i].set_context_entities(context_entities)
                    mentions[i].candidates[j].set_context_entities_sim(
                        self.cal_candidate_context_entities_sim(candidate.entity_id, seed_entities_for_mention))

        # 设置 mention 的 believe_score
        for i, mention in enumerate(mentions):
            for cand in mention.candidates:
                cand.set_believe_score(self.words_sim_weight * cand.context_words_sim + (1-self.words_sim_weight) * cand.context_entities_sim)
            mentions[i].candidates = sorted(mention.candidates, key=lambda item: item.believe_score, reverse=True)
            mentions[i].set_result_cand(mention.candidates[0])

        # 根据 believe_score 再次筛选 mentions
        refined_mentions = []
        for m in mentions:
            if m.result_cand.believe_score > self.believe_score_th:
                refined_mentions.append(m)

        # TODO: expand seed candidates here
        # for i, mention in enumerate(mentions):
        #     for j, candidate in enumerate(mentions[i].candidates):
        #         mentions[i].candidates[j].set_context_entities_sim(
        #             self.cal_candidate_context_entities_sim(candidate.entity_id, seed_candidates))

        return refined_mentions


    def cal_candidate_context_words_sim(self, entity_id, context_words) -> float:
        if len(context_words) == 0: return 0
        context_embed = numpy.zeros(self.word_manager.vec_model.vec_size)
        for word in context_words:
            context_embed += numpy.array(self.word_manager.vec_model.vectors.get(word))
        context_embed /= len(context_words)

        entity_embed = self.entity_manager.vec_model.vectors.get(entity_id)
        return numpy.matmul(entity_embed, context_embed)/(LA.norm(entity_embed, 2) * LA.norm(context_embed, 2))

    def cal_candidate_context_entities_sim(self, entity_id, context_entities) -> float:
        if len(context_entities) == 0: return 0
        context_embed = numpy.zeros(self.entity_manager.vec_model.vec_size)
        for candidate in context_entities:
            context_embed += numpy.array(self.entity_manager.vec_model.vectors.get(candidate.entity_id))
        context_embed /= len(context_entities)

        entity_embed = self.entity_manager.vec_model.vectors.get(entity_id)
        return numpy.matmul(entity_embed, context_embed)/(LA.norm(entity_embed, 2) * LA.norm(context_embed, 2))


class ProbGenerativeModelPredictor(Predictor):
    entity_manager = None   # type: Any[EntityManager.BaiduEntityManager,  EntityManager]
    word_manager = None     # type: WordManager.WordManager
    word_parser = None      # type: WordParser.WordParser

    prob_mention_parser = None      # type: MentionParser.MentionParser
    no_prob_mention_parser = None   # type: MentionParser.MentionParser

    def __new__(cls, source,
                entity_dict_path,
                entity_vec_path,
                word_vec_path,
                prob_mention_txt_path,
                prob_mention_trie_path,
                no_prob_mention_txt_path,
                no_prob_mention_trie_path):
        if not hasattr(ProbGenerativeModelPredictor, 'instance'):
            cls.instance = super(ProbGenerativeModelPredictor, cls).__new__(cls)
            cls.instance.init(source,
                entity_dict_path,
                entity_vec_path,
                word_vec_path,
                prob_mention_txt_path,
                prob_mention_trie_path,
                no_prob_mention_txt_path,
                no_prob_mention_trie_path)
        return cls.instance

    def init(self, source,
                entity_dict_path,
                entity_vec_path,
                word_vec_path,
                prob_mention_txt_path,
                prob_mention_trie_path,
                no_prob_mention_txt_path,
                no_prob_mention_trie_path):
        if not Config.is_source_valid(source):

            raise ValueError("Currently, `source` should be in [{}]".format(",".join(Config.get_sources())))

        EManager, WManager, WParser, MParser = None, None, WordParser.JiebaWordParser, MentionParser.TrieTreeMentionParser

        if source == 'bd':
            EManager = EntityManager.BaiduEntityManager
            WManager = WordManager.BaiduWordManager
        elif source == 'wiki':
            EManager = EntityManager.WikiEntityManager
            WManager = WordManager.WikiWordManager

        self.entity_manager = EManager(entity_dict_path, entity_vec_path)
        self.word_manager = WManager(word_vec_path)
        self.word_parser = WParser()
        self.prob_mention_parser = MParser(prob_mention_txt_path, prob_mention_trie_path)
        self.no_prob_mention_parser = MParser(no_prob_mention_txt_path, no_prob_mention_trie_path)


    def predict(self, document):

        pass
