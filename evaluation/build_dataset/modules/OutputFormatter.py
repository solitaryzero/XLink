""" Format the possible mentions to file for manually annotating.

"""
from typing import List
from evaluation.build_dataset.modules import SampleBuilder

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
