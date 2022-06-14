import stanza
import sys
import os
import re
import traceback
import stanza
from stanza.utils.conll import CoNLL
import spacy

def txt2conll(nlp, file_path):
    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>' + file_path)
    with open(f'{file_path}.txt') as f:
        text = f.readlines()
        
    newConll = []
    for sent in text:
        doc = nlp(sent)
        conll = CoNLL.doc2conll(doc)
        for s in conll:
            for token in s:
                newConll.append(token)
            # token = str(sent_ind) + '\t' + token
            # newConll.append(token)
        # sent_ind += 1
        newConll.append('\n')
    
    conllCombinedPPs = combinePPs('\n'.join(newConll))
    
    with open(f'{file_path}.conll', 'w') as f :
        for row in conllCombinedPPs:
            f.write(row+'\n')


def txt2conll_nltk(nlp, file_path):
    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>' + file_path)
    with open(f'{file_path}.txt') as f:
        text = f.readlines()
        
    newConll = []
    for sent in text:
        doc = nlp(sent)
        conll = CoNLL.doc2conll(doc)
        for s in conll:
            for token in s:
                newConll.append(token)
            # token = str(sent_ind) + '\t' + token
            # newConll.append(token)
        # sent_ind += 1
        newConll.append('\n')
    
    conllCombinedPPs = combinePPs('\n'.join(newConll))
    
    with open(f'{file_path}.conll', 'w') as f :
        for row in conllCombinedPPs:
            f.write(row+'\n')

def txt2spacy(nlp, file_path):
    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>' + file_path)
    with open(f'{file_path}.txt') as f:
        text = f.read()
    text = re.sub('\n', ' ', text)
    text = re.sub('\s+', ' ', text)
    
    with open(f'{file_path}.txt_spacy', 'w') as f:
        f.write(text)
    
    newConll = []
    
    os.system(f'parse-as-conll de_dep_news_trf spacy --input_str "{text}" > {file_path}.conll_spacy')
    # for sent in text:
    #     doc = nlp(sent)
    #     conll = CoNLL.doc2conll(doc)
    #     for s in conll:
    #         for token in s:
    #             newConll.append(token)
    #         # token = str(sent_ind) + '\t' + token
    #         # newConll.append(token)
    #     # sent_ind += 1
    #     newConll.append('\n')
    
    # conllCombinedPPs = combinePPs('\n'.join(newConll))
    
    # with open(f'{file_path}.conll_spacy', 'w') as f :
    #     for row in conllCombinedPPs:
    #         f.write(row+'\n')

def combinePPs(conll):
    tokens = conll.split('\n')
    pat = re.compile('\d+-\d+')
    newConll = []
    counter = 0
    while counter < len(tokens):
        found = re.findall(pat, tokens[counter])
        if found:
            comb = tokens[counter].split('\t')
            prep = tokens[counter+1].split('\t')
            det = tokens[counter+2].split('\t')
            comb[3] = prep[3]
            comb[4] = prep[4]
            comb[5] = prep[5]
            comb[6] = det[6]
            newConll.append('\t'.join(comb))
            counter += 3
        else:
            newConll.append(tokens[counter])
            counter += 1
    return newConll

if __name__ == "__main__":
    print('====================== text 2 conll =================')
    # if len(sys.argv) > 1:
    data_dir = 'pcc2/'
    nlp = stanza.Pipeline('de')
    spacy_nlp = spacy.load("de_dep_news_trf")

    all_files = os.listdir(data_dir)
    counter = 0
    for filename in sorted(all_files):
        if not filename.endswith('.txt'):
            continue
        filename = filename.split('.txt')[0]
        try:
            # txt2conll(nlp, f'{data_dir}/{filename}')
            txt2spacy(nlp, f'{data_dir}/{filename}')
        except Exception as ex:
            print('###################################################')
            print(filename)
            print(ex)
            traceback.print_exc()
    else:
        print('Please specify a path to txt files!!')

