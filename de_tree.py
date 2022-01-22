import re
import json
import os
import stanza
import sys
import glob


class Node:
    def __init__(self, right, left, node_id='-1', is_leaf=False, is_nucleus=False, rel='', root=False, multinuc='p', leaf_range=""):
        self.is_leaf = is_leaf
        self.is_nucleus = is_nucleus
        self.right = right
        self.node_id = node_id
        self.left = left
        self.rel = rel
        self.root = root
        self.multinuc = multinuc
        self.leaf_range = leaf_range
        self.node_text = ''
        self.parent_text = ''
        self.word_count = 0
        self.children = []


def binarize(span_node):
    if len(span_node.children) == 0:
        return
    if len(span_node.children) == 1:
        span_node.left = span_node.children[0]
        binarize(span_node.left)
        return 
    if len(span_node.children) == 2:
        span_node.left = span_node.children[0]
        binarize(span_node.left)
        span_node.right = span_node.children[1]
        binarize(span_node.right)
        return

    # handle 3 or more childern
    new_nodes = []
    
    if span_node.children[0].rel != span_node.children[1].rel:
        intermediate_node = Node(None, None, node_id='-1', rel='span')
        intermediate_node.children = span_node.children[1:]
        new_nodes = [span_node.children[0], intermediate_node]
    else:
        intermediate_node = Node(None, None, node_id='-1', rel='span')
        intermediate_node.children = span_node.children[0:-1]
        new_nodes = [intermediate_node, span_node.children[-1]]
    
    (span_node.left, span_node.right) = (new_nodes[0], new_nodes[1])
    if (int(span_node.left.node_id) < 0 and span_node.left.children[0].rel == span_node.right.rel or 
        int(span_node.right.node_id) < 0 and span_node.right.children[0].rel == span_node.left.rel):
        # three multi nodes with the same multinuc relation type
        span_node.left.multinuc, span_node.right.multinuc = 'c','c'
    else:
        
        if int(span_node.left.node_id) > 0:
            if span_node.left.rel == 'span':
                raise Exception(f'Unacceptable schema; node_id:{span_node.node_id}')
            span_node.left.multinuc = 'r'
            span_node.right.multinuc = 'r'
            # set nuclearity of the intermediate node
            if span_node.right.children[0].rel != span_node.right.children[1].rel:
                if span_node.right.children[1].rel == 'span':
                    raise Exception(f'Unacceptable schema in multinuc node; node_id:{span_node.node_id}')
                span_node.right.children[0].multinuc = 'l'
                span_node.right.children[1].multinuc = 'l'

        else: # int(span_node.right.node_id) > 0:
            if span_node.right.rel == 'span':
                raise Exception(f'Unacceptable schema; node_id:{span_node.node_id}')
            span_node.left.multinuc = 'l'
            span_node.right.multinuc = 'l'
            if span_node.left.children[0].rel != span_node.left.children[1].rel:
                if span_node.left.children[0].rel == 'span':
                    raise Exception(f'Unacceptable schema in multinuc node; node_id:{span_node.node_id}')
                span_node.right.children[0].multinuc = 'l'
                span_node.right.children[1].multinuc = 'l'

    binarize(span_node.left)
    binarize(span_node.right)


def get_index_in_sent(my_list, word):
    for index, item in enumerate(my_list):
        if item.text == word:
            return index

 
