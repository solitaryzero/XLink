//  Copyright 2013 Google Inc. All Rights Reserved.
//
//  Licensed under the Apache License, Version 2.0 (the "License");
//  you may not use this file except in compliance with the License.
//  You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
//  Unless required by applicable law or agreed to in writing, software
//  distributed under the License is distributed on an "AS IS" BASIS,
//  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//  See the License for the specific language governing permissions and
//  limitations under the License.

#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>
#include <ctype.h>
#define MAX_STRING 2000

const int N = 1;                  // number of closest words that will be shown
const long long max_w = 50;              // max length of vocabulary entries
char interval_pattern = '\t';
char items[4][MAX_STRING],eval_file[MAX_STRING];
long long bi[4];
int comment_line_num=0;

struct vocab_item{
    char read_file[MAX_STRING];
    char *vocab;
    long long vocab_size, layer_size;
    float *M;
}word;

//return 1 if the fourth word is the top_n nearest words, 0 otherwise.
int FindNearest(int top_n, float *vec){
    float dist, bestd[top_n];
    int bestid[top_n];
    long long a, d;
    float len;
    int is_fourth_correct = 0, c;
    for (a = 0; a < top_n; a++) bestd[a] = -1;
    for (a = 0; a < top_n; a++) bestid[a] = -1;
    
    //normalization
    len = 0;
    for (a = 0; a < word.layer_size; a++) len += vec[a] * vec[a];
    len = sqrt(len);
    for (a = 0; a < word.layer_size; a++) vec[a] /= len;

    //compute distance with each word
    for (c = 0; c < word.vocab_size; c++) {
        //skip self
        if (c == bi[0]) continue;
        if (c == bi[1]) continue;
        if (c == bi[2]) continue;
        a = 0;
        dist = 0;
        for (a = 0; a < word.layer_size; a++) dist += vec[a] * word.M[a + c * word.layer_size];
        for (a = 0; a < top_n; a++) {
            if (dist > bestd[a]) {
                for (d = top_n - 1; d > a; d--) {
                    bestd[d] = bestd[d - 1];
                    bestid[d] = bestid[d-1];
                }
                bestd[a] = dist;
                bestid[a] = c;
                break;
            }
        }
    }
    for (a = 0; a < top_n; a++)
        if(bestid[a]==bi[3]){
            is_fourth_correct = 1;
            break;
        }
    return is_fourth_correct;
}

//return 0 if there is a word out of dic, otherwise 1;
int SearchVocab(){
    int a,b;
    for (a = 0; a < 4; a++) {
        for (b = 0; b <word.vocab_size; b++) if (!strcmp(&word.vocab[b * max_w], items[a])) break;
        if (b == word.vocab_size)
            return 0;
        
        bi[a] = b;
    }
    return 1;
}

//return the number of input items
int GetItem(char *item){
    long long b=0, c=0;
    int cn=0;
    while (1) {
        if(item[c]==':' || cn>=4){
            comment_line_num++;
            cn=-1;
            break;
        }
        
        items[cn][b] = toupper(item[c]);
        b++;
        c++;
        items[cn][b] = 0;
        if (item[c] == 0 || item[c] == '\n') break;
        if (item[c] == ' ') {
            cn++;
            b = 0;
            c++;
        }
    }
    cn++;
    return cn;
}

