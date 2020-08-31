CC = gcc -g -rdynamic
#Using -Ofast instead of -O3 might result in faster code, but is supported only by newer GCC versions
CFLAGS = -lm -pthread -Ofast -march=native -Wall -funroll-loops -Wno-unused-result

all: align distance analogy evalWord compute-accuracy

align : align.c
	$(CC) align.c -o align $(CFLAGS)
distance : distance.c
	$(CC) distance.c -o distance $(CFLAGS)
analogy : analogy.c
	$(CC) analogy.c -o analogy $(CFLAGS)
evalWord : evalWord.c
	$(CC) evalWord.c -o evalWord $(CFLAGS)
compute-accuracy : compute-accuracy.c
	$(CC) compute-accuracy.c -o compute-accuracy $(CFLAGS)
	chmod +x *.sh

clean:
	rm -rf align distance analogy evalWord compute-accuracy
