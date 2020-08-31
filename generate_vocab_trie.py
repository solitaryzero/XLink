import os, json
from datatool.pipeline.generate_prob_files import Parser
from jpype import *

def init_JVM():
    from config import Config
    jar_path = Config.project_root + "data/jar/BuildIndex.jar"

    if not isJVMStarted():
        startJVM(getDefaultJVMPath(), "-Djava.class.path=%s" % jar_path)
    if not isThreadAttachedToJVM():
        attachThreadToJVM()
    JDClass = JClass("edu.TextParser")
    return JDClass

if __name__ == "__main__":
    source, corpus_name = "bd", "abstract"
    # data_path       = "/mnt/sdd/zxr/xlink/{}/".format(source)
    data_path = '/mnt/sdd/zfw/xlink2020/%s/' %(source)

    JDClass = init_JVM()

    vocab_txt_path = os.path.join(data_path, "vocab_word.txt")
    vocab_trie_path = os.path.join(data_path, "vocab_word.trie")

    if (os.path.exists(vocab_trie_path)):
        os.remove(vocab_trie_path)

    parser = Parser.get_instance(vocab_txt_path, vocab_trie_path, JDClass)

    shutdownJVM()