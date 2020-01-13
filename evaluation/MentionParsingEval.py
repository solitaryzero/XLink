from typing import List

from models import Mention


class ValidMentionGenerator:
    """ Find all valid mentions in our parsed result.

    Valid mentions are the mentions that appear in gold standard annotations.
    """
    @classmethod
    def get_doc_valid_result(cls, parsed_mentions: List[Mention], gold_mentions: List[Mention]):
        """
        :param parsed_mentions:
        :param gold_mentions:
        :return:
        """
        parsed_idx, gold_idx = 0, 0
        valid_mentions = [] # type: List[Mention]
        valid_candidate_mentions = [] # type: List[Mention]

        while parsed_idx < len(parsed_mentions) and gold_idx < len(gold_mentions):
            parsed_mention = parsed_mentions[parsed_idx]
            gold_mention   = gold_mentions[gold_idx]
            if gold_mention.start < parsed_mention.start:
                gold_idx += 1
            elif gold_mention.start == parsed_mention.start:
                if gold_mention.end == parsed_mention.end:
                    valid_mentions.append(parsed_mention)
                    for cand in parsed_mention.candidates:
                        if gold_mention.result_cand is not None and cand.entity_id == gold_mention.result_cand.entity_id:
                            parsed_mention.set_result_cand(gold_mention.result_cand)
                            # print(parsed_mention.result_cand.entity_id, gold_mention.result_cand.entity_id)
                            valid_candidate_mentions.append(parsed_mention)
                            break
                gold_idx += 1
                parsed_idx += 1
            else:
                parsed_idx += 1

        return valid_mentions, valid_candidate_mentions

    @classmethod
    def get_batch_valid_result(cls, parsed_mentions: List[List[Mention]], gold_mentions: List[List[Mention]]):
        if len(parsed_mentions) != len(gold_mentions): return 0, 0

        valid_mentions = []  # type: List[List[Mention]]
        valid_candidate_mentions = []  # type: List[List[Mention]]

        for i, parsed_doc_mentions in enumerate(parsed_mentions):
            gold_doc_mentions = gold_mentions[i]
            doc_mention_result = cls.get_doc_valid_result(parsed_doc_mentions, gold_doc_mentions)
            valid_mentions.append(doc_mention_result[0])
            valid_candidate_mentions.append(doc_mention_result[1])

        total_gold_mentions = len([item for doc_mention in gold_mentions for item in doc_mention])
        total_parsed_mentions = len([item for doc_mention in parsed_mentions for item in doc_mention])
        total_valid_mentions = len([item for doc_mention in valid_mentions for item in doc_mention])
        total_valid_candidate_mentions = len([item for doc_mention in valid_candidate_mentions for item in doc_mention])

        print("Total Gold Mentions: {}\n"
              "Total Parsed Mentions: {}\n"
              "Parsed Valid Mention: {}\n" # 有 Mention 有 Candidate
              "Parsed Valid Candidate Mention: {}\n".format(
            total_gold_mentions, total_parsed_mentions,
            "{}({}%)".format(total_valid_mentions, "%.2f"%(total_valid_mentions/total_gold_mentions * 100)),
            "{}({}%)".format(total_valid_candidate_mentions, "%.2f"%(total_valid_candidate_mentions/total_gold_mentions * 100))
        ))
        return valid_mentions, valid_candidate_mentions

