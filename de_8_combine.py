import re 
import sys
import os

def rewrite_conll(outfile, content):
    for sent in content:
        sentence = sent.split('\n')
        for i in range(len(sentence)):
            line = sentence[i]
            if len(line) > 2:
                units = line.split('\t')
                if units[4] == '_':
                    units[4] = '-'
                sentence[i] = units[0] + '\t' + units[1] + '\t_\t' + units[4] + '\t_\t_\t' + units[6] + '\t' + units[7] + '\t_\t_\n'
    return content


def main(read_dir, write_dir, combo_name):
    all_content = ''
    all_conll = ''
    all_files = os.listdir(read_dir)
    all_files.sort()
    
    for file in all_files:
        if file.endswith('.prep'):
            with open(f'{read_dir}/{file}') as f:
                content = f.read()
                content = content.replace("-__", '-_-')
                content = content.replace("_Heide", "Heide")
                content = content.replace("_der", "der")
                content = re.sub("(\w+)_(\w+)_(\w+)", "\\1\\2_\\3", content)
                all_content += content + '\n'
                
        if file.endswith('.conll'):
            with open(f'{read_dir}/{file}') as f:
                conll_content = f.read().split('\n\n')
                corrected_conll = rewrite_conll(f'{write_dir}/{file}2', conll_content)
                conll = '\n\n'.joing(corrected_conll)
                all_conll += conll
    
    with open(f'{write_dir}{combo_name}.pcc', 'w') as f:
        f.write(content)
    with open(f'{write_dir}{combo_name}.conll', 'w') as f:
        f.write(conll)
    

if __name__ == '__main__':
    print('====================== combining trees to one single file =================')
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
        pcc_dir = sys.argv[2]       
        main(data_dir, pcc_dir, 'aliamir')
     