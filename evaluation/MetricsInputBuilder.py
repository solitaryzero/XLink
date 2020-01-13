from abc import ABCMeta, abstractmethod
from typing import List, Tuple

from models import Mention


class MetricsInputBuilder(metaclass=ABCMeta):
    @abstractmethod
    def build_input(self, predict_result: List[List[Mention]],
                    gold_annotation: List[List[Mention]]) -> Tuple:
        """
        :param predict_result: shape(#doc_size, #mention_size_respectively)
        :param gold_annotation: shape(#doc_size, #mention_size_respectively)
        :return: predict_vector, gold_vector  # shape of both is (#doc_size, #mention_size)
        """
        pass


class XLinkEDMetricsInputBuilder(MetricsInputBuilder):
    """ Build input vectors for XLink entity disambiguation only task.

    This class is for ED Model, therefore, the params of `build_input` has the same dimension, as the ED model only
    ranks the candidate entities for each given mention.
    """
    def build_input(self, predict_result: List[List[Mention]],
                    gold_annotation: List[List[Mention]]):
        predict_vector, gold_vector = [], []
        for i, doc_gold_mentions in enumerate(gold_annotation):
            doc_predict_mentions = predict_result[i]
            for mention_i, gold_mention in enumerate(doc_gold_mentions):
                predict_mention = doc_predict_mentions[mention_i]
                if predict_mention.result_cand is None or predict_mention.result_cand.entity_id != gold_mention.result_cand.entity_id:
                    predict_vector.append(0)
                else:
                    predict_vector.append(1)
                gold_vector.append(1)
        return predict_vector, gold_vector


class XLinkMPMetricsInputBuilder(MetricsInputBuilder):
    """ Build input vectors for XLink mention parsing process.

    This class is for Mention Parsing, therefore the parsed result(`predict_result`) may have different dimension
    compared to `gold_annotation`, for this situation, the rules for `build_input` contains two special case:
        1. A mention that contained in predict_result but gold_annotation:
            predict_vector.append(1)
            gold_vector.append(0)
        2. A mention that contained in gold_annotation but predict_result:
            predict_vector.append(0)
            gold_vector.append(1)
    """
    def build_input(self, predict_result: List[List[Mention]],
                    gold_annotation: List[List[Mention]]):
        predict_vector = []
        gold_vector = []
        for doc_idx, doc_gold_mentions in enumerate(gold_annotation):
            doc_predict_mentions = predict_result[doc_idx]
            predict_idx, gold_idx = 0, 0
            while predict_idx < len(doc_predict_mentions) and gold_idx < len(doc_gold_mentions):
                if doc_predict_mentions[predict_idx].start < doc_gold_mentions[gold_idx].start:
                    predict_vector.append(1)
                    gold_vector.append(0)
                    predict_idx += 1
                elif doc_predict_mentions[predict_idx].start == doc_gold_mentions[gold_idx].start:
                    if doc_predict_mentions[predict_idx].end == doc_gold_mentions[gold_idx].end:
                        predict_vector.append(1)
                        gold_vector.append(1)
                    else:
                        predict_vector.extend([1, 0])
                        gold_vector.extend([0, 1])
                    predict_idx += 1
                    gold_idx += 1
                else:
                    predict_vector.append(0)
                    gold_vector.append(1)
                    gold_idx += 1
        return predict_vector, gold_vector