def xml2tree(fname, nlp):
    with open(fname) as f:
        content = f.read().replace('&lt;P&gt;', '')

    node_dict = dict({})
    leaf_idx = []
    c = 0
    nodes = re.findall('id="\\d+.*"', content)
    leaf_nodes = re.findall('<segment id="\\d+".*', content)

    # save leaf node indices here
    for ln in leaf_nodes:
        idx = re.findall('\\d+', ln)[0]
        leaf_idx.append(idx)

    # create nodes to be filled later
    node_dict = dict({})
    for nd in nodes:
        node_id = re.findall('id="\\d+"', nd)[0]
        node_id = re.findall('\\d+', node_id)[0]
        n = Node(right=None, left=None, node_id=node_id)
        node_dict[node_id] = n
    for node in nodes:
        idx = re.findall('id="\\d+"', node)[0]
        idx = re.findall('\\d+', idx)[0]
        node_dict[idx].node_text = node
    
    root_ind = -1

    for node in nodes:
        # skip rootre.findall('id="\\d+"', node)[0]
        if 'parent' not in node:
            idx = re.findall('id="\\d+"', node)[0]
            idx = re.findall('\\d+', idx)[0]
            node_dict[idx].root = True
            root_ind = idx
            pass
        else:
            # find relation name
            idx = re.findall('id="\\d+"', node)[0]
            idx = re.findall('\\d+', idx)[0]
            parent_id = re.findall('parent="\\d+"', node)[0]
            parent_id = re.findall('\\d+', parent_id)[0]
            relname = re.findall('relname="[\w+-?]+"', node)[0]
            relname = relname[9:len(relname) - 1]
            node_dict[idx].rel = relname
            
            if idx in leaf_idx:
                node_dict[idx].is_leaf = True
                for ln in leaf_nodes:
                    if 'segment id="' + idx + '"' in ln:
                        ln_text = re.sub(r'<.*>(.*)<\/\w+>', '\\1', ln)
                        ln_text_processed = nlp(ln_text)
                        count_all_sents_words = 0
                        for sent in ln_text_processed.sentences:
                            count_all_sents_words += len(sent.words)
                        
                        node_dict[idx].word_count = count_all_sents_words



            # find the nuclearity label
            if 'type' in node:
                nuc = re.findall('type="\\w+"', node)[0]
                nuc = nuc[6: len(nuc) - 1]
            else:
                nuc = relname

            if 'multinuc' in nuc or relname == 'span':
                node_dict[idx].is_nucleus = True


            # TODO: This method of nuclearity assignment only works for RST-DT. It should be changed for German. 
            if node_dict[idx].is_leaf and nuc != 'span' :
                if 'type="multinuc"' in node_dict[parent_id].node_text:
                    node_dict[idx].multinuc = 'c'
                else:
                    if parent_id > idx:
                        node_dict[idx].multinuc = 'r'
                    else:
                        node_dict[idx].multinuc = 'l'
            elif node_dict[idx].is_leaf and nuc == 'span':
                if 'type="multinuc"' in node_dict[parent_id].node_text:
                    node_dict[idx].multinuc = 'c'
                else:
                    if parent_id < idx:
                        node_dict[idx].multinuc = 'r'
                    else:
                        node_dict[idx].multinuc = 'l'
            # elif  node_dict[idx].is_leaf and nuc == 'span':
            elif not node_dict[idx].is_leaf:
                if nuc != 'multinuc':
                    if 'type="multinuc"' in node_dict[parent_id].node_text:
                        node_dict[idx].multinuc = 'c'
                    else:
                        if parent_id > idx:
                            node_dict[idx].multinuc = 'r'
                        else:
                            node_dict[idx].multinuc = 'l'
                else:

                    if parent_id > idx:
                        node_dict[idx].multinuc = 'r'
                    else:
                        node_dict[idx].multinuc = 'l'
            else:
                print('exception')
            # Assign left and right nodes


    counter = 0
    for lidx in leaf_idx:
        node_dict[lidx].leaf_range = str(counter) + " " + str(counter + node_dict[lidx].word_count - 1)
        counter += node_dict[lidx].word_count
    
    for node in node_dict:
        if not node_dict[node].root:
            parent_id = re.findall('parent="\\d+"', node_dict[node].node_text)[0]
            parent_id = re.findall('\\d+', parent_id)[0]
            node_dict[parent_id].children.append(node_dict[node])

            # Since trees are not binarized, this kind of assignment does not work. Trees should be binarized 
            # using binarize function.
            # if node_dict[parent_id].left is None:
                # node_dict[parent_id].left = node_dict[idx]   
            # elif idx < node_dict[parent_id].left.node_id:
            #     tmp = node_dict[parent_id].left
            #     node_dict[parent_id].left = node_dict[idx]
            #     node_dict[parent_id].right = tmp
            # else:
            #     node_dict[parent_id].right = node_dict[idx]


    return node_dict[root_ind], node_dict

