from concurrent.futures import process
from bs4 import BeautifulSoup
import sys
import stanza
import re
import os
import json
from stanza.utils.conll import CoNLL

nlp = stanza.Pipeline(lang='de')

def load_preps(filename):
    with open(filename) as f_in:
        return json.load(f_in)

prep_dict = load_preps('prepositions.json')

def rst2txt(filepath):
    primary_dir = 'pcc/primary-data/'
    fname = filepath.split('.')[0]
    txt_name = fname.split('/')[-1] + '.txt'
    with open(primary_dir + txt_name) as f:
        primary_text = f.read()
    outfile = open(fname + '.txt', 'w')
    with open(filepath) as f:
        rst_txt = f.read()
    rst = open(filepath , 'r').read()
    rst = '<xml>' + rst + '</xml>'
    soup = BeautifulSoup(rst, features='lxml')
    segments = soup.find_all('segment')
    for segment in segments:
        idx = segment.attrs['id']
        if not "parent" in segment.attrs and not f'parent="{idx}"' in rst_txt:
            print('>>>>>>>>>>>>>>>>>>>>>>>> Unused Segment, id=', idx)
            # primary_text.replace(segment.text, '')
            st_idx = primary_text.find(segment.text.strip())
            if st_idx == 0:
                primary_text = primary_text.replace(segment.text.strip(), '')
            else:
                primary_text = primary_text[st_idx:]
                primary_text = primary_text.replace(segment.text.strip(), '')
    
    
    for p in prep_dict:
        if " " + p + " " in primary_text:
            primary_text = primary_text.replace(" " + p + " ", " " + prep_dict[p] + " ")
            
    primary_text = re.sub('\n{3,}', '', primary_text)
    primary_text = re.sub('\n\n', '\n', primary_text)
    outfile.write(primary_text.strip())

def edit_rst_content(path, filename):
    with open(f'{path}/{filename}') as f:
        rst_text = f.read()
        rst_text = re.sub("(>)\n+(\w+)", "\\1\\2", rst_text)
        for p in prep_dict:
            if " " + p + " " in rst_text:
                rst_text = rst_text.replace(" " + p + " ", " " + prep_dict[p] + " ")
    with open(f'{path}/{filename}', 'w') as f:
        f.write(rst_text)



def de_rst2txt(filepath):
    with open(filepath) as f:
        rst_txt = f.read()
    fname = filepath.split('.')[0]
    outfile = open(fname + '.txt', 'w')
    rst = open(filepath , 'r').read()
    rst = '<xml>' + rst + '</xml>'
    soup = BeautifulSoup(rst, features='lxml')
    segments = soup.find_all('segment')
    doc = ''
    for segment in segments:
        idx = segment.attrs['id']
        if not "parent" in segment.attrs and not f'parent="{idx}"' in rst_txt:
            pass
        else:
            processed = nlp(segment.text)
            for sent in processed.sentences:
                doc += sent.text + '\n' 
                
    for p in prep_dict:
        doc = re.sub(f'^{p}\\s+|\\s+{p} ', f' {prep_dict[p]} ', doc)
        
    doc = doc.strip()
    doc = doc.replace('-', ' - ')
    doc = re.sub('\n{2,}', '', doc)
    doc = re.sub('[ ]{2,}', ' ', doc)
    outfile.write(doc.strip())



def de_rst2segment(filepath):
    with open(filepath) as f:
        rst_txt = f.read()
    fname = filepath.split('.')[0]
    outfile = open(fname + '.segment', 'w')
    rst = open(filepath , 'r').read()
    rst = '<xml>' + rst + '</xml>'
    soup = BeautifulSoup(rst, features='lxml')
    segments = soup.find_all('segment')
    doc = ''
    for segment in segments:
        idx = segment.attrs['id']
        if not "parent" in segment.attrs and not f'parent="{idx}"' in rst_txt:
            pass
        else:
            
            segtext = ''
            text = segment.text
            text = re.sub('-', ' - ', text)
            text = re.sub('(\\d+)\\.', '\\1 .', text)
            for p in prep_dict:
                text = re.sub(f'(\\s+){p}(\\s+)', f'\\1{prep_dict[p]}\\2', text)
                text = re.sub(f'^{p}\\s+', f'{prep_dict[p]} ', text)
            processed = nlp(text)
            conll = CoNLL.doc2conll(processed)
            for s in conll:
                st,end='-1','-1'
                for token in s:
                    if '-' not in token.split('\t')[0] and bool(st) and st not in token.split('\t')[0] and bool(end) and not end in token.split('\t')[0]:
                        segtext += token.split('\t')[1] + ' '
                    elif bool(st) and st == token.split('\t')[0]:
                        st = '-1'
                    elif bool(end) and end == token.split('\t')[0]:
                        end = '-1'
                    else:
                        st,end = token.split('\t')[0].split('-')
                        rest = token.split('\t')[1]
                        segtext += rest + ' '
                        print('<UNK> occurred! ')
            doc += segment.attrs['id'] + '\t' + segtext + '\n'
            
    doc = doc.strip()
    doc = re.sub('\n{2,}', '', doc)
    doc = re.sub('[ ]{2,}', ' ', doc)
    outfile.write(doc.strip())


if __name__ == "__main__":
    print('====================== rst 2 text =================')
    if len(sys.argv) > 1:
        path = sys.argv[1]
    path = 'test/'
    if path.endswith('/'):
        path = path[:len(path)-1]
    all_files = os.listdir(path)
    counter = 0
    for filename in sorted(all_files):
        if not filename.endswith('.rs3'):
            continue
        filename = filename.split('.rs3/')[0]

        try:
            # if '18945' in filename:
            de_rst2txt(f'{path}/{filename}')
            de_rst2segment(f'{path}/{filename}')
        except Exception as ex:
            print('###################################################')
            print(ex)
            print(filename)
        counter += 1
        if counter % 10 == 0:
            print("Progress: {} / {}".format(counter, len(all_files)))

