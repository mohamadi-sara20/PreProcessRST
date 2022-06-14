import stanza
import sys
import os
import re
import traceback

def txt2conll(nlp, file_path):
    with open(f'{file_path}.txt') as f:
        text = f.read()
    outfile = open(f'{file_path}.conll', 'w')
    


    doc = nlp(text)
    # sentence id
    sent_id = 0
    word_ind = 0
    parse_ind = 0

    for i, sentence in enumerate(doc.sentences):
        word_ind = 1
        for word in sentence.words:
            word_ner = 0
            if word.lemma is None:
                word_lemma = word.text
            else:
                word_lemma = word.lemma.split("#")[-1]

            # if(not w):
            #     word_ind +=1
            #     w = ners[word_ind][0]

            for ent in doc.ents:
                if word == ent.text:
                    word_ner = ent.type
            
            word_upos = word.upos
            word_pos_tag = word.xpos
            word_dependency_tag = word.deprel
            word_head = word.head
            # word_ner = 0
            parse = sentence.constituency
            feats = word.feats
            # parse_end = find_partial_parse(parse, parse_ind, word.text)

            # if (parse_end < 0):
            #     word_partial_parse = '_'
            # else:
            #     word_partial_parse = parse[parse_ind: parse_end]
            #     parse_ind = parse_end

            # if (len(word_partial_parse) == 0):
            #     word_partial_parse = '_'
                
            outfile.write(f'{word_ind}\t{word.text}\t{word_lemma}\t{word.upos}\t{word_pos_tag}\t{feats}\t{word_head}\t{word_dependency_tag}\t{word_ner}\n')
            word_ind+=1
        # outfile.write('\n')

def find_partial_parse(text, begin, word):
    index = text.find(word, begin)
    if (index < 0):
        return -1
    index += 1
    while(index < len(text)):
        if (text[index] == '('):
            break
        index += 1
    return index



if __name__ == "__main__":
    print('====================== text 2 conll =================')
    nlp = stanza.Pipeline(lang='en')
    path = sys.argv[1]
    
    if path.endswith('/'):
        path = path[:len(path)-1]
    all_files = os.listdir(path)
    counter = 0
    for filename in sorted(all_files):
        if not filename.endswith('.txt'):
            continue
        filename = filename.split('.txt')[0]
        try:
            txt2conll(nlp, f'{path}/{filename}')
        except Exception as ex:
            print('###################################################')
            print(filename)
            print(ex)
            traceback.print_exc()

        counter += 1
        if counter % 10 == 0:
            pass
            # print("Progress: {} / {}".format(counter, len(all_files)))
