""" Format the possible mentions to file for manually annotating.

"""
from typing import List, Tuple

from evaluation.build_dataset import SampleBuilder
from models import Mention


class OutputFormatter:

    @classmethod
    def format(cls, mentions: List[SampleBuilder.Mention], document: str) -> str:
        output_str = ""
        plain_text_start = 0
        for mention in mentions:
            if mention.start > plain_text_start:
                output_str += document[plain_text_start: mention.start]
            plain_text_start = mention.end
            output_str += cls.get_mention_output(mention)
        if plain_text_start < len(document):
            output_str += document[plain_text_start:]
        return output_str

    @classmethod
    def format_for_json(cls, mentions: List[Mention])->List[str]:
        formatted_ann = []
        for mention in mentions:
            candidates = []
            for cand in mention.candidates:
                candidates.append("【{}|{}|{}|{}|{}】".format(
                    cand.entity_id,
                    cand.entity.get_full_title(),
                    "%.2f"%cand.believe_score,
                    "%.2f"%cand.context_words_sim,
                    "%.2f"%cand.context_entities_sim))
            formatted_ann.append("{}, {}, {}|{}, {}".format(mention.start, mention.end, mention.label, mention.believe_score or -1, "".join(candidates)))
        for m in mentions:
            if m.context_entities is not None:
                formatted_ann.append(",".join([entity.get_full_title() for entity in m.context_entities]))
                break
        return formatted_ann

    @classmethod
    def format_batch_for_json(cls, mention_list: List[List[Mention]]):
        result = []
        for mentions in mention_list:
            result.append(cls.format_for_json(mentions))
        return result

    @classmethod
    def format_for_dataset_annotations(cls, mentions: List[Mention]) -> List[Tuple]:
        mention_lists = []
        for mention in mentions:
            mention_lists.append((mention.start, mention.end, mention.label, mention.result_cand.entity_id))
        return mention_lists

    @classmethod
    def format_as_annotated_doc(cls, mentions: List[Mention], doc: str) -> str:
        formatted_doc = ""
        last_end = 0
        for mention in mentions:
            formatted_doc += doc[last_end: mention.start]
            candidate_str = ""
            if len(mention.candidates) > 0:
                candidate_str = mention.candidates[0].entity_id
            formatted_doc += "【{}|{}】".format(
                mention.label, candidate_str)
            last_end = mention.end
        formatted_doc += doc[last_end:]
        return formatted_doc

    @classmethod
    def format_as_annotated_doc_with_url(cls, mentions: List[Mention], doc: str) -> str:
        formatted_doc = ""
        last_end = 0
        for mention in mentions:
            formatted_doc += doc[last_end: mention.start]
            candidate_str = ""
            url = "https://xlore.org/instance.html?url=http://xlore.org/instance/"
            if len(mention.candidates) > 0:
                candidate_str = mention.result_cand.entity_id
            if len(candidate_str) > 0:
                url += candidate_str
            formatted_doc += "【{}|[{}]({})】".format(
                mention.label, candidate_str, url)
            last_end = mention.end
        formatted_doc += doc[last_end:]
        return formatted_doc

    @classmethod
    def get_mention_output(cls, mention: SampleBuilder.Mention):
        output_str = "\n<mention>\n"
        output_str += mention.label + "\n"

        candidates_str = ""
        for candidate in mention.candidates: # type: SampleBuilder.Candidate
            candidates_str += "\t{}\t{}\tP(C|e): {}\tP(N|e): {}\n".format(
                candidate.entity_id,
                candidate.entity.get_full_title(),
                candidate.context_words_sim,
                candidate.context_entities_sim)
        output_str += candidates_str + "</mention>\n"
        return output_str
