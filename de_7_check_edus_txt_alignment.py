import os, re, sys

if __name__ == '__main__':
    print('====================== checking edu txt alignments =================')
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
        all = os.listdir(data_dir)
        c = 0
        for file in all:
            if file.endswith('prep'):
                with open(data_dir + '/' + file) as f:
                    content = f.readlines()
                    text = ' '.join(content[:int(len(content) / 2) - 1])
                    last_edu = re.findall('\\d+', content[-2])[-1]
                    if len(text.split()) != int(last_edu) + 1:
                        c+=1
                        print('>>>>>>>>>>>>>>>>>>>>>>>>>>> warning', len(text.split()), int(last_edu), file)
                    else:
                        print("OK")
                print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", str(c))
        
    else:
        print('Please specify a path to tree files generated by de_tree!')