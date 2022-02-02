import os, re


data_dir = 'pcc/output'
all = os.listdir(data_dir)
c = 0

for file in all:
    with open(data_dir + '/' + file) as f:
        content = f.readlines()
        text = ' '.join(content[:int(len(content) / 2) - 1])
        last_edu = re.findall('\\d+', content[-2])[-1]
        
        if len(text.split()) != int(last_edu) + 1:
            c+=1
            print('>>>>>>>>>>>>>>>>>>>>>>>>>>> warning', len(text.split()), int(last_edu), file)
            
print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", str(c))