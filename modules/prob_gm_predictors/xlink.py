import copy
import imp
from typing import List

import numpy
from numpy import linalg as LA

from models import Candidate, Mention
from modules import EntityManager, MentionParser, ProbHolder, WordManager, WordParser
from modules import Predictor

imp.reload(ProbHolder)
imp.reload(MentionParser)

class XLinkPredictor(Predictor.Predictor):

    entity_manager = None   # type: EntityManager.EntityManager
    word_manager = None     # type: WordManager.WordManager
    word_parser = None      # type: WordParser.WordParser

    prob_mention_parser = None      # type: MentionParser.MentionParser
    no_prob_mention_parser = None   # type: MentionParser.MentionParser

    prob_holder = None      # type: ProbHolder.ProbHolder


    context_words_window = 50
    entity_popularity_power = 0.02
    link_prob_th = 0.008
    mention_believe_score_th = 0.2

    no_prob_context_words_window = 50
    no_prob_context_words_sim_th = 0.3
    no_prob_seed_candidates_sim_th = 0.45
    no_prob_believe_score_th = 0.5
    no_prob_words_sim_weight = 0.5

    def __new__(cls, source,
                entity_dict_path,
                entity_vec_path,
                word_vec_path,
                prob_mention_dict_txt_path,
                prob_mention_dict_trie_path,
                no_prob_mention_dict_txt_path,
                no_prob_mention_dict_trie_path,
                entity_prior_path,
                m_given_e_path,
                e_given_m_path,
                link_prob_path,
                force_reload=False):

        if not hasattr(XLinkPredictor, 'instance'):
            cls.instance = super(XLinkPredictor, cls).__new__(cls)
            cls.instance._init(source,
                entity_dict_path,
                entity_vec_path,
                word_vec_path,
                prob_mention_dict_txt_path,
                prob_mention_dict_trie_path,
                no_prob_mention_dict_txt_path,
                no_prob_mention_dict_trie_path,
                entity_prior_path,
                m_given_e_path,
                e_given_m_path,
                link_prob_path,
                force_reload)
        return cls.instance

    def _init(self, source,
                entity_dict_path,
                entity_vec_path,
                word_vec_path,
                prob_mention_dict_txt_path,
                prob_mention_dict_trie_path,
                no_prob_mention_dict_txt_path,
                no_prob_mention_dict_trie_path,
                entity_prior_path,
                m_given_e_path,
                e_given_m_path,
                link_prob_path,
                force_reload = False):

        EManager, PHolder, WManager, WParser, MParser = None, None, None, None, MentionParser.TrieTreeMentionParser

        if source == 'bd':
            EManager = EntityManager.BaiduEntityManager
            WManager = WordManager.BaiduWordManager
            PHolder  = ProbHolder.BaiduProbHolder
            WParser  = WordParser.JiebaWordParser
        elif source == 'wiki':
            EManager = EntityManager.WikiEntityManager
            WManager = WordManager.WikiWordManager
            PHolder  = ProbHolder.WikiProbHolder
            WParser  = WordParser.EnWordParser

        self.entity_manager = EManager(entity_dict_path, entity_vec_path, force_reload)
        self.word_manager   = WManager(word_vec_path, force_reload)
        self.word_parser    = WParser()

        ma_trie_config = MentionParser.TrieTreeConfig(prob_mention_dict_txt_path, prob_mention_dict_trie_path, "ma", 100)
        tt_trie_config = MentionParser.TrieTreeConfig(no_prob_mention_dict_txt_path, no_prob_mention_dict_trie_path, "tt", 0)
        self.prob_mention_parser = MParser(ma_trie_config)
        self.no_prob_mention_parser = MParser(tt_trie_config)

        self.prob_holder    = PHolder(entity_prior_path, m_given_e_path, e_given_m_path, link_prob_path)

    def predict(self, document) -> List[Mention]:
        prob_link_result = self.predict_has_prob(document)
        no_prob_link_result = self.predict_no_prob(document)
        return self.merge_two_result(prob_link_result, no_prob_link_result)

    def predict_has_prob(self, document) -> List[Mention]:
        prob_mentions = self.prob_mention_parser.parse_text(document)   # type: List[Mention]

        # 1. Find all unambiguous mentions
        unambiguous_mentions = []  # type: List[Mention]
        prob_link_result = []  # type: List[Mention]
        for mention in prob_mentions:

            prev_start = mention.start - self.context_words_window
            if prev_start < 0: prev_start = 0
            after_end = mention.end + self.context_words_window
            if after_end > len(document): after_end = len(document)
            prev_context_words = [word for word in self.word_parser.parse_text(document[prev_start: mention.start]) if
                                  word in self.word_manager.vec_model.vectors]
            after_context_words = [word for word in self.word_parser.parse_text(document[mention.end: after_end]) if
                                   word in self.word_manager.vec_model.vectors]

            mention.set_prev_context(prev_context_words)
            mention.set_after_context(after_context_words)

            if len(mention.candidates) == 1:
                entity_id = mention.candidates[0].entity_id
                candidate = mention.candidates[0]
                if self.entity_manager.is_entity_has_embed(entity_id):
                    candidate.set_entity(self.entity_manager.get_entity_dictionary().get_entity_from_id(entity_id))
                    mention.set_result_cand(candidate)
                    unambiguous_mentions.append(mention)

            else:
                for candidate in mention.candidates:
                    if self.entity_manager.is_entity_has_embed(candidate.entity_id):
                        candidate.set_entity(self.entity_manager.get_entity_dictionary().get_entity_from_id(candidate.entity_id))

            prob_link_result.append(mention)

        # 2. Calculate candidates' believe score.
        tmp_mentions_holder = []
        for mention in prob_link_result:
            context_words = copy.deepcopy(mention.prev_context)
            context_words.extend(mention.after_context)
            tmp_cands = []
            for candidate in mention.candidates:
                if self.entity_manager.is_entity_has_embed(candidate.entity_id):
                    candidate.set_context_words_sim(
                        self.cal_candidate_context_words_sim(candidate.entity_id, context_words))
                    candidate.set_context_entities_sim(self.cal_candidate_context_entities_sim(candidate.entity_id,
                                                                                           [mention.result_cand for
                                                                                            mention in
                                                                                            unambiguous_mentions]))
                    candidate.set_believe_score(self.cal_candidate_believe_score_v2(mention, candidate))
                    tmp_cands.append(candidate)
            mention.candidates = sorted(tmp_cands, key=lambda item: item.believe_score, reverse=True)
            mention.set_result_cand(mention.candidates[0])
            tmp_mentions_holder.append(mention)

        # 3. Refine mentions' believe score
        prob_link_result = []
        for mention in tmp_mentions_holder:
            if self.prob_holder.get_link_prob(mention.label) is not None and self.prob_holder.get_link_prob(
                    mention.label) > self.link_prob_th:
                mention.set_believe_score(
                    (mention.result_cand.believe_score + self.prob_holder.get_link_prob(mention.label)) / 2)
                if mention.believe_score > self.mention_believe_score_th:
                    prob_link_result.append(mention)
        return prob_link_result


    def predict_no_prob(self, document) -> List[Mention]:
        mention_list = self.no_prob_mention_parser.parse_text(document)

        mentions = []
        for mention in mention_list:

            prev_start = mention.start - self.no_prob_context_words_window
            if prev_start < 0: prev_start = 0
            after_end = mention.end + self.no_prob_context_words_window
            if after_end > len(document): after_end = len(document)
            prev_context_words = [word for word in self.word_parser.parse_text(document[prev_start: mention.start]) if
                                  word in self.word_manager.vec_model.vectors]
            after_context_words = [word for word in self.word_parser.parse_text(document[mention.end: after_end]) if
                                   word in self.word_manager.vec_model.vectors]
            context_words = prev_context_words
            context_words.extend(after_context_words)

            # 按照 context_words_sim 初步筛选出 valid candidate for mention
            valid_candidates = []  # type: List[Candidate]
            for candidate in mention.candidates:
                candidate_id = candidate.entity_id
                if self.entity_manager.is_entity_has_embed(candidate_id) and \
                        self.entity_manager.get_entity_dictionary().entity_dict.get(candidate_id) is not None:
                    candidate.set_entity(self.entity_manager.get_entity_dictionary().entity_dict.get(candidate_id))

                    candidate.set_context_words_sim(self.cal_candidate_context_words_sim(candidate_id, context_words))
                    if candidate.context_words_sim > self.no_prob_context_words_sim_th:
                        valid_candidates.append(candidate)

            if len(valid_candidates) > 0:
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
            if max_cand.context_words_sim > self.no_prob_seed_candidates_sim_th:
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

        # 设置 candidates 的 believe_score
        for i, mention in enumerate(mentions):
            for cand in mention.candidates:
                cand.set_believe_score(self.no_prob_words_sim_weight * cand.context_words_sim + (
                            1 - self.no_prob_words_sim_weight) * cand.context_entities_sim)
            mentions[i].candidates = sorted(mention.candidates, key=lambda item: item.believe_score, reverse=True)
            mentions[i].set_result_cand(mention.candidates[0])

        # 根据 believe_score 再次筛选 mentions
        refined_mentions = []   # type: List[Mention]
        for m in mentions:
            if m.result_cand.believe_score > self.no_prob_believe_score_th:
                refined_mentions.append(m)

        return refined_mentions

    @staticmethod
    def merge_two_result(has_prob_result, no_prob_result) -> List[Mention]:
        original_results = has_prob_result  # type: List[Mention]
        original_results.extend(no_prob_result) # type: List[Mention]

        if len(original_results) == 0: return []

        result = [] # type: List[Mention]

        def key_for_compare(i):
            return i.start

        original_results = sorted(original_results, key=key_for_compare)
        conflict_mentions = [original_results[0]]
        start, end = conflict_mentions[0].start, conflict_mentions[0].end

        for item in original_results[1:]:
            if item.start < end:
                conflict_mentions.append(item)
                end = max(item.end, end)
            else:
                # If there are prob_mentions in the conflict_mentions, then keep all prob_mentions, drop all no_prob_mentions.
                # If there are no prob_mentions in the conflict_mentions, the conflict_mentions definitely contains only one no_prob_mention, keep it.
                mentions_has_prob = []
                for conflict_mention in conflict_mentions:
                    if conflict_mention.believe_score is not None:
                        mentions_has_prob.append(conflict_mention)
                if len(mentions_has_prob) is not None:
                    result.extend(mentions_has_prob)
                else:
                    result.extend(conflict_mentions)
                conflict_mentions = [item]
                start, end = item.start, item.end

        mentions_has_prob = []
        for conflict_mention in conflict_mentions:
            if conflict_mention.believe_score is not None:
                mentions_has_prob.append(conflict_mention)
        if len(mentions_has_prob) is not None:
            result.extend(mentions_has_prob)
        else:
            result.extend(conflict_mentions)

        result = sorted(result, key=key_for_compare)
        return result

    def cal_candidate_context_words_sim(self, entity_id, context_words) -> float:
        if len(context_words) == 0: return 0
        context_embed = numpy.zeros(self.word_manager.vec_model.vec_size)
        for word in context_words:
            context_embed += numpy.array(self.word_manager.vec_model.vectors.get(word))
        context_embed /= len(context_words)

        entity_embed = self.entity_manager.get_vec_model().vectors.get(entity_id)
        return numpy.matmul(entity_embed, context_embed)/(LA.norm(entity_embed, 2) * LA.norm(context_embed, 2))

    def cal_candidate_context_entities_sim(self, entity_id, context_entities: List[Candidate]) -> float:
        if len(context_entities) == 0: return 1
        context_embed = numpy.zeros(self.entity_manager.get_vec_model().vec_size)
        for candidate in context_entities:
            context_embed += numpy.array(self.entity_manager.get_vec_model().vectors.get(candidate.entity_id))
        context_embed /= len(context_entities)

        entity_embed = self.entity_manager.get_vec_model().vectors.get(entity_id)
        return numpy.matmul(entity_embed, context_embed)/(LA.norm(entity_embed, 2) * LA.norm(context_embed, 2))

    def cal_candidate_believe_score_v1(self, candidate: Candidate) -> float:
        """ P(e)^a * P(C|e) * P(N|e)
        """
        if self.prob_holder.get_entity_prior(candidate.entity_id) is not None:
            return candidate.context_entities_sim * \
               candidate.context_words_sim * \
               numpy.power(self.prob_holder.get_entity_prior(candidate.entity_id), self.entity_popularity_power)
        return 0

    def cal_candidate_believe_score_v2(self, mention: Mention, candidate: Candidate) -> float:
        """ P(e|m) * P(C|e) * P(N|e)
        """
        if self.prob_holder.get_e_given_m(candidate.entity_id, mention.label) is not None:
            return candidate.context_entities_sim * \
               candidate.context_words_sim * \
               numpy.power(self.prob_holder.get_e_given_m(candidate.entity_id, mention.label), self.entity_popularity_power)
        return 0

    def set_hyper_params(self,
                         context_words_window=None,
                         entity_popularity_power=None,
                         link_prob_th=None,
                         mention_believe_score_th=None,
                         no_prob_context_words_window=None,
                         no_prob_context_words_sim_th = None,
                         no_prob_seed_candidates_sim_th = None,
                         no_prob_believe_score_th = None,
                         no_prob_words_sim_weight = None,
        ):
        if context_words_window is not None:
            self.context_words_window = context_words_window

        if entity_popularity_power is not None:
            self.entity_popularity_power = entity_popularity_power

        if link_prob_th is not None:
            self.link_prob_th = link_prob_th

        if mention_believe_score_th is not None:
            self.mention_believe_score_th = mention_believe_score_th

        if no_prob_context_words_window is not None:
            self.no_prob_context_words_window = no_prob_context_words_window

        if no_prob_context_words_sim_th is not None:
            self.no_prob_context_words_sim_th = no_prob_context_words_sim_th

        if no_prob_seed_candidates_sim_th is not None:
            self.no_prob_seed_candidates_sim_th = no_prob_seed_candidates_sim_th

        if no_prob_believe_score_th is not None:
            self.no_prob_believe_score_th = no_prob_believe_score_th

        if no_prob_words_sim_weight is not None:
            self.no_prob_words_sim_weight = no_prob_words_sim_weight


    def print_hyper_params(self):
        print("context_words_window: {}\n"
              "entity_popularity_power: {}\n"
              "link_prob_th: {}\n"
              "mention_believe_score_th: {}\n"
              "no_prob_context_words_window: {}\n"
              "no_prob_context_words_sim_th: {}\n"
              "no_prob_seed_candidates_sim_th: {}\n"
              "no_prob_believe_score_th: {}\n"
              "no_prob_words_sim_weight: {}\n".format(
            self.context_words_window,
            self.entity_popularity_power,
            self.link_prob_th,
            self.mention_believe_score_th,
            self.no_prob_context_words_window,
            self.no_prob_context_words_sim_th,
            self.no_prob_seed_candidates_sim_th,
            self.no_prob_believe_score_th,
            self.no_prob_words_sim_weight
        ))


