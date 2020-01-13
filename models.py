from typing import List


class Entity:
    ID = None           # type: str
    full_title = None   # type: str
    title = None        # type: str
    sub_title = None    # type: str
    language = None     # type: str
    source = None       # type: str
    embed = None        # type: List[float]

    def __init__(self, entity_id, title, sub_title, source, language, embed=None):
        self.ID = entity_id
        self.full_title = title + sub_title
        self.title = title
        self.sub_title = sub_title
        self.source = source
        self.language = language
        self.embed = embed

    def set_embed(self, embed: List[float]):
        self.embed = embed

    def get_full_title(self):
        return self.full_title


class Candidate:
    entity_id = None            # type: str
    entity    = None            # type: Entity
    context_words_sim = None    # type: float
    context_entities_sim = None # type: float
    e_given_m = None            # type: float

    believe_score = None        # type: float

    def __init__(self, entity_id, entity_title=""):
        self.entity_id = entity_id
        self.entity_title = entity_title

    def set_context_words_sim(self, similarity: float):
        self.context_words_sim = similarity

    def set_context_entities_sim(self, similarity: float):
        self.context_entities_sim = similarity

    def set_e_given_m(self, prob: float):
        self.e_given_m = prob

    def set_entity(self, entity: Entity):
        self.entity = entity

    def set_believe_score(self, score: float):
        self.believe_score = score


class Mention:
    label = None        # type: str
    candidates = []     # type: List[Candidate]
    start = None        # type: int
    end   = None        # type: int

    prev_context = None         # type: List[str]
    after_context = None        # type: List[str]
    context_entities = None     # type: List[Entity]

    result_cand = None      # type: Candidate
    gold_entity = None      # type: Entity

    believe_score = None    # type: float

    parse_from = None       # type: str

    def __init__(self, start, end, mention_str, candidates=None):
        self.start = start
        self.end = end
        self.label = mention_str
        if candidates is None:
            self.candidates = []
        else:
            self.candidates = Candidate

    def add_candidate(self, candidate: Candidate):
        self.candidates.append(candidate)

    def set_prev_context(self, context_words):
        self.prev_context = context_words

    def set_after_context(self, context_words):
        self.after_context = context_words

    def set_context_entities(self, context_entities: List[Entity]):
        self.context_entities = context_entities

    def set_result_cand(self, candidate):
        self.result_cand = candidate

    def set_gold_entity(self, entity: Entity):
        self.gold_entity = entity

    def set_believe_score(self, score: float):
        self.believe_score = score

    def __str__(self):
        return "{}, {}, {}, {}".format(self.start, self.end, self.label, "::=".join([cand.entity_id for cand in self.candidates]))

