from curses import nl
import stanza
from stanza.utils.conll import CoNLL
import sys
import os

global nlp


def make_conll(data_dir, fname):
    first_line = True
    fn = fname.split('.txt')[0]
    with open(f'{data_dir}/{fname}') as f:
        text = f.read()
        
    doc  = nlp(text)
    conll = CoNLL.doc2conll(doc)
    ch9 = open(f'{data_dir}/{fn}.conll', 'w')

    for c in conll:
        if not first_line:
            ch9.write('\n')
        first_line = False
        for j in range(len(c)):
            content = c[j].split('\t')
            if content[5] == '_':
                features_rewritten = '_'
            else:
                features = content[5].split('|')
                features_rewritten = ''
                for i in range(len(features)):
                    ft = features[i].split('=')[-1].lower()
                    features_rewritten += ft + '|'
            ch9.write(f'{content[0]}\t{content[1]}\t{content[2]}\t{content[2]}\t{content[3]}\t{content[4]}\t{features_rewritten}\t{features_rewritten}\t{content[6]}\t{content[6]}\t{content[7]}\t_\n')
            features_rewritten = ''
            
            

if __name__ == '__main__':
    nlp = stanza.Pipeline('de')
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    else:
        data_dir = 'segs'
    
    files = os.listdir(data_dir)
    for fname in files:
        make_conll(data_dir=data_dir, fname=fname)
        
         
        

    