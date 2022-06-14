import re
import json
import os
import stanza
import sys
import glob
import html


class Node:
    def __init__(self, right, left, node_id='-1', is_leaf=False, is_nucleus=False, rel='', root=False, multinuc='p', leaf_range="", range=None, parent=None, is_multi=False):
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
        self.parent = parent
        self.range = range
        self.is_multi = is_multi


def sort_children(tree):
    if tree is None:
        return ''

    if (tree.leaf_range is not None) and (len(tree.leaf_range) > 0):
        tree.range = tree.leaf_range.split()
        tree.range[0] = int(tree.range[0])
        tree.range[1] = int(tree.range[1])

    if len(tree.children) == 0:
        return tree.leaf_range
    
    ranges = []
    if tree.range is not None:
        ranges.append(tree.range)

    # if len(tree.children) == 1:
    #     tree.leaf_range = sort_children(tree.children[0])
    #     return tree.leaf_range
    
    for child in tree.children:
        sort_children(child)
        ranges.append(child.range)
    
    tree.children.sort(key=lambda x: int(x.range[0]))
    ranges.sort(key=lambda x: x[0])
    tree.range = [ranges[0][0], ranges[-1][1]]

    if (tree.leaf_range is None) or (len(tree.leaf_range) == 0):
        tree.leaf_range = str(tree.children[0].range[0]) + ' ' + str(tree.children[-1].range[1])
    return tree.leaf_range 


def binarize(span_node):
    if len(span_node.children) == 0:
        return
    if len(span_node.children) == 1:
        span_node.left = span_node.children[0]
        binarize(span_node.left)
        return 
    if len(span_node.children) == 2:
        if not span_node.is_leaf:
            span_node.left = span_node.children[0]
            binarize(span_node.left)
            span_node.right = span_node.children[1]
            binarize(span_node.right)
            return
        else:
            current_node = span_node
            current_node.is_leaf = False

            [child1, child2] = span_node.children
            duplicate = Node(None, None, node_id= span_node.node_id, rel='span', is_leaf = True, 
                leaf_range = span_node.leaf_range, is_nucleus=True, root=False, 
                multinuc='l', parent = current_node, is_multi = current_node.is_multi )

            child1.parent = duplicate
            child1.multinuc = 'r'
            duplicate.children = [child1]
            
            current_node.children = [duplicate, child2]
            current_node.leaf_range = f'{span_node.range[0]} {span_node.range[1]}'
            child2.parent = current_node
            current_node.node_id = -1

            sort_children(current_node)
            binarize(current_node)

            return
            

    # handle 3 or more childern
    new_nodes = []
    
    if span_node.children[0].rel != span_node.children[1].rel:
        intermediate_node = Node(None, None, node_id='-1', rel='span')
        intermediate_node.children = span_node.children[1:]
        intermediate_node.is_multi = span_node.is_multi
        intermediate_node.is_nucleus = True
        intermediate_node.parent = span_node.parent
        intermediate_node.range = span_node.range
        span_node.is_multi = False
        new_nodes = [span_node.children[0], intermediate_node]
    else:
        intermediate_node = Node(None, None, node_id='-1', rel='span')
        intermediate_node.children = span_node.children[0:-1]
        intermediate_node.is_multi = span_node.is_multi
        intermediate_node.is_nucleus = True
        intermediate_node.parent = span_node.parent
        intermediate_node.range = span_node.range
        span_node.is_multi = False
        new_nodes = [intermediate_node, span_node.children[-1]]
    
    (span_node.left, span_node.right) = (new_nodes[0], new_nodes[1])
    if (int(span_node.left.node_id) < 0 and span_node.left.children[0].rel == span_node.right.rel or 
        int(span_node.right.node_id) < 0 and span_node.right.children[0].rel == span_node.left.rel):
        # three multi nodes with the same multinuc relation type
        span_node.is_multi = True
        span_node.is_nucleus = True
        span_node.multinuc = 'c'
        # span_node.parent = span_node.parent
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
                span_node.right.children[0].multinuc = 'r'
                span_node.right.children[1].multinuc = 'r'

    binarize(span_node.left)
    binarize(span_node.right)
    sort_children(span_node)


def get_index_in_sent(my_list, word):
    for index, item in enumerate(my_list):
        if item.text == word:
            return index



