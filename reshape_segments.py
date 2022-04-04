import os, sys, stanza, re


def reshape_output(data_dir, fname):
    fn = fname.split('.seg')[0]
    with open(f'{data_dir}/{fname}') as f:
        text = f.read()
    text = re.sub('\\(HSF|\\(HS', '\n', text)
    text = re.sub('-OP- ! -CP-|\\(OBJ|\\(SUB', '', text)
    text = re.sub('\\)', '', text)
    text = re.sub('^ ', '', text)
    text = re.sub('\\n ', '\n', text)
    text = re.sub('\\n{2,}', '\n', text)
    text = re.sub(' {2,}', ' ', text)

    text = text.strip()
    with open(f'{data_dir}/{fn}.txt', 'w') as f:
        f.write(text)
    
    return text

if __name__ == '__main__':
    nlp = stanza.Pipeline('de')
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    else:
        data_dir = 'seg_output'
    
    files = os.listdir(data_dir)
    for fname in files:
        if fname.endswith('.seg'):
            reshape_output(data_dir, fname)  