import os, sys, glob

def read_conll_file(filename):
	with open(filename) as f:
		content = f.readlines()

	word_pos_set = []
	for c in content:
		conll = c.split('\t')
		word_pos = [conll[2], conll[5]]
		word_pos_set.append(word_pos)
	return word_pos_set


def read_txt_files(filename):
	with open(filename) as f:
		text = f.read()
		words = text.split()
	return words


def prepare_dis_tree(filename):
	with open(filename) as f:
		text = f.read()
		words = text.split()
	return words

if __name__ == '__main__':
	if(len(sys.argv)) > 1:
		corpus_dir = sys.argv[1]
		file_list = glob.glob(corpus_dir + "*.txt")

	print(file_list)
	print(read_conll_file('derst/maz-00001.conll'))
	print(read_txt_files('derst/maz-00001.txt'))