def xml2tree(fname, nlp):

    kkk = 0
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


    seg_name =  fname.split('.')[0]
    seg_fname = f'{seg_name}.segment'
    segs = dict({})
    with open(seg_fname) as f:
        seg_content = f.readlines()  
    for line in seg_content:
        id, content = line.split('\t')
        segs[id.strip()] = content.strip()                  

    for node in nodes:
        idx = re.findall('id="\\d+"', node)[0]
        idx = re.findall('\\d+', idx)[0]

        if 'multinuc' in node:
            node_dict[idx].is_multi = True

        # skip rootre.findall('id="\\d+"', node)[0]
        if 'parent' not in node:
            node_dict[idx].root = True
            root_ind = idx
            pass
        else:
            # find relation name
            parent_id = re.findall('parent="\\d+"', node)[0]
            parent_id = re.findall('\\d+', parent_id)[0]
            relname = re.findall('relname="[\w+-?]+"', node)[0]
            relname = relname[9:len(relname) - 1]
            node_dict[idx].rel = relname
            
            if idx in leaf_idx:
                node_dict[idx].is_leaf = True
                for ln in leaf_nodes:
                    if 'segment id="' + idx + '"' in ln:
                        kkk += len(segs[idx].split())
                        node_dict[idx].word_count = len(segs[idx].split())

            # node_dict[idx].multinuc = 'r'
            # find the nuclearity label
            if 'type' in node: 
                nuc = re.findall('type="\\w+"', node)[0]
                nuc = nuc[6: len(nuc) - 1]
            else:
                nuc = relname


            rstext = ' '.join(nodes)

            if 'multinuc' in nuc or relname == 'span':
                node_dict[idx].is_nucleus = True
            elif f'parent="{parent_id}"' in rstext:
                node_dict[parent_id].is_nucleus = True
                

            # # TODO: This method of nuclearity assignment only works for RST-DT. It should be changed for German. 
            # if node_dict[idx].is_leaf and nuc != 'span' :
            #     if 'type="multinuc"' in node_dict[parent_id].node_text:
            #         node_dict[idx].multinuc = 'c'
            #     else:
            #         if int(parent_id) > int(idx):
            #             node_dict[idx].multinuc = 'r'
            #         else:
            #             node_dict[idx].multinuc = 'l'
            # elif node_dict[idx].is_leaf and nuc == 'span':
            #     if 'type="multinuc"' in node_dict[parent_id].node_text:
            #         node_dict[idx].multinuc = 'c'
            #     else:
            #         if int(parent_id) < int(idx):
            #             node_dict[idx].multinuc = 'r'
            #         else:
            #             node_dict[idx].multinuc = 'l'
            # # elif  node_dict[idx].is_leaf and nuc == 'span':
            # elif not node_dict[idx].is_leaf:
            #     if nuc != 'multinuc':
            #         if 'type="multinuc"' in node_dict[parent_id].node_text:
            #             node_dict[idx].multinuc = 'c'
                    # else:
                    #     if int(parent_id) > int(idx):
                    #         node_dict[idx].multinuc = 'r'
                    #     else:
                    #         node_dict[idx].multinuc = 'l'
            #     else:

            #         if int(parent_id) > int(idx):
            #             node_dict[idx].multinuc = 'r'
            #         else:
          

    counter = 0
    for lidx in leaf_idx:
        node_dict[lidx].leaf_range = str(counter) + " " + str(counter + node_dict[lidx].word_count - 1)
        counter += node_dict[lidx].word_count
    
    for node in node_dict:
        if not node_dict[node].root:
            parent_id = re.findall('parent="\\d+"', node_dict[node].node_text)[0]
            parent_id = re.findall('\\d+', parent_id)[0]
            node_dict[parent_id].children.append(node_dict[node])
            node_dict[node].parent = node_dict[parent_id]

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

def find_node_by_leaf_range_start (tree, start):
    if tree is None:
        return None
    
    for child in tree.children:
        result = find_node_by_leaf_range_start(child, start)
        if result is not None:
            return result
    result = find_node_by_leaf_range_start(tree.left, start)
    if result is not None:
            return result
    reuslt = find_node_by_leaf_range_start(tree.right, start)
    if result is not None:
            return result
    
    if tree.leaf_range is not None and tree.leaf_range.find(str(start)) == 0:
        return tree

    return None

def find_node_by_id (tree, id):
    if tree is None:
        return None
    if int(tree.node_id) == int(id):
        return tree
    
    for child in tree.children:
        result = find_node_by_id(child, id)
        if result is not None:
            return result
    result = find_node_by_id(tree.left, id)
    if result is not None:
            return result
    result = find_node_by_id(tree.right, id)
    if result is not None:
            return result

    return None



