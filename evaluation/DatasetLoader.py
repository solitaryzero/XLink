import json
import os
from models import Mention, Candidate
from typing import List, Tuple


class DatasetLoader:
    @classmethod
    def load_dataset(cls, dataset_dir, annotation_file_name="annotations.json") -> Tuple[List[List[Mention]], List[str]]:
        annotation_path = os.path.join(dataset_dir, annotation_file_name)
        doc_path = os.path.join(dataset_dir, "docs.json")
        mentions = json.load(open(annotation_path, "r"))
        docs = json.load(open(doc_path, "r"))   # type: List[str]

        mention_list = []
        for doc_mentions in mentions:
            doc_mention_list = []
            for start, end, label, candidate_id in doc_mentions:
                mention = Mention(int(start), int(end), label)
                mention.candidates = []
                if candidate_id != "NIL":
                    candidate = Candidate(candidate_id)
                    mention.add_candidate(candidate)
                    mention.set_result_cand(candidate)
                doc_mention_list.append(mention)
            mention_list.append(doc_mention_list)
        return mention_list, docs

