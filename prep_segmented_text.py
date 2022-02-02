import stanza
import sys
import os

def prepare_segmented_tree(nlp, fname, fmerge):
    with open(fname) as f:
        text = f.read()
    outname = fname + '.prep'
    out_file = open(outname, 'w')
    text_pos = ''
    doc = nlp(text)
    for sent in doc.sentences:
        for word in sent.words:
            out_file.write(word.text + "_" + word.xpos + " ")
        out_file.write('\n')
    
    for sent in doc.sentences:
        out_file.write(str(sent.constituency))
        out_file.write('\n')
        
    leaf_idx = prepare_leaf_idx(fmerge)
    out_file.write(leaf_idx.strip())
    out_file.write('\n\n')
    out_file.close()

    return text_pos

def prepare_leaf_idx(fname):
    out = ''
    conll = open(fname).readlines()
    
    current_tok_id_start = 0
    current_tok_id_end = 0
    current_segment = 1
    current_tok_str = ' ( leaf t ' + str(current_tok_id_start) + ' '

    for tok in conll:
        line = tok.split('\t')
        
        if int(line[-1].strip()) == current_segment:
            current_tok_id_end += 1
        else:
            current_tok_str += str(current_tok_id_end - 1) + " )"
            out += current_tok_str
            current_tok_id_start = current_tok_id_end 
            current_tok_id_end = current_tok_id_end + 1
            current_tok_str = ' ( leaf t ' + str(current_tok_id_start) + ' '
            current_segment += 1
    out += current_tok_str + str(current_tok_id_end - 1) + ' ) '
    return out  

if __name__ == '__main__':
    nlp = stanza.Pipeline('en')
    print('====================== prepare segmented tree =================')
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
            print('ee')
            fname = filename.split('.')[0]
            prepare_segmented_tree(nlp, f'{path}/{fname}.txt', f'{path}/{fname}.merge')
        except Exception as ex:
            print('###################################################')
            print(ex)
            print(filename)

        counter += 1
        if counter % 10 == 0:
            print("Progress: {} / {}".format(counter, len(all_files)))
