import os
import re
import sys


if __name__ == "__main__":
        print('====================== check conll =================')
        if len(sys.argv) > 1:
                data_dir = sys.argv[1]
                all = os.listdir(data_dir)
                for f in all:
                        if f.endswith('.segment'):
                                with open(data_dir + '/' + f) as g:
                                        content = g.read()
                                fname = f.split('.')[0]
                                with open(data_dir + '/' + fname+ '.conll') as g:
                                        conll = g.read()

                                content = re.sub('\\d+\t', '', content)
                                conll = re.sub('\n\n', '', conll)
                                if len(conll.split('\n')[:-1]) != len(content.split()):
                                        print('>>>>>>>>>>>>>>>>>>>>>>>' + fname + " " + str(len(conll.split('\n')[:-1])) + " " + str(len(content.split())))
                                        
                                        words = ''
                                        items = conll[:-1].split('\n')
                                        for item in items:
                                                tok = item.split('\t')[1]
                                                words += tok + ' '
                                                
                                                print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
                                                print(words == content)
                                                content = re.sub('\n', ' ', content)
                                                # splitC = set(content.split(words))
                                                # splitW = set(words.split(content))
                                                # diff = splitW.difference(splitC)
                                                # print(diff)
                                                print(words)
                                                print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
                                                print(content)
                                                print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
                                                
        else:
                print("Please specify a path to conll files!")