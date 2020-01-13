import datetime
import struct
import time


class BinaryReader:
    @staticmethod
    def readStringWithoutBlank(f):
        try:
            seq = bytes()
            b = f.read(1)
            while 1:
                if b == b' ' or b == b'\n' or b == b'\t' or b == b'':
                    break
                seq += b
                b = f.read(1)
            return bytes.decode(seq)
        except EOFError:
            pass

    @staticmethod
    def readStringWithBlank(f):
        try:
            seq = bytes()
            b = f.read(1)
            while 1:
                if b == b'\t' or b == b'\n' or b == b'':
                    break
                seq += b
                b = f.read(1)
            # print(seq)
            return bytes.decode(seq)
        except EOFError:
            pass

    @staticmethod
    def readFloat(f):
        try:
            b = f.read(4)
            return struct.unpack('f', b)[0]
        except:
            pass


class VecModel:
    def __init__(self, vec_path):
        self.vec_path = vec_path
        self.file = open(self.vec_path, 'rb')
        self.words_num = int(BinaryReader.readStringWithoutBlank(self.file))
        self.vec_size  = int(BinaryReader.readStringWithoutBlank(self.file))
        self.vectors   = {}
        self.loadAllWords()

    def __del__(self):
        self.file.close()

    def refreshFilePointer(self):
        self.file.close()
        self.file = open(self.vec_path, 'rb')
        self.words_num = int(BinaryReader.readStringWithoutBlank(self.file))
        self.vec_size = int(BinaryReader.readStringWithoutBlank(self.file))

    def getDataSize(self):
        return self.words_num, self.vec_size

    def readOneWordEmbedding(self):
        try:
            vec  = []
            word = BinaryReader.readStringWithBlank(self.file)
            for i in range(0, self.vec_size):
                vec.append(BinaryReader.readFloat(self.file))
            BinaryReader.readStringWithoutBlank(self.file)
            return word, vec
        except EOFError:
            return ['', []]
            pass

    def loadAllWords(self):
        try:
            print('\nLoading embeddings from {}，expected num: #{}'.format(self.vec_path, self.words_num))
            start_time = time.time()
            self.refreshFilePointer()
            self.vectors = {}
            counter = 0
            while 1:
                counter += 1
                if counter %100000 == 0:
                    print("\t#"+str(counter))
                word, vec = self.readOneWordEmbedding()

                if word != '':
                    self.vectors[word] = vec
                else:
                    if counter >= self.words_num:
                        break

            print('Loaded, excepted num #{}, loaded: #{}, time: {}'.format(
                self.words_num, counter, str(datetime.timedelta(seconds=int(time.time())-start_time))))
            return self.vectors
        except EnvironmentError:
            pass