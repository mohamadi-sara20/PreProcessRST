from cgi import test
from re import I
import sys
import os

def main(read_dir, write_dir, combo_name):
    content = ''
    conll = ''
    all_files = os.listdir(read_dir)
    print(all_files)
    for file in all_files:
        if file.endswith('.prep'):
            with open(f'{read_dir}/{file}') as f:
                text = f.read()
                content += text + '\n'
        if file.endswith('.conll'):
            with open(f'{read_dir}/{file}') as f:
                text = f.read()
                conll += text 
    with open(f'{write_dir}{combo_name}.pcc', 'w') as f:
        f.write(content)
    with open(f'{write_dir}{combo_name}.conll', 'w') as f:
        f.write(conll)
    

if __name__ == '__main__':
    pcc_dir = 'pcc/'
    train_dir = 'pcc/train'
    test_dir = 'pcc/test'
    dev_dir = 'pcc/dev'
    
    if len(sys.argv) > 1:
        train_dir = sys.argv[1]
        dev_dir = sys.argv[2]
        test_dir = sys.argv[3]
        pcc_dir = sys.argv[4]
        
    main(train_dir, pcc_dir, 'train')
    main(dev_dir, pcc_dir, 'dev')
    main(test_dir, pcc_dir, 'test')
    