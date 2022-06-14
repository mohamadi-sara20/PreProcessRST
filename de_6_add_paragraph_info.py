import sys
import os
import re

def add_paragraph_info(fname):
    with open(fname) as f:
                content = f.read().split('\n')
                tr_cont = ''
                length = len(content)
                tr = content[:(length-3)//2]
                for l in tr:
                    words = l.split()
                    for w in words:
                        word = w.split('_')
                        tr_cont += word[0] + ' '
                    tr_cont += '\n\n'
    tr_conts = tr_cont.split('\n\n')
    txt_name = fname[:-5]
    tr_conts = list(filter(None, tr_conts))
    with open(txt_name + '.txt') as f:
        txt = f.read().replace('\n\n', '\n').split('\n')[2:]
        
    txt = list(filter(None, txt))
    for par in txt:
        for i in range(len(tr_conts)):
            par = re.sub('(\\?|\\!|\\.|-|\\(|\\)|"|:|;|,)', ' \\1 ', par)
            par_words = par.split()
            res = tr_conts[i].strip().endswith(par_words[-2] + ' ' + par_words[-1])
            if res:
                tr_conts[i] += "<P>"
                res = None
    
    for i in range(len(tr_conts)):
        if "<P>" not in tr_conts[i]:  
            content[i] += "<S>"
        else:
            content[i] += "<P>"
    ps_content = "\n".join(content[:len(content)//2 - 1])
    return  ps_content, ps_content.split(), content[-3], "\n".join(content[:-3])

def modify_ranges2(content, tree):
    leaves = re.findall("\\( leaf \w+ \d+ \d+ \)", tree)
    newTree = tree

    sp_count = 0
    for i in range(len(leaves)):
        leaf_info = leaves[i].split()
        start, end = int(leaf_info[-3]), int(leaf_info[-2])

        orig_index = start
        new_start = start + sp_count
        while (orig_index <= end) :
            token = content[orig_index + sp_count]
            if token == "<S>" or token == "<P>":
                sp_count += 1
                continue
            orig_index += 1
        
        next_token = content[orig_index + sp_count]
        if next_token == "<S>" or next_token == "<P>":
             sp_count += 1
        new_end = end + sp_count
        
        leaf_info[-3], leaf_info[-2] = str(new_start), str(new_end)
        newLeaf = '%'.join(leaf_info)
        newTree = newTree.replace(leaves[i], newLeaf, 1)
    return newTree.replace('%', ' ')
    

def check_rst_file(f, file_name):
    lines = f.read().split("\n")
    tokens = 0
    tokens_finished = False
    tree = ''
    for line in lines:
        if line == 'Tree':
            tokens_finished = True
            continue
        if not tokens_finished:
            tokens += len(line.strip().split(' '))
        else:
            tree = line
            break
    
    res = re.findall(" \d+ \d+", tree)
    # if len(res) == 0:
    #     raise Exception(f'No segment found {file_name}')
    ids = []
    for i in res:        
        a,b = i.split()
        a,b = int(a), int(b)
        ids.append(a)
        ids.append(b)
    
    max_token = ids[-1]
    if (max_token != tokens - 1):
        print(f"------ Tokens in segments {max_token} is different from tokens in text {tokens} - {file_name}")
    for i in range(2, len(ids), 2):
        if not ids[i-1] + 1 == ids[i]:
            print(">>>>>>>>>> segment ends with: " + str(ids[i-1]) + " - next segment starts with: " + str(ids[i]))
    
    
def check_sets(data_path):
    with open(data_path) as f:
        content = f.read().split('\n\n')
    for tree in content:
        tr = tree.split('\n')[-1]
        res = re.findall(" \d+ \d+", tree)
        ids = []
        for i in res:        
            a,b = i.split()
            a,b = int(a), int(b)
            ids.append(a)
            ids.append(b)
        
        # Check node ids are consecutively incremented 
        for i in range(2, len(ids), 2):
            if not ids[i-1] + 1 == ids[i]:
                print(ids[i-2], ids[i-1])
    
    
if __name__ == "__main__":
    print('====================== adding <P> & <S> to trees =================')
    if len(sys.argv) > 1:
        trees = sys.argv[1]
        files = os.listdir(trees)
        
        # Check alignment before applying changes
        for fname in files:
            if fname.endswith('prep'):
                with open(f'{trees}/{fname}', 'r') as f:
                    check_rst_file(f, fname)
                    
        for fname in files:
            if '3415' in fname:
                    print()
            if fname.endswith('conll'):
                ps_content, ps_content2, rstree, old_content = add_paragraph_info(trees + fname[:-6]+".prep")
                newTree = modify_ranges2(ps_content2, rstree)
                sents = ps_content.split('\n')
                with open(f'{trees}/{fname[:-5]}prep2', 'w') as f:
                    for i in range(len(sents)):
                        f.write(sents[i]+ '\n')
                    for i in range(len(sents)):
                        f.write('Tree\n')
                    f.write(newTree + '\n\n') 

        # Check alignment before applying changes
        for fname in files:
            if fname.endswith('prep2'):
                with open(f'{trees}/{fname}', 'r') as f:
                    check_rst_file(f, fname)
                    
        print()