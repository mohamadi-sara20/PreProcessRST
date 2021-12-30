import re
import json
import os
import stanza


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



def rebuild_tree_old(tree_node):
    if tree_node is None:
        return

    new_node = Node(None, None, 0)

    if tree_node.multinuc == 'c':
        new_node.rel = rel_dict[tree_node.right.rel]
        new_node.multinuc = 'c'

    if tree_node.rel == 'span':
        if tree_node.left is not None and tree_node.right is not None and (
                tree_node.right.rel == 'span' or tree_node.left.rel == 'span'):
            if tree_node.right.rel != 'span':
                new_node.rel = rel_dict[tree_node.right.rel]
                new_node.multinuc = 'l'
            else:
                new_node.rel = rel_dict[tree_node.left.rel]
                new_node.multinuc = 'l'
        if tree_node.is_leaf and tree_node.left is not None and tree_node.right is None and tree_node.left.rel != 'span':
            new_node.rel =  rel_dict[tree_node.left.rel]
            new_node.multinuc = 'l'

    if tree_node.is_leaf:
        new_node.rel = 'leaf'
        new_node.multinuc = 't'
        new_node.is_leaf = True

    if new_node.rel is None or new_node.rel == '':
        if(tree_node.right):
            print('!!!!!!!!! UNEXPECTED RIGHT NODE FOUND !!!!!!')
        return rebuild_tree(tree_node.left)

    new_node.left = rebuild_tree_old(tree_node.left)
    new_node.right = rebuild_tree_old(tree_node.right)
    return new_node



def get_index_in_sent(my_list, word):
    for index, item in enumerate(my_list):
        if item.text == word:
            return index


def xml2tree(fname):
    with open(fname) as f:
        content = f.read().replace('&lt;P&gt;', '')

    node_dict = dict({})
    leaf_idx = []

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

    for node in nodes:
        # skip root
        if 'parent' not in node:
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

            if idx in leaf_idx:
                pass
                # for ln in leaf_nodes: if 'segment id="' + idx + '"' in ln: ln_text = re.sub(r'<.*>(.*)<\/\w+>',
                # '\\1', ln) for i in range(len(tokens.sentences)): if i > 0: begin += len(tokens.sentences[
                # i-1].words) end += len(tokens.sentences[i-1].words) else: begin = 0 end = 0 if ln_text in
                # tokens.sentences[i].text: ln_text_processed = nlp(ln_text) if len(ln_text_processed.sentences) ==
                # 1: s = begin + ln_text_processed.sentences[0].words[0].id - 1 e = end +
                # ln_text_processed.sentences[0].words[-1].id - 1 node_dict[idx].leaf_range = str(s) + " " + str(e)
                # else: print('############### length greater than one: ' + str(len(ln_text_processed.sentences)) +
                # "########")

            # find the nuclearity label
            if 'type' in node:
                nuc = re.findall('type="\\w+"', node)[0]
                nuc = nuc[6: len(nuc) - 1]
            else:
                nuc = relname

            if 'multinuc' in nuc or relname == 'span':
                node_dict[idx].is_nucleus = True

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

            if node_dict[parent_id].left is None:
                node_dict[parent_id].left = node_dict[idx]
            elif idx < node_dict[parent_id].left.node_id:
                tmp = node_dict[parent_id].left
                node_dict[parent_id].left = node_dict[idx]
                node_dict[parent_id].right = tmp
            else:
                node_dict[parent_id].right = node_dict[idx]


    node_dict['1'].root = True
    return node_dict['1'], leaf_idx


def load_relation_mappings(filename):
    with open(filename) as f_in:
        return json.load(f_in)


