import sys, os, re


def replace_problematic_words_in_embeddings(fpath):
    with open(fpath) as f:
        content = f.read()
    
    content = content.replace("_der", "der")
    content = content.replace("_Heide", "Heide")
    content = content.replace("A_0", "A2")
    content = content.replace("B_96", "B96")
    content = re.sub("^(\d+)_(\d+ )", "\\1\\2")
    with open(fpath, 'w') as f:
        f.write(content)
    
    
    
    

if __name__ == '__main__':
    print('====================== combining trees to one single file =================')
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
        pcc_dir = sys.argv[2]       
       
     