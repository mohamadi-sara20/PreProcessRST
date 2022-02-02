from bs4 import BeautifulSoup
import sys
import html
import os
import json

def load_preps(filename):
    with open(filename) as f_in:
        return json.load(f_in)

prep_dict = load_preps('prepositions.json')

def merge(file_path, filename):
    print(filename)
    # ners = add_ner(f'data/de/ner/{filename}.ner')
    conll = open(file_path + '.conll', 'r').readlines()
    rst = open(file_path + '.rs3', 'r').read()
    rst = '<xml>' + rst + '</xml>'
    soup = BeautifulSoup(rst, features='lxml')
    seg_ind = 0
    text_ind = 0
    segments = soup.find_all('segment')

    for tok_ind in range(len(conll)):
        if conll[tok_ind] == '\n':
            continue
        
        word = conll[tok_ind].split('\t')[1].strip()
        segment = html.unescape(segments[seg_ind].text.strip())

        orig_ind = text_ind
        text_ind = segment.find(word, text_ind) 

        if text_ind < 0:
            text_ind = segment.find(word.replace('.', '. '), orig_ind)
            if text_ind < 0: 
                text_ind = segment.find(word.replace('.', ' .'), orig_ind)
                if (text_ind >= 0):
                    word = word.replace('.', ' .')
            else: 
                word = word.replace('.', '. ')
 
            if text_ind < 0:
                print('###',word)
                print('$$$', segment)
                raise IOError(f'Word <{word}> was not found in segment {seg_ind + 1}')

        conll[tok_ind] = conll[tok_ind].strip() +  '\t' + str(seg_ind + 1)
        text_ind += len(word)

     
        if text_ind >= len(segment):
            seg_ind += 1
            text_ind = 0

    text = '\n'.join(conll)
    f_merge = open(file_path + '.merge', 'w')
    f_merge.write(text)



if __name__ == "__main__":
    print('====================== conll 2 merge =================')
    path = 'pcc'
    if path.endswith('/'):
        path = path[:len(path) - 1]
    all_files = os.listdir(path)
    for filename in sorted(all_files):
        if not filename.endswith('.conll'):
            continue
        filename = filename.split('.conll')[0]
        print (filename)
        merge(f'{path}/{filename}', filename)