def rebuild_tree(tree_node):
    if tree_node is None:
        return
    new_node = Node(None, None, node_id=tree_node.node_id)

    # multinuc nodes
    if tree_node.left is not None and tree_node.right is not None and tree_node.is_multi:
        new_node.rel = rel_dict[tree_node.right.rel]
        new_node.multinuc = 'c'
        new_node.is_multi = True
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
                new_node.is_nucleus = tree_node.right.is_nucleus
                tree_node.right.rel = 'span'
            else:
                new_node.rel = rel_dict[tree_node.left.rel]
                new_node.multinuc = 'r'
                new_node.is_nucleus = tree_node.left.is_nucleus
                tree_node.left.rel = 'span'
                

        elif tree_node.is_leaf and tree_node.left is not None and tree_node.left.is_leaf:
            new_node.rel = rel_dict[tree_node.left.rel] if rel_dict[tree_node.left.rel] != 'span' else rel_dict[tree_node.rel]
            new_node.multinuc = tree_node.left.multinuc
            new_node.is_nucleus = tree_node.is_nucleus

            child1 = Node(left=None, right=None, node_id=tree_node.node_id, rel='leaf', is_leaf=True, multinuc='t', leaf_range=tree_node.leaf_range, range = tree_node.range)
            child2 = Node(left=None, right=None, node_id=tree_node.left.node_id, rel='leaf', is_leaf=True, multinuc='t', leaf_range=tree_node.left.leaf_range, range = tree_node.left.range)
            if tree_node.range[0] < tree_node.left.range[0] or tree_node.range[1] < tree_node.left.range[1]:
                tree_node.left = child1
                tree_node.right = child2
            else:
                tree_node.left = child2
                tree_node.right = child1

        elif tree_node.is_leaf and tree_node.left is not None and not(tree_node.left.rel == tree_node.rel == 'span'):
            new_node.rel = rel_dict[tree_node.left.rel] if rel_dict[tree_node.left.rel] != 'span' else rel_dict[tree_node.rel]
            new_node.multinuc = tree_node.multinuc
            new_node.is_nucleus = tree_node.is_nucleus
            child1 = Node(left=None, right=None, node_id=tree_node.node_id, rel='leaf', is_leaf=True, multinuc='t', leaf_range=tree_node.leaf_range, range = tree_node.range)
            child2 = Node(left=tree_node.left.left, right=tree_node.left.right, node_id=tree_node.left.node_id, rel='span', leaf_range=tree_node.left.leaf_range, is_leaf=tree_node.left.is_leaf, multinuc=tree_node.left.multinuc, range = tree_node.left.range, is_multi = tree_node.left.is_multi)
            # leaf - span
            if tree_node.range[0] < tree_node.left.range[0] or tree_node.range[1] < tree_node.left.range[1]:
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
        new_node.is_nucleus = tree_node.is_nucleus
        new_node.leaf_range = tree_node.leaf_range

    if tree_node.left is None and tree_node.rel != 'leaf':
        new_node.rel = 'leaf'
        new_node.multinuc = 't'
        new_node.is_nucleus = tree_node.is_nucleus
        new_node.leaf_range = tree_node.leaf_range

    if new_node.rel is None or new_node.rel == '':
        return rebuild_tree(tree_node.left)

    new_node.left = rebuild_tree(tree_node.left)
    new_node.right = rebuild_tree(tree_node.right)
    new_node.node_id = tree_node.node_id
    new_node.range = tree_node.range
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
        print(f'Unary node {tree.node_id}')
        tree.leaf_range = rearange_children(tree.left)
        return tree.leaf_range
    if tree.left is None:
        print(f'Unary node {tree.node_id}')
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

def assign_nuclearity(tree):
    if tree is None:
        return

    if tree.left is not None and tree.right is not None:
        if tree.is_multi and not tree.root and tree.parent is not None:
            if tree.parent.range[0] < tree.range[0]:
                tree.multinuc = 'l'
            else:
                tree.multinuc = 'r'
        else:
            if tree.left.is_nucleus:
                    tree.multinuc = 'l'
            elif tree.right.is_nucleus:
                    tree.multinuc = 'r'

    elif tree.left is not None:
        tree_start, tree_end = [int(item) for item in tree.leaf_range.split()]
        child_start, child_end = [int(item) for item in tree.left.leaf_range.split()]
        
        if tree.is_nucleus:

            if child_end == tree_end:
                if child_start < tree_start:
                    tree.multinuc = 'r'
                else:
                    tree.multinuc = 'l'
            
            elif tree_start == child_start:
                if child_end < tree_end:
                    tree.multinuc = 'r'
                else:
                    tree.multinuc = 'l'
            elif tree_end < child_start:
                tree.multinuc = 'l'
           
            elif tree_start == child_end + 1:
                tree.multinuc = 'r'
            
        elif tree.left.is_nucleus:
            
            if child_end == tree_end:
                if child_start < tree_start:
                    tree.multinuc = 'l'
                else:
                    tree.multinuc = 'r'
            elif tree_end < child_start:
                tree.multinuc = 'l'
                
            elif tree_start == child_start:
                if child_end < tree_end:
                    tree.multinuc = 'l'
                else:
                    tree.multinuc = 'r'
            elif tree_start == child_end + 1:
                tree.multinuc = 'r'
            
    else:
        parent_start, parent_end = [int(item) for item in tree.parent.leaf_range.split()]
        child_start, child_end = [int(item) for item in tree.leaf_range.split()]
        if tree.parent.is_nucleus:
            
            if child_end == parent_end:
                if child_start < parent_start:
                    tree.multinuc = 'r'
                else:
                    tree.multinuc = 'l'
            
            elif parent_start == child_start:
                if child_end < parent_end:
                    tree.multinuc = 'r'
                else:
                    tree.multinuc = 'l'
            elif parent_end < child_start:
                tree.multinuc = 'l'
           
            elif parent_start == child_end + 1:
                tree.multinuc = 'r'
            
        elif tree.is_nucleus:
            if child_end == parent_end:
                if child_start < parent_start:
                    tree.multinuc = 'l'
                else:
                    tree.multinuc = 'r'
            elif parent_end < child_start:
                tree.multinuc = 'l'
                
            elif parent_start == child_start:
                if child_end < parent_end:
                    tree.multinuc = 'l'
                else:
                    tree.multinuc = 'r'
            elif parent_start == child_end + 1:
                tree.multinuc = 'r'
        else:
            print('Warning: You are missing something.')
            
    
    
    assign_nuclearity(tree.left)
    assign_nuclearity(tree.right)
    return


