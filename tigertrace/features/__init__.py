from copy import deepcopy
from collections import defaultdict
from tigertrace.util.tree import BinaryTree

class Feature(object):
    
    def __init__(self):
        pass
    def __add__(self, other):
        pass

class SoftLabel(Feature):

    def __init__(self, labels_dict={}):
        self.labels = defaultdict(int, labels_dict)
    
    def __add__(self, other):
        for _id , count in other.labels.items():
            self.labels[_id] += count
        return self

    def __eq__(self, other):
        return self.labels == other.labels

    def __getitem__(self, key):
        return self.labels[key]

    def __setitem__(self, key, item):
        self.labels[key] = item

    @staticmethod
    def triplet_feature(one, other):
        voxel_sum = 0
        for label in one.labels:
            if label in other.labels:
                voxel_sum += one[label] * other[label] 
        return voxel_sum

class Neighbors(Feature):

    def __init__(self, neighbors_list=[]):
        self.s = set(neighbors_list)

    def __add__(self, other):
        s = deepcopy(self.s) 
        return Neighbors(s.union(other.s))

    def add(self, neighbor):
        self.s.add(neighbor)
        return self

    def remove(self, neighbor):
        self.s.remove(neighbor)
        return self

    def __contains__(self, neighbor):
        return neighbor in self.s

    def union(self, other):
        n = Neighbors()
        n.s = self.s.union(other.s)
        return n

    def difference(self, other):
        n = Neighbors()
        n.s = self.s.difference(other.s)
        return n

    def __iter__(self):
        return self.s.__iter__()

    def __eq__(self, other):
        return self.s == other.s

    def __str__(self):
        return self.s.__str__()

class Tree(Feature):

    def __init__(self, root_id=0, fromarray=None):
        self.t = BinaryTree(key=root_id,fromarray=fromarray)

    def insert_left_tree(self, other):
        self.t.insert_left_tree(other.t)

    def insert_right_tree(self, other):
        self.t.insert_right_tree(other.t)

    def get_leaf(self):
        return self.t.get_leaf_stack()

    def __add__(self, other):
        return self

    def __eq__(self, other):
        return self.t == other.t

    def __repr__(self):
        return self.t.__repr__()

class Position(Feature):

    def __init__(self):
        pass
        # self.pos = np.array([])

    def __add__(self, other):
        self.pos = np.concatenate([self.pos, 
                                   other.pos])
        return self

class Size(Feature):

    def __add__(self, other):
        self.size += other.size
        return self