void ReadVector(){
    FILE *f;
    long long a, b;
    float len;
    f = fopen(word.read_file, "rb");
    if (f == NULL) {
        printf("Input file not found\n");
        return;
    }
    fscanf(f, "%lld", &word.vocab_size);
    fscanf(f, "%lld", &word.layer_size);
    word.vocab = (char *)malloc((long long)word.vocab_size * max_w * sizeof(char));
    word.M = (float *)malloc((long long)word.vocab_size * (long long)word.layer_size * sizeof(float));
    if (word.M == NULL) {
        printf("Cannot allocate memory: %lld MB    %lld  %lld\n", (long long)word.vocab_size * word.layer_size * sizeof(float) / 1048576, word.vocab_size, word.layer_size);
        return;
    }
    for (b = 0; b < word.vocab_size; b++) {
        a = 0;
        while (1) {
            word.vocab[b * max_w + a] = fgetc(f);
            if (feof(f) || (word.vocab[b * max_w + a] == interval_pattern)) break;
            if ((a < max_w) && (word.vocab[b * max_w + a] != '\n')) a++;
        }
        word.vocab[b * max_w + a] = 0;
        for (a = 0; a < max_w; a++) word.vocab[b * max_w + a] = toupper(word.vocab[b * max_w + a]);
        for (a = 0; a < word.layer_size; a++) fread(&word.M[a + b * word.layer_size], sizeof(float), 1, f);
        len = 0;
        for (a = 0; a < word.layer_size; a++) len += word.M[a + b * word.layer_size] * word.M[a + b * word.layer_size];
        len = sqrt(len);
        for (a = 0; a < word.layer_size; a++) word.M[a + b * word.layer_size] /= len;
    }
    fclose(f);
}

int ArgPos(char *str, int argc, char **argv) {
    int a;
    for (a = 1; a < argc; a++) if (!strcmp(str, argv[a])) {
        if (a == argc - 1) {
            printf("Argument missing for %s\n", str);
            exit(1);
        }
        return a;
    }
    return -1;
}

int main(int argc, char **argv) {
    int i, cn, has_word=0, is_correct=0, skip=0, line_count=0, correct_num=0;
    long long a;
    float word_vec[MAX_STRING];
    char *line;
    ssize_t read;
    size_t len;
    FILE *fi;
    
    if (argc < 2) {
        printf("\t-read_word_vector <file>\n");
        printf("\t\tUse <file> to read the resulting word vectors\n");
        printf("\t-eval_file <file>\n");
        printf("\t\tUse <file> to evaluate the analogy results\n");
        printf("\nExamples:\n");
        printf("./distance -read_word_vector ./vec_word -eval_file ./question-words.txt\n\n");
        return 0;
    }
    word.read_file[0] = 0;
    word.vocab_size = 0;
    word.layer_size = 0;
    eval_file[0] = 0;
    if ((i = ArgPos((char *)"-read_word_vector", argc, argv)) > 0) strcpy(word.read_file, argv[i + 1]);
    if ((i = ArgPos((char *)"-eval_file", argc, argv)) > 0) strcpy(eval_file, argv[i + 1]);
    
    if(0!=word.read_file[0]&&0!=eval_file[0]){
        printf("loading word vectors...\n");
        ReadVector();
        if(word.vocab_size>0)
            printf("Successfully load %lld words with %lld dimentions from %s\n", word.vocab_size, word.layer_size, word.read_file);
        fi = fopen(eval_file, "rb");
    
        while(1){
            if((read = getline(&line, &len, fi)) == -1)
                break;
            line_count++;
            if(line_count%100==0)
                printf("process line %d\n",line_count);
            cn = GetItem(line);
            if (4!=cn) continue;
            
            has_word = SearchVocab();
            if(has_word){
                for (a = 0; a < word.layer_size; a++) word_vec[a] = 0;
                for (a = 0; a < word.layer_size; a++) word_vec[a] += word.M[a + bi[1] * word.layer_size]-word.M[a + bi[0] * word.layer_size]+word.M[a + bi[2] * word.layer_size];
                is_correct = FindNearest(N, word_vec);
                if(is_correct) correct_num++;
            }
            else skip++;
        }
        printf("Hit@%d in %d/%d analogy pairs.\n\tprecision: %f \n\tskip %d pairs \n\tcomment %d lines", N, correct_num, line_count, (float)correct_num/(line_count-comment_line_num-skip), skip, comment_line_num);
    }
    return 0;
}