def rebuild_tree(tree_node):
    if tree_node is None:
        return
    new_node = Node(None, None, '0')

    # multinuc nodes
    if tree_node.rel == 'span' and tree_node.left is not None and tree_node.right is not None and tree_node.right.multinuc == 'c':
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
            left_child = Node(left=None, right=None, node_id=tree_node.left.node_id, rel='leaf', is_leaf=True, multinuc='t', leaf_range=tree_node.left.leaf_range)
            right_child = Node(left=None, right=None, node_id=tree_node.node_id, rel='leaf', is_leaf=True, multinuc='t')
            if tree_node.node_id < tree_node.left.node_id:
                tree_node.left = right_child
                tree_node.right = left_child
            else:
                tree_node.left = left_child
                tree_node.right = right_child

        # leaf - span
        elif tree_node.is_leaf and tree_node.left is not None:

            new_node.rel = rel_dict[tree_node.left.rel] if rel_dict[tree_node.left.rel] != 'span' else rel_dict[tree_node.rel]
            new_node.multinuc = tree_node.left.multinuc
            left_child = Node(left=None, right=None, node_id=tree_node.node_id, rel='leaf', is_leaf=True, multinuc='t', leaf_range=tree_node.leaf_range)
            right_child = Node(left=tree_node.left.left, right=tree_node.left.right, node_id=tree_node.left.node_id, rel='span', is_leaf=tree_node.left.is_leaf, multinuc=tree_node.left.multinuc)
            if tree_node.node_id < tree_node.left.node_id:
                tree_node.left = left_child
                tree_node.right = right_child
            else:
                tree_node.left = right_child
                tree_node.right = left_child

        # span - leaf
        elif tree_node.left is not None and tree_node.left.is_leaf:
            new_node.rel = rel_dict[tree_node.left.left.rel] if rel_dict[tree_node.left.left.rel] != 'span' else rel_dict[
                tree_node.left.rel]
            new_node.multinuc = tree_node.left.left.multinuc
            right_child = Node(left=None, right=None, node_id=tree_node.left.node_id, rel='leaf', is_leaf=True, multinuc='t',
                              leaf_range=tree_node.left.leaf_range)
            left_child = Node(left=tree_node.left.left.left, right=tree_node.left.left.right, node_id=tree_node.left.left.node_id,
                               rel='span', is_leaf=tree_node.left.left.is_leaf, multinuc=tree_node.left.left.multinuc)
            if tree_node.left.node_id < tree_node.left.left.node_id:
                tree_node.left = right_child
                tree_node.right = left_child
            else:
                tree_node.left = left_child
                tree_node.right = right_child
        
        elif tree_node.left is not None and tree_node.left.is_leaf:
            new_node.rel = rel_dict[tree_node.right.rel]
            new_node.multinuc = 'c'
            tree_node.left = tree_node.left.left
            tree_node.right = tree_node.right.left
            
    else:
        new_node.rel = rel_dict[tree_node.rel]
        new_node.multinuc = tree_node.multinuc
        new_node.leaf_range = tree_node.leaf_range

    if tree_node.left is None and tree_node.rel != 'leaf':
        new_node.rel = 'leaf'
        new_node.multinuc = 't'
        new_node.leaf_range = tree_node.leaf_range

    if new_node.rel is None or new_node.rel == '':
        if tree_node.right:
             print('!!!!!!!!! UNEXPECTED RIGHT NODE FOUND !!!!!!')
        return rebuild_tree(tree_node.left)

    new_node.left = rebuild_tree(tree_node.left)
    new_node.right = rebuild_tree(tree_node.right)
    return new_node


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
    sm += ')'
    return sm


def pos_const_rst_builder(fname, outname):
    with open(fname) as f:
        text = f.read()

    out_file = open(outname, 'w')
    text_pos = ''
    # doc = nlp(text)
    # for sent in doc.sentences:
    #     for word in sent.words:
    #         out_file.write(word.text + "_" + word.xpos + " ")
    #     out_file.write('\n')
    #
    # for sent in doc.sentences:
    #     out_file.write(str(sent.constituency))
    #     out_file.write('\n')

    # out_file.close()


if __name__ == '__main__':
    # nlp = stanza.Pipeline('en')
    rel_dict = load_relation_mappings('relname_mapping.json')
    with open('wsj.txt') as f:
        text = f.read()

    # tokens = nlp(text)
    out_node, leaf_idx = xml2tree('wsj_input_rs3.xml')
    tree_rebuilt = rebuild_tree(out_node)
    # print(pos_const_rst_builder('wsj.txt', 'janc.txt'))
    