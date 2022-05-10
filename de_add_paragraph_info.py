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
    return  ps_content, content[-3], "\n".join(content[:-3])

def modify_ranges(content, tree, old_content):
    firstSent = True
    leaves = re.findall("\\( leaf \w+ \d+ \d+ \)", tree)
    old_content = ' '.join(old_content.split('\n'))
    old_content_words = old_content.split()
    content_words = content.split()
    sents = content.split("\n")
    newTree = tree
    for i in range(len(leaves)):
        leaf_info = leaves[i].split()
        start, end = leaf_info[-3], leaf_info[-2]
        # assert (sents[i].split()[-1] == '<S>' or  sents[i].split()[-1] == '<P>')
        if firstSent:
            leaf_info[-2] = str(int(end) + 1)
            firstSent = False
        else:
            # if "<S>" in sents[int(leaf_info[-3]):int(leaf_info[-2])+1]or "<P>" in sents[int(leaf_info[-3]):int(leaf_info[-2])+1]:
            leaf_info[-3], leaf_info[-2] =   str(int(start) + i)  , str(int(end) + i) 
            # else:
            #     leaf_info[-3], leaf_info[-2] =   str(int(start) + i )  , str(int(end) + i) 
                
        newLeaf = ' '.join(leaf_info)
        newTree = newTree.replace(leaves[i], newLeaf)

    return newTree

if __name__ == "__main__":
    trees = 'trees/'
    files = os.listdir(trees)
    for fname in files:
        if 'maz-19150' in fname:
            print()
        if fname.endswith('prep'):
            ps_content, rstree, old_content = add_paragraph_info(trees + fname)
            newTree = modify_ranges(ps_content, rstree, old_content)
            sents = ps_content.split("\n")
            with open(f'{trees}/{fname[:-5]}.prep2', 'w') as f:
                for i in range(len(sents)):
                    f.write(sents[i]+ '\n')
                for i in range(len(sents)):
                    f.write('Tree\n')
                f.write(newTree + '\n\n') 
                
    print()