"""
WordManager holds all words who have embeddings.
"""
from evaluation.build_dataset.modules.VecModel import VecModel


class WordManager:
    vec_model = None    # type: VecModel

    def get_word_vec_model(self, vec_path=""):
        if self.vec_model is None:
            self.vec_model = VecModel(vec_path)
        return self.vec_model

    def get_word_emb(self, word):
        if self.vec_model is None: return None
        return self.vec_model.vectors.get(word)

    def is_word_valid(self, word):
        if self.vec_model is None: return False
        return self.vec_model.vectors.get(word) is not None


class BaiduWordManager(WordManager):
    source = "bd"       # type: str
    language = "zh"     # type: str

    def __new__(cls, vec_path, force_reload=False):
        if not hasattr(BaiduWordManager, 'instance'):
            cls.instance = super(BaiduWordManager, cls).__new__(cls)
            cls.instance.vec_model = VecModel(vec_path)
        if force_reload:
            cls.instance.vec_model = VecModel(vec_path)
        return cls.instance

class WikiWordManager(WordManager):
    source = "wiki"
    language = "en"

    def __new__(cls, vec_path, force_reload=False):
        if not hasattr(WikiWordManager, 'instance'):
            cls.instance = super(WikiWordManager, cls).__new__(cls)
            cls.instance.vec_model = VecModel(vec_path)
        if force_reload:
            cls.instance.vec_model = VecModel(vec_path)
        return cls.instance