from logging import root
import re
import json
import os
import stanza
import sys
import glob
from stanza.server import CoreNLPClient

os.environ['$CORENLP_HOME'] = "/Users/sara/stanford-corenlp-4.3.2/*"
os.environ['$CLASSPATH'] = "/Users/sara/stanford-corenlp-4.3.2/*"


def pos_const_rst_builder(nlp, txt_filename):
    with open(txt_filename) as f:
        text = f.read().strip()


    doc = nlp(text)
    text_pos = ''

    for sent in doc.sentences:
        for word in sent.words:
            print("WORD IS", word)
            print('file: ', txt_filename)
            text_pos += word.text + "_" + word.xpos + " "
        text_pos += '\n'
    with CoreNLPClient(
        properties={
            'annotators': "tokenize,ssplit,pos,lemma,ner,parse,depparse",
            'tokenize.language': 'de',
            'pos.model': 'edu/stanford/nlp/models/pos-tagger/german-ud.tagger',
            'parse.model': 'edu/stanford/nlp/models/srparser/germanSR.ser.gz',
            'outputFormat': 'json'
            },
            classpath="/Users/sara/stanford-corenlp-4.3.2/*",
        timeout=30000,
        memory='10G',
        be_quiet=False) as client:
        sentences = client.annotate(text)


    # print("===================================", len(sentences))

    # for sent in sentences:
    #    print("===================================", sent)

    return text_pos

def main(data_dir):
    
    nlp = stanza.Pipeline(lang='de')
    txt_files = glob.glob(data_dir + "/*.txt")
    rst_files = glob.glob(data_dir + "/*.rs3")
    fns = [fn.split('/')[-1].split('.')[0] for fn in txt_files]
    print(fns)

    for fn in fns:
        pos_tags = pos_const_rst_builder(nlp, f'{data_dir}/{fn}.txt')
        with open(f'{data_dir}/output/{fn}.prep', 'w') as fh:
            # fh.write(pos_tags)
            fh.write('\n')
            # fh.write(const_parse_trees)
            fh.write('\n')
            # fh.write(rst_tree)
            fh.write('\n')


if __name__ == '__main__':
    data_dir = './pcc3'
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    if not os.path.isdir(f'{data_dir}/output'):
        os.mkdir(f'{data_dir}/output')
    main(data_dir)


    