class XLinkEntityDisambiguator(Predictor.Disambiguator):
    entity_manager = None   # type: EntityManager.EntityManager
    word_manager = None     # type: WordManager.WordManager
    word_parser = None      # type: WordParser.WordParser

    prob_holder = None      # type: ProbHolder.ProbHolder

    context_words_window = 50
    entity_popularity_power = 0.02
    link_prob_th = 0.008
    mention_believe_score_th = 0.2

    no_prob_context_words_window = 50
    no_prob_context_words_sim_th = 0.3
    no_prob_seed_candidates_sim_th = 0.45
    no_prob_believe_score_th = 0.5
    no_prob_words_sim_weight = 0.5

    def __new__(cls, source,
                entity_dict_path,
                entity_vec_path,
                word_vec_path,
                entity_prior_path,
                m_given_e_path,
                e_given_m_path,
                link_prob_path,
                force_reload):
        if not hasattr(XLinkEntityDisambiguator, 'instance'):
            cls.instance = super(XLinkEntityDisambiguator, cls).__new__(cls)
            cls.instance.init(
                source,
                entity_dict_path,
                entity_vec_path,
                word_vec_path,
                entity_prior_path,
                m_given_e_path,
                e_given_m_path,
                link_prob_path,
                force_reload
            )
        return cls.instance

    def init(self, source,
                entity_dict_path,
                entity_vec_path,
                word_vec_path,
                entity_prior_path,
                m_given_e_path,
                e_given_m_path,
                link_prob_path,
                force_reload):
        EManager, PHolder, WManager, WParser = None, None, None, None

        if source == 'bd':
            EManager = EntityManager.BaiduEntityManager
            WManager = WordManager.BaiduWordManager
            PHolder  = ProbHolder.BaiduProbHolder
            WParser  = WordParser.JiebaWordParser
        elif source == 'wiki':
            EManager = EntityManager.WikiEntityManager
            WManager = WordManager.WikiWordManager
            PHolder  = ProbHolder.WikiProbHolder
            WParser  = WordParser.EnWordParser

        self.entity_manager = EManager(entity_dict_path, entity_vec_path, force_reload)
        self.word_manager = WManager(word_vec_path, force_reload)
        self.word_parser = WParser()
        self.prob_holder = PHolder(entity_prior_path, m_given_e_path, e_given_m_path, link_prob_path)


    def predict(self, document, mentions_for_ed: List[Mention]):
        # 1. Find all unambiguous mentions
        unambiguous_mentions = []  # type: List[Mention]
        prob_link_result = []  # type: List[Mention]

        for mention in mentions_for_ed:
            prev_start = mention.start - self.context_words_window
            if prev_start < 0: prev_start = 0
            after_end = mention.end + self.context_words_window
            if after_end > len(document): after_end = len(document)
            prev_context_words = [word for word in self.word_parser.parse_text(document[prev_start: mention.start]) if
                                  word in self.word_manager.vec_model.vectors]
            after_context_words = [word for word in self.word_parser.parse_text(document[mention.end: after_end]) if
                                   word in self.word_manager.vec_model.vectors]

            mention.set_prev_context(prev_context_words)
            mention.set_after_context(after_context_words)

            if len(mention.candidates) == 1:
                entity_id = mention.candidates[0].entity_id
                candidate = mention.candidates[0]
                if self.entity_manager.is_entity_has_embed(entity_id):
                    candidate.set_entity(self.entity_manager.get_entity_dictionary().get_entity_from_id(entity_id))
                    mention.set_result_cand(candidate)
                    unambiguous_mentions.append(mention)

            else:
                for candidate in mention.candidates:
                    if self.entity_manager.is_entity_has_embed(candidate.entity_id):
                        candidate.set_entity(
                            self.entity_manager.get_entity_dictionary().get_entity_from_id(candidate.entity_id))
            prob_link_result.append(mention)

        # 2. Calculate candidates' believe score.
        result = []
        for i, mention in enumerate(prob_link_result):
            context_words = copy.deepcopy(mention.prev_context)
            context_words.extend(mention.after_context)
            mention.context_entities = [m.result_cand.entity for m in unambiguous_mentions]
            tmp_cands = []
            for candidate in mention.candidates:
                if self.entity_manager.is_entity_has_embed(candidate.entity_id):
                    candidate.set_context_words_sim(
                        self.cal_candidate_context_words_sim(candidate.entity_id, context_words))
                    candidate.set_context_entities_sim(self.cal_candidate_context_entities_sim(candidate.entity_id,
                                                                                               [mention.result_cand for
                                                                                                mention in
                                                                                                unambiguous_mentions]))
                    if mention.parse_from in ['ma']:
                        candidate.set_believe_score(self.cal_candidate_believe_score_v2(mention, candidate))    # P(e|m)^a * P(e|C) * P(e|N)
                        # candidate.set_believe_score(self.cal_candidate_believe_score_v1(candidate))           # P(e) * P(C|e) * P(N|e)
                    else:
                        candidate.set_believe_score(self.cal_candidate_believe_score_v3(candidate))             # w * P(C|e) + (1-w) * P(N|e)
                    tmp_cands.append(candidate)
            mention.candidates = sorted(tmp_cands, key=lambda item: item.believe_score, reverse=True)
            mention.set_result_cand(mention.candidates[0])
            result.append(mention)
        return result

    def cal_candidate_context_words_sim(self, entity_id, context_words) -> float:
        if len(context_words) == 0: return 0
        context_embed = numpy.zeros(self.word_manager.vec_model.vec_size)
        for word in context_words:
            context_embed += numpy.array(self.word_manager.vec_model.vectors.get(word))
        context_embed /= len(context_words)

        entity_embed = self.entity_manager.get_vec_model().vectors.get(entity_id)
        return numpy.matmul(entity_embed, context_embed)/(LA.norm(entity_embed, 2) * LA.norm(context_embed, 2))

    def cal_candidate_context_entities_sim(self, entity_id, context_entities: List[Candidate]) -> float:
        if len(context_entities) == 0: return 1
        context_embed = numpy.zeros(self.entity_manager.get_vec_model().vec_size)
        for candidate in context_entities:
            context_embed += numpy.array(self.entity_manager.get_vec_model().vectors.get(candidate.entity_id))
        context_embed /= len(context_entities)

        entity_embed = self.entity_manager.get_vec_model().vectors.get(entity_id)
        return numpy.matmul(entity_embed, context_embed)/(LA.norm(entity_embed, 2) * LA.norm(context_embed, 2))

    def cal_candidate_believe_score_v1(self, candidate: Candidate) -> float:
        """ P(e)^a * P(C|e) * P(N|e)
        """
        if self.prob_holder.get_entity_prior(candidate.entity_id) is not None:
            return candidate.context_entities_sim * \
               candidate.context_words_sim * \
               numpy.power(self.prob_holder.get_entity_prior(candidate.entity_id), self.entity_popularity_power)
        return 0

    def cal_candidate_believe_score_v3(self, candidate: Candidate):
        return (1-self.no_prob_words_sim_weight) * candidate.context_entities_sim + \
               self.no_prob_words_sim_weight * candidate.context_words_sim

    def cal_candidate_believe_score_v2(self, mention: Mention, candidate: Candidate) -> float:
        """ P(e|m, C, N) = P(e|m) * P(e|C) * P(e|N)
        """
        if self.prob_holder.get_e_given_m(candidate.entity_id, mention.label) is not None:
            return candidate.context_entities_sim * \
               candidate.context_words_sim * \
               numpy.power(self.prob_holder.get_e_given_m(candidate.entity_id, mention.label), self.entity_popularity_power)
        return 0

    def set_hyper_params(self,
                         context_words_window = None,
                         entity_popularity_power = None,
                         link_prob_th = None,
                         mention_believe_score_th = None,
                         no_prob_context_words_window = None,
                         no_prob_context_words_sim_th = None,
                         no_prob_seed_candidates_sim_th = None,
                         no_prob_believe_score_th = None,
                         no_prob_words_sim_weight = None
        ):

        if context_words_window is not None:
            self.context_words_window = context_words_window

        if entity_popularity_power is not None:
            self.entity_popularity_power = entity_popularity_power

        if link_prob_th is not None:
            self.link_prob_th = link_prob_th

        if mention_believe_score_th is not None:
            self.mention_believe_score_th = mention_believe_score_th

        if no_prob_context_words_window is not None:
            self.no_prob_context_words_window = no_prob_context_words_window

        if no_prob_context_words_sim_th is not None:
            self.no_prob_context_words_sim_th = no_prob_context_words_sim_th

        if no_prob_seed_candidates_sim_th is not None:
            self.no_prob_seed_candidates_sim_th = no_prob_seed_candidates_sim_th

        if no_prob_believe_score_th is not None:
            self.no_prob_believe_score_th = no_prob_believe_score_th

        if no_prob_words_sim_weight is not None:
            self.no_prob_words_sim_weight = no_prob_words_sim_weight

    def print_hyper_params(self):
        print("context_words_window: {}\n"
              "entity_popularity_power: {}\n"
              "link_prob_th: {}\n"
              "mention_believe_score_th: {}\n"
              "no_prob_context_words_window: {}\n"
              "no_prob_context_words_sim_th: {}\n"
              "no_prob_seed_candidates_sim_th: {}\n"
              "no_prob_believe_score_th: {}\n"
              "no_prob_words_sim_weight: {}\n".format(
            self.context_words_window,
            self.entity_popularity_power,
            self.link_prob_th,
            self.mention_believe_score_th,
            self.no_prob_context_words_window,
            self.no_prob_context_words_sim_th,
            self.no_prob_seed_candidates_sim_th,
            self.no_prob_believe_score_th,
            self.no_prob_words_sim_weight
        ))