def verify_nodes(new_tree, node_dict, title):
    print (f' ------ Verifying leaves after {title}')
    missing_nodes = 0
    for key in node_dict:
        if node_dict[key].is_leaf and find_node_by_id(new_tree, key) is None:
            missing_nodes += 1
            print(f'The leaves {key} is missing')
    if missing_nodes == 0:
        print('No leaf is mssing')
    
def rst_tree_builder(nlp, txt_filename, rst_filename):
    print(txt_filename)
    with open(txt_filename) as f:
        text = f.read()
    out_node, node_dict = xml2tree(rst_filename, nlp)
    sort_children(out_node)
    verify_nodes(out_node, node_dict, 'Sort Children')

    binarize(out_node)
    verify_nodes(out_node, node_dict, 'Binarize')
    
    assign_nuclearity(out_node)

    tree_rebuilt = rebuild_tree(out_node)
    verify_nodes(tree_rebuilt, node_dict, 'Rebuild Tree')

    rearange_children(tree_rebuilt)
    verify_nodes(tree_rebuilt, node_dict, 'Rearrange children')
    
    # print(tree_rebuilt)

    return preorder_str(tree_rebuilt)

def prepare_de_data(nlp, data_dir, fn):
    with open(f'{data_dir}{fn}.conll') as f:
        text = f.read()
        text = text.replace('\n\n', '\n')
        text = text.split('\n')[:-1]
    out_file = open(f'{data_dir}/output/{fn}.prep', 'w')
    
    
    c = 0
    for i in range(len(text)):
        if text[i]:
            tokens = text[i].split('\t')
            word = tokens[1]
            pos = tokens[4]
            out_file.write(word + "_" + pos + " ")
        else:
            c += 1
            out_file.write('\n')
            continue
        
    for i in range(c):
        out_file.write('Tree\n')
    rst_tree = rst_tree_builder(nlp, f'{data_dir}/{fn}.txt', f'{data_dir}/{fn}.rs3')
    rst_tree = re.sub('\s+', ' ', rst_tree)
    out_file.write(rst_tree.strip())
    out_file.write('\n\n')
    out_file.close()

def reshape_output(data_dir, fname):
    fn = fname.split('.seg')[0]
    with open(f'{data_dir}/{fname}') as f:
        text = f.read()
    text = re.sub('\\(HSF|\\(HS', '\n', text)
    text = re.sub('-OP- ! -CP-|\\(OBJ|\\(SUB', '', text)
    text = re.sub('\\)', '', text)
    text = re.sub('^ ', '', text)
    text = re.sub('\\n ', '\n', text)
    text = re.sub('\\n{2,}', '\n', text)
    text = re.sub(' {2,}', ' ', text)

    text = text.strip()
    with open(f'{data_dir}/{fn}.txt', 'w') as f:
        f.write(text)
    
    return text

def main(data_dir):
    nlp = stanza.Pipeline('de', tokenize_language='de')
    txt_files = glob.glob(data_dir + "/*.txt")
    files = glob.glob(data_dir + "/*.rs3")
    fns = [fn.split('/')[-1].split('.')[0] for fn in txt_files]
    # assert len(txt_files) == len(files)
    for fn in fns:
        if '12666' in fn:
            print('d')
        # if not os.path.exists(f'{data_dir}output/{fn}.prep'):
        prepare_de_data(nlp, f'{data_dir}',  f'{fn}',)


if __name__ == '__main__':
    data_dir = 'sara/'
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    if not os.path.isdir(f'{data_dir}/output'):
        os.mkdir(f'{data_dir}/output')
    main(data_dir)
    