import re
import json
import os


def js_r(filename):
    with open(filename) as f_in:
        return json.load(f_in)


class Node:
    def __init__(self, right, left, node_id, is_leaf=False, is_nucleus=False, rel='', root=False, multinuc='l'):
        self.is_leaf = is_leaf
        self.is_nucleus = is_nucleus
        self.right = right
        self.node_id = node_id
        self.left = left
        self.rel = rel
        self.root = root
        self.multinuc = multinuc

# def __repr__(self):
# 	if self.left.rel and self.right is not None:
# 		return self.left.rel + self.right.rel
# 	if self.left.rel:
# 		return self.left.rel
# 	return ''

def xml2tree(fname):
    with open(fname) as f:
        content = f.read()
    nodes = re.findall('id="\\d+.*"', content)
    leaf_nodes = re.findall('<segment id="\\d+"', content)
    leaf_idx = []
    for ln in leaf_nodes:
        idx = re.findall('\\d+', ln)[0]
        leaf_idx.append(idx)

    node_dict = dict({})
    for nd in nodes:
        node_id = re.findall('id="\\d+"', nd)[0]
        node_id = re.findall('\\d+', node_id)[0]
        n = Node(right=None, left=None, node_id=node_id)
        node_dict[node_id] = n

    for node in nodes:
        if 'parent' not in node:
            pass
        else:
            idx = re.findall('id="\\d+"', node)[0]
            idx = re.findall('\\d+', idx)[0]
            parent_id = re.findall('parent="\\d+"', node)[0]
            parent_id = re.findall('\\d+', parent_id)[0]
            relname = re.findall('relname="[\w+-?]+"', node)[0]
            relname = relname[9:len(relname) - 1]
            node_dict[idx].rel = relname

            if relname != 'span':
                node_dict[idx].is_nucleus = True

            if idx in leaf_idx:
                node_dict[idx].is_leaf = True
            else:
                nuc = re.findall('type="\\w+"', node)[0]
                nuc = nuc[6: len(nuc) - 1]

                if node_dict[idx].is_leaf:
                    node_dict[idx].multinuc = 't'
                elif nuc == 'span':
                    node_dict[idx].multinuc = 'l'
                else:
                    node_dict[idx].multinuc = 'c'


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


rel_dict = js_r('relname_mapping.json')
out_node, leaf_idx = xml2tree('wsj_input_rs3.xml')


def old_print_preoder(tree_node):
    if tree_node is None:
        return
    # if tree_node.multinuc:
    #     rel = rel_dict[tree_node.right.rel]
    #     print("( " + rel + " c")
    #
    # if tree_node.rel == 'span':
    #     if tree_node.left is not None and tree_node.right is not None and (
    #             tree_node.right.rel == 'span' or tree_node.left.rel == 'span'):
    #         if tree_node.right.rel != 'span':
    #             print('( ' + rel_dict[tree_node.right.rel] + ' l ')
    #         else:
    #             print('( ' + rel_dict[tree_node.left.rel] + ' l ')
    #     if tree_node.is_leaf and tree_node.left is not None and tree_node.right is None and tree_node.left.rel != 'span':
    #         print('( ' + rel_dict[tree_node.left.rel] + ' l ')
    #
    # if tree_node.is_leaf:
    #     print('( leaf t ')

    print_preoder(tree_node.left)
    print_preoder(tree_node.right)
    print(')')


def rebuild_tree(tree_node):
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

    new_node.left = rebuild_tree(tree_node.left)
    new_node.right = rebuild_tree(tree_node.right)
    return new_node



def preorder_str(tree_node):
    if tree_node is None:
        return ''
    sm = '( '
    if tree_node.rel =='leaf':
        sm += tree_node.rel + ' ' + tree_node.multinuc + " "
    else:
        sm += tree_node.rel + ' ' + tree_node.multinuc + " "
    sm += preorder_str(tree_node.left)
    sm += preorder_str(tree_node.right)
    sm += ')'
    return sm


def print_preoder(tree_node):
    if tree_node is None:
        return
    print('(')
    print(tree_node.rel + ' ' +  tree_node.multinuc )
    print_preoder(tree_node.left)
    print_preoder(tree_node.right)
    print(')')

if __name__ == '__main__':
    # print_preoder(out_node)
    queue = [out_node]

    s = ""
    # while len(queue) > 0:
    # 	node = queue.pop(0)
    # 	if node.left is not None:
    # 		queue.append(node.left)
    # 	if node.right is not None:
    # 		queue.append(node.right)
    # if node.multinuc:
    # 	rel = rel_dict[node.right.rel]
    # 	s += "(" + rel + " c\n"
    # if node.node_id in leaf_idx:
    # 	s += "(leaf t\n"
    # if node.rel == 'span' and node.left is not None and node.right is not None and (node.right.rel == 'span' or node.left.rel == 'span'):
    # 	if node.right.rel != 'span':
    # 		s += '(' + rel_dict[node.right.rel]
    # 	else:
    # 		s += '(' + rel_dict[node.left.rel]

    # new_tree = Node(None, None, 0)

    # new_tree = Node(None, None, 0)
    # while len(queue) > 0:
    #     node = queue.pop(0)
    #     if node.left is not None:
    #         queue.append(node.left)
    #     if node.right is not None:
    #         queue.append(node.right)
    #     if node.multinuc:
    #         rel = rel_dict[node.right.rel]
    #         new_tree.rel = rel
    #     if node.node_id in leaf_idx:
    #         new_tree.rel = 'leaf'
    #     if node.rel == 'span' and node.left is not None and node.right is not None and (
    #             node.right.rel == 'span' or node.left.rel == 'span'):
    #         if node.right.rel != 'span':
    #             new_tree.rel = rel_dict[node.right.rel]
    #         else:
    #             new_tree.rel += rel_dict[node.left.rel]


    nn = rebuild_tree(out_node)
    print(preorder_str(nn))