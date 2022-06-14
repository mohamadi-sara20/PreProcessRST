import re
import json
import os
import sys
import glob
import html

class Node:
    def __init__(self, id, start, end, left = None, right = None, rel = '', type = '', parent = None, is_nucleus=False, is_multinuc=False):
        self.start = start
        self.end = end
        self.is_leaf = (start == end)
        self.left = left
        self.right = right
        self.parent = parent
        self.rel = rel
        self.type = type
        self.id = id
        self.is_nucleus = is_nucleus
        self.is_multinuc = is_multinuc

def load_segments(file):
    tagged_tokens = []
    the_rest = ''

    while True:
        text = file.readline()
        if not text:
            break
        text = text.strip()
        
        # sentences
        if re.search(r'(<P>|<S>)$', text, re.IGNORECASE):
            # text = re.sub(r'(<P>|<S>)$', '', text)
            text = text.strip()
            tagged_tokens += text.split()
            continue
        
        # last line contains the segments
        the_rest += text
    
    # remove tags
    tokens = []
    for word in tagged_tokens:
        if word.find('_') >= 0:
            tokens.append(re.sub(r'_[^_]*$', '', word))
        elif word.find('-') >= 0:
            tokens.append(word.split('-')[0])
        else:
            tokens.append(word)
    print("token count: " + str(len(tokens)))

    leaves = re.findall(r'leaf \w (\d+\s\d+)', the_rest)
    leaves = list(map(lambda n: [int(n.split()[0]), int(n.split()[1])], leaves))
    leaves = list(map(lambda n: ' '.join(tokens[n[0]:n[1]+1]), leaves))

    return leaves

def load_predict(file):
    text = file.read()
    text = text.replace("'", '"')
    predict = json.loads(text)
    predict = list(map(lambda x: {
        "is_nucleus": True if x[0].find('NUC') >= 0 else False,
        "start": int(x[1]),
        "end": int(x[2]),
        "rel": x[3]
    }, predict))
    return predict

def create_tree(ranges):
    id = 1
    # add the tree node to the queue
    predict = ranges.pop(0)
    root = Node(id, predict["start"], predict["end"], rel=predict["rel"], type="span")
    id += 1

    nodes = [root]
    while len(nodes) != 0:
        current_node = nodes.pop(0)
        
        # leaf node
        if (current_node.is_leaf):
            continue
        
        predict = ranges.pop(0)
        child1 = Node(id, predict["start"], predict["end"], rel=predict["rel"], type="span", parent=current_node, is_nucleus=predict["is_nucleus"])
        id += 1
        nodes.append(child1)
        
        # we expect to find the right child at the top of stack
        predict = ranges.pop(0)
        child2 = Node(id, predict["start"], predict["end"], rel=predict["rel"], type="span", parent=current_node, is_nucleus=predict["is_nucleus"])
        id += 1
        nodes.append(child2)

        if child2.start != child1.end + 1: 
            raise Exception('Child 2 does not follow child 1')
        if child1.start != current_node.start: 
            raise Exception('Child 1 does not match parent')
        if child2.end != current_node.end: 
            raise Exception('Child 2 does not match parent')
        
        current_node.left = child1
        current_node.right = child2

    if len(ranges) > 0: raise Exception("Ranges are not empty")

    return root

def convert_to_rs3(tree):
    if tree is None or tree.is_leaf:
        return tree
    
    tree.left = convert_to_rs3(tree.left)
    tree.right = convert_to_rs3(tree.right)
    
    if tree.left.is_nucleus and tree.right.is_nucleus:
        tree.left.is_multinuc = True
        tree.right.is_multinuc = True
        tree.type = 'multinuc'
        return tree
    

    if tree.left.rel == 'span':
        tree.right.parent = tree.left
    elif tree.right.rel == 'span':
        tree.left.parent = tree.right
    else:
        raise Exception("Invalid node: no nucleus offsprings")
    
    return tree

def convert_to_rs3_v2(tree):
    if tree.is_leaf:
        return tree
    
    if tree.left.is_nucleus and tree.right.is_nucleus:
        tree.left.is_multinuc = True
        tree.right.is_multinuc = True
        tree.type = 'multinuc'
    
    tree.left = convert_to_rs3_v2(tree.left)
    tree.right = convert_to_rs3_v2(tree.right)
    
    return tree

def get_relations(tree, relations):
    if tree is None:
        return
    if tree.is_multinuc:
        relations[tree.rel] = 'multinuc'
    else:
        relations[tree.rel] = 'rst'

    get_relations(tree.left, relations)
    get_relations(tree.right, relations)

def write_relations(relations, fh):
    # write mono-nuc relations
    for key, value in relations.items():
        if value == 'rst':
            fh.write(f'      <rel name="{key}" type="rst" />\n')
    # write multi-nuc relations
    for key, value in relations.items():
        if value != 'rst':
            fh.write(f'      <rel name="{key}" type="multinuc" />\n')

def write_leaves(tree, segments, fh):
    if tree is None:
        return
    
    write_leaves(tree.left, segments, fh)
    
    if tree.is_leaf:
        id, parent = tree.id, tree.parent.id if tree.parent is not None else None
        rel = tree.rel
        text = html.escape(segments[tree.start])

        if parent is None:
            fh.write(f'    <segment id="{id}" relname="{rel}">{text}</segment>\n')
        else:
            fh.write(f'    <segment id="{id}" parent="{parent}" relname="{rel}">{text}</segment>\n')
    
        
    write_leaves(tree.right, segments, fh)

def write_groups(tree, fh):
    if tree is None:
        return
    
    if not tree.is_leaf:
        id, parent = tree.id, tree.parent.id if tree.parent is not None else None
        rel = tree.rel
        type = tree.type

        if parent is None:
            fh.write(f'    <group id="{id}" type="{type}" relname="{rel}"/>\n')
        else:
            fh.write(f'    <group id="{id}" parent="{parent}" type="{type}" relname="{rel}"/>\n')
        
    write_groups(tree.left, fh)
    write_groups(tree.right, fh)


def write_to_rs3_file(tree, segments, relations, file):
    f.write("<rst>\n")
    f.write("  <header>\n")
    f.write("    <relations>\n")
    write_relations(relations, file)
    f.write("    </relations>\n")
    f.write("  </header>\n")

    f.write("  <body>\n")
    write_leaves(tree, segments, file)
    write_groups(tree, file)
    f.write("  </body>\n")

    f.write("</rst>\n")
    
if __name__ == '__main__':
    # data_dir = './output_data/predict'
    data_dir='segs'
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    if not os.path.isdir(f'{data_dir}/output'):
        os.mkdir(f'{data_dir}/output')
    print(data_dir)
    
    txt_files = glob.glob(data_dir + "/*.segment")
    fns = [fn.split('/')[-1].split('.')[0] for fn in txt_files]

    for fn in fns:
        print(f'>>>>>>>>>>>>>>>>>>>>>>>>> {fn} ')
        with open(f'{data_dir}/{fn}.txt.prep') as f:
            segments = load_segments(f)
        with open(f'{data_dir}/{fn}.predict') as f:
            predict = load_predict(f)

        predict.insert(0, {"is_nuclear": False, "start": 0, "end": len(segments)-1, "rel": 'span'})
        tree = create_tree(predict)

        rs3_tree = convert_to_rs3(tree)
        #rs3_tree = convert_to_rs3_v2(tree)
        relations = {}
        get_relations(rs3_tree, relations)

        with open(f'{data_dir}/output/{fn}_merged_predicted.rs3', 'w') as f:
            write_to_rs3_file(rs3_tree, segments, relations, f)
            
