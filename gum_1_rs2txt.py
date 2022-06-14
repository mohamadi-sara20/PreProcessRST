from bs4 import BeautifulSoup
import sys
import stanza
import re
import os

nlp = stanza.Pipeline(lang='en')

def rst2txt(filepath):
    outfile = open(filepath + '.txt', 'w')
    rst = open(filepath , 'r').read()
    rst = '<xml>' + rst + '</xml>'
    soup = BeautifulSoup(rst, features='lxml')
    seg_ind = 1
    tok_ind = 0
    segments = soup.find_all('segment')
    doc = ''
    for segment in segments:
        doc_obj = nlp(segment.text)
        tokens = []
        for s in doc_obj.sentences:
            for t in s.tokens:
                doc += t.text + ' '
    doc = doc.replace(' .', ' .\n')
    doc = re.sub(r'…', ' … ', doc)
    # doc = re.sub(r'( .\n){2,}', ' … ', doc)
    doc = re.sub(r"-", " - ", doc)
    doc = re.sub('[ ]{2,}', ' ', doc)

    outfile.write(doc.strip())

if __name__ == "__main__":
    print('====================== rst 2 text =================')
    path = sys.argv[1]
    if path.endswith('/'):
        path = path[:len(path)-1]
    all_files = os.listdir(path)
    counter = 0
    for filename in sorted(all_files):
        if not filename.endswith('.rs3'):
            continue
        filename = filename.split('.rs3/')[0]
        try:
            rst2txt(f'{path}/{filename}')
        except Exception as ex:
            print('###################################################')
            print(ex)
            print(filename)

        counter += 1
        if counter % 10 == 0:
            print("Progress: {} / {}".format(counter, len(all_files)))

