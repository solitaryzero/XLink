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

    title_entity_txt_path = os.path.join(data_path, "title_entities.txt")
    title_entity_trie_path = os.path.join(data_path, "title_entities.trie")

    if (os.path.exists(title_entity_trie_path)):
        os.remove(title_entity_trie_path)

    parser = Parser.get_instance(title_entity_txt_path, title_entity_trie_path, JDClass)

    shutdownJVM()