def rebuild_tree(tree_node):
    if tree_node is None:
        return
    new_node = Node(None, None, '0')

    # multinuc nodes
    if tree_node.left is not None and tree_node.right is not None and tree_node.right.multinuc == 'c':
        new_node.rel = rel_dict[tree_node.right.rel]
        new_node.multinuc = 'c'
        tree_node.left.rel = 'span'
        tree_node.right.rel = 'span'
    # mononuc nodes
    elif tree_node.rel == 'span':
        # span-span mononuc
        if tree_node.left is not None and tree_node.right is not None and (
                tree_node.right.rel == 'span' or tree_node.left.rel == 'span'):
            if tree_node.right.rel != 'span':
                new_node.rel = rel_dict[tree_node.right.rel]
                new_node.multinuc = 'l'
                tree_node.right.rel = 'span'
            else:
                new_node.rel = rel_dict[tree_node.left.rel]
                new_node.multinuc = 'r'
                tree_node.left.rel = 'span'

        elif tree_node.is_leaf and tree_node.left is not None and tree_node.left.is_leaf:
            new_node.rel = rel_dict[tree_node.left.rel] if rel_dict[tree_node.left.rel] != 'span' else rel_dict[tree_node.rel]
            new_node.multinuc = tree_node.left.multinuc
            child1 = Node(left=None, right=None, node_id=tree_node.node_id, rel='leaf', is_leaf=True, multinuc='t', leaf_range=tree_node.leaf_range)
            child2 = Node(left=None, right=None, node_id=tree_node.left.node_id, rel='leaf', is_leaf=True, multinuc='t', leaf_range=tree_node.left.leaf_range)
            if tree_node.node_id < tree_node.left.node_id:
                tree_node.left = child1
                tree_node.right = child2
            else:
                tree_node.left = child2
                tree_node.right = child1

        elif tree_node.is_leaf and tree_node.left is not None and not(tree_node.left.rel == tree_node.rel == 'span'):
            new_node.rel = rel_dict[tree_node.left.rel] if rel_dict[tree_node.left.rel] != 'span' else rel_dict[tree_node.rel]
            new_node.multinuc = tree_node.left.multinuc
            child1 = Node(left=None, right=None, node_id=tree_node.node_id, rel='leaf', is_leaf=True, multinuc='t', leaf_range=tree_node.leaf_range)
            child2 = Node(left=tree_node.left.left, right=tree_node.left.right, node_id=tree_node.left.node_id, rel='span', leaf_range=tree_node.left.leaf_range, is_leaf=tree_node.left.is_leaf, multinuc=tree_node.left.multinuc)
            # leaf - span
            if tree_node.node_id < tree_node.left.node_id:
                tree_node.left = child1
                tree_node.right = child2
            # span - leaf
            else:
                tree_node.left = child2
                tree_node.right = child1
   
    else:
        # reached a leaf node
        new_node.rel = rel_dict[tree_node.rel]
        new_node.multinuc = tree_node.multinuc
        new_node.leaf_range = tree_node.leaf_range

    if tree_node.left is None and tree_node.rel != 'leaf':
        new_node.rel = 'leaf'
        new_node.multinuc = 't'
        new_node.leaf_range = tree_node.leaf_range

    if new_node.rel is None or new_node.rel == '':
        return rebuild_tree(tree_node.left)

    new_node.left = rebuild_tree(tree_node.left)
    new_node.right = rebuild_tree(tree_node.right)
    new_node.node_id = tree_node.node_id
    return new_node


def load_relation_mappings(filename):
    with open(filename) as f_in:
        return json.load(f_in)

rel_dict = load_relation_mappings('relname_mapping.json')

def preoder_print(tree_node):
    if tree_node is None:
        return
    print('(')
    print(tree_node.rel + ' ' + tree_node.multinuc)
    preoder_print(tree_node.left)
    preoder_print(tree_node.right)
    print(' )')

def preoder_write2file(tree_node, fp):
    if tree_node is None:
        return
    fp.write('( ')
    fp.write(tree_node.rel + ' ' + tree_node.multinuc)
    preoder_write2file(tree_node.left, fp)
    preoder_write2file(tree_node.right, fp)
    fp.write(')')

def preorder_str(tree_node):
    if tree_node is None:
        return ''
    sm = '( '
    if tree_node.rel == 'leaf':
        sm += tree_node.rel + ' ' + tree_node.multinuc + " " + tree_node.leaf_range
    else:
        sm += tree_node.rel + ' ' + tree_node.multinuc + " "
    sm += preorder_str(tree_node.left)
    sm += preorder_str(tree_node.right)
    sm += ' ) '
    return sm

def rearange_children(tree):
    if tree is None:
        return ''
    if tree.is_leaf or tree.rel == 'leaf':
        return tree.leaf_range
    
    if tree.right is None:
        tree.leaf_range = rearange_children(tree.left)
        return tree.leaf_range
    if tree.left is None:
        tree.leaf_range = rearange_children(tree.right)
        return tree.leaf_range
    
    left_range = rearange_children(tree.left)
    right_range = rearange_children(tree.right)
    left_range = left_range.split()
    right_range = right_range.split()
    
    if int(left_range[0]) > int(right_range[0]):
        (left_range, right_range) = (right_range, left_range)
        (tree.left, tree.right) = (tree.right, tree.left)
        for child in (tree.left, tree.right):
            if child.multinuc == 'l':
                child.multinuc = 'r'
            elif child.multinuc == 'r':
                child.multinuc = 'l'

    tree.leaf_range = left_range[0]+ ' ' + right_range[1]
    return tree.leaf_range 



def sort_children(tree):
    if tree is None:
        return ''
    if len(tree.children) == 0:
        return tree.leaf_range
    
    if len(tree.children) == 1:
        tree.leaf_range = sort_children(tree.children[0])
        return tree.leaf_range
    
    for child in tree.children:
        sort_children(child)
        child.range = child.leaf_range.split()
    
    tree.children.sort(key=lambda x: x.range[0])

    tree.leaf_range = tree.children[0].range[0]+ ' ' + tree.children[-1].range[1]
    return tree.leaf_range 

def assign_nuclearity(node, parent_node):

    if 'type' in node.node_text:
        nuc = re.findall('type="\\w+"', node.node_text)[0]
        nuc = nuc[6: len(nuc) - 1]
    else:
        nuc = node.rel
        
    if node.is_leaf :
        if 'type="multinuc"' in parent_node.node_text:
            node.multinuc = 'c'
        else:
            if parent_node.node_id > node.node_id:
                node.multinuc = 'r'
            else:
                node.multinuc = 'l'
    elif node.is_leaf and nuc == 'span':
        if 'type="multinuc"' in parent_node.node_text:
            node.multinuc = 'c'
        else:
            if parent_node.node_id < node.node_id:
                node.multinuc = 'r'
            else:
                node.multinuc = 'l'
    # elif  node_dict[idx].is_leaf and nuc == 'span':
    elif not node.is_leaf:
        if nuc != 'multinuc':
            if 'type="multinuc"' in parent_node.node_text:
                node.multinuc = 'c'
            else:
                if parent_node.node_id > node.node_id:
                    node.multinuc = 'r'
                else:
                    node.multinuc = 'l'
        else:

            if parent_node.node_id > node.node_id:
                node.multinuc = 'r'
            else:
                node.multinuc = 'l'
    else:
        print('exception')
    # Assign left and right nodes

    
def rst_tree_builder(nlp, txt_filename, rst_filename):
    print(txt_filename)
    with open(txt_filename) as f:
        text = f.read()
    # tokens = nlp(text)
    out_node, node_dict = xml2tree(rst_filename, nlp)
    binarize(out_node)
    tree_rebuilt = rebuild_tree(out_node)
    rearange_children(tree_rebuilt)
    for idx in node_dict:
        if not 'parent' in node_dict[idx].node_text:
            if node_dict[idx].node_id == '1':
                pass
                # print('Skipping Title!')
            elif node_dict[idx].root:
                pass
                # print('Skipping root!')
            else:
                raise Exception('Skipping unusual node! Investigate. ')
        else:
            parent_id = re.findall('parent="\\d+"', node_dict[idx].node_text)[0]
            parent_id = re.findall('\\d+', parent_id)[0]
            assign_nuclearity(node_dict[idx], node_dict[parent_id])
        
    return preorder_str(tree_rebuilt)

def prepare_de_data(nlp, data_dir, fn):
    with open(f'{data_dir}{fn}.txt') as f:
        text = f.read().split('\n')
    out_file = open(f'{data_dir}/output/{fn}.prep', 'w')
    
    for titem in text:
        titem_processed = nlp(titem.strip())
        for sent in titem_processed.sentences:
            for word in sent.words:
                out_file.write(word.text + "_" + word.xpos + " ")
        out_file.write('\n')
    rst_tree = rst_tree_builder(nlp, f'{data_dir}/{fn}.txt', f'{data_dir}/{fn}.rs3')
    out_file.write(rst_tree.strip())
    out_file.write('\n\n')
    out_file.close()


def main(data_dir):
    nlp = stanza.Pipeline('de', tokenize_language='de')
    txt_files = glob.glob(data_dir + "/*.txt")
    files = glob.glob(data_dir + "/*.rs3")
    fns = [fn.split('/')[-1].split('.')[0] for fn in txt_files]
    # assert len(txt_files) == len(files)
    for fn in fns:
        prepare_de_data(nlp, f'{data_dir}',  f'{fn}',)


if __name__ == '__main__':
    data_dir = 'pcc/'
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    if not os.path.isdir(f'{data_dir}/output'):
        os.mkdir(f'{data_dir}/output')
    main(data_dir)
    
